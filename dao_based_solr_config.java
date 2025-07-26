// Enhanced Configuration Models for DAO-based data fetching

@Data
public class CollectionUpdateConfig {
    private String collectionName;
    private IdentifierConfig identifier;
    private List<FieldMapping> fieldMappings = new ArrayList<>();
    private List<DataSourceConfig> dataSources = new ArrayList<>();
    private Map<String, Object> defaultValues = new HashMap<>();
    private boolean validateBeforeUpdate = true;
    private int batchSize = 1000;
}

@Data
public class DataSourceConfig {
    private String name;                    // Unique name for this data source
    private String type;                    // "DAO", "SERVICE", "REPOSITORY"
    private String beanName;                // Spring bean name
    private String methodName;              // Method to call
    private List<String> inputFields;       // Fields from trigger data needed as input
    private String resultType;              // "SINGLE", "LIST", "MAP"
    private String resultPath;              // Path to extract data from result (e.g., "data.records")
    private Map<String, String> staticParams = new HashMap<>(); // Static parameters
    private boolean required = true;        // Fail if this data source fails
    private int retryCount = 0;            // Number of retries on failure
    private long cacheTimeoutMs = 0;       // Cache timeout (0 = no cache)
}

@Data
public class FieldMapping {
    private String solrField;              // Target Solr field
    private String dataSource;             // Which data source to use
    private String sourcePath;             // Path in the data source result (e.g., "user.email")
    private String dataType = "STRING";    // Data type conversion
    private boolean required = false;
    private String defaultValue;
    private List<String> allowedValues;
    private String transformFunction;
    
    // For composite fields
    private List<String> sourcePaths;      // Multiple paths for composite fields
    private String separator = "_";
    private String combineFunction;
    
    // For direct value mapping (not from data source)
    private String staticValue;            // Static value assignment
    private String triggerField;           // Field from trigger data (CSV/JSON input)
}

@Data
public class IdentifierConfig {
    private List<FieldMapping> identifierFields = new ArrayList<>();
    private String compositeStrategy = "COMBINE"; // "COMBINE", "HASH", "CUSTOM"
    private String compositeFunction;      // Custom function for combining identifiers
}

// Updated Service for DAO-based processing

@Service
@Slf4j
public class DaoBasedPartialUpdateService {
    
    private final SolrUpdateConfiguration config;
    private final SolrClient solrClient;
    private final ApplicationContext applicationContext;
    private final DataSourceExecutor dataSourceExecutor;
    private final FieldTransformationService transformationService;
    private final ResultCacheService cacheService;
    
    public DaoBasedPartialUpdateService(
            SolrUpdateConfiguration config,
            SolrClient solrClient,
            ApplicationContext applicationContext,
            DataSourceExecutor dataSourceExecutor,
            FieldTransformationService transformationService,
            ResultCacheService cacheService) {
        this.config = config;
        this.solrClient = solrClient;
        this.applicationContext = applicationContext;
        this.dataSourceExecutor = dataSourceExecutor;
        this.transformationService = transformationService;
        this.cacheService = cacheService;
    }
    
    public void processPartialUpdate(String collectionName, List<Map<String, Object>> triggerData) {
        try {
            CollectionUpdateConfig collectionConfig = getCollectionConfig(collectionName);
            
            // Process in batches
            for (int i = 0; i < triggerData.size(); i += collectionConfig.getBatchSize()) {
                int endIndex = Math.min(i + collectionConfig.getBatchSize(), triggerData.size());
                List<Map<String, Object>> batch = triggerData.subList(i, endIndex);
                processBatch(collectionConfig, batch);
            }
            
            solrClient.commit(collectionConfig.getCollectionName());
            log.info("Successfully processed {} records for collection {}", 
                    triggerData.size(), collectionName);
            
        } catch (Exception e) {
            log.error("Error processing DAO-based update for collection: {}", collectionName, e);
            throw new RuntimeException("DAO-based update failed", e);
        }
    }
    
    private void processBatch(CollectionUpdateConfig config, List<Map<String, Object>> batch) 
            throws Exception {
        
        Collection<SolrInputDocument> documents = new ArrayList<>();
        
        for (Map<String, Object> triggerRecord : batch) {
            try {
                // Fetch all required data from configured data sources
                Map<String, Object> aggregatedData = fetchDataFromSources(config, triggerRecord);
                
                // Create Solr update document
                SolrInputDocument updateDoc = createUpdateDocument(config, triggerRecord, aggregatedData);
                if (updateDoc != null) {
                    documents.add(updateDoc);
                }
            } catch (Exception e) {
                log.warn("Failed to process record: {}, Error: {}", triggerRecord, e.getMessage());
                if (config.isValidateBeforeUpdate()) {
                    throw e; // Fail fast if validation is enabled
                }
            }
        }
        
        if (!documents.isEmpty()) {
            solrClient.add(config.getCollectionName(), documents);
        }
    }
    
    private Map<String, Object> fetchDataFromSources(CollectionUpdateConfig config, 
            Map<String, Object> triggerRecord) throws Exception {
        
        Map<String, Object> aggregatedData = new HashMap<>();
        aggregatedData.put("trigger", triggerRecord); // Include original trigger data
        
        for (DataSourceConfig dataSource : config.getDataSources()) {
            try {
                Object result = dataSourceExecutor.executeDataSource(dataSource, triggerRecord);
                aggregatedData.put(dataSource.getName(), result);
                
                log.debug("Data source '{}' returned: {}", dataSource.getName(), 
                         result != null ? result.getClass().getSimpleName() : "null");
                
            } catch (Exception e) {
                log.error("Failed to fetch data from source: {}", dataSource.getName(), e);
                if (dataSource.isRequired()) {
                    throw new RuntimeException("Required data source failed: " + dataSource.getName(), e);
                }
                // Add null for optional data sources
                aggregatedData.put(dataSource.getName(), null);
            }
        }
        
        return aggregatedData;
    }
    
    private SolrInputDocument createUpdateDocument(CollectionUpdateConfig config, 
            Map<String, Object> triggerRecord, Map<String, Object> aggregatedData) throws Exception {
        
        SolrInputDocument updateDoc = new SolrInputDocument();
        
        // Add identifier fields
        addIdentifierFields(updateDoc, config.getIdentifier(), aggregatedData);
        
        // Process field mappings
        for (FieldMapping mapping : config.getFieldMappings()) {
            processFieldMapping(updateDoc, mapping, aggregatedData);
        }
        
        // Add default values
        addDefaultValues(updateDoc, config.getDefaultValues());
        
        return updateDoc;
    }
    
    private void addIdentifierFields(SolrInputDocument doc, IdentifierConfig identifier, 
            Map<String, Object> aggregatedData) throws Exception {
        
        List<String> identifierParts = new ArrayList<>();
        
        for (FieldMapping idField : identifier.getIdentifierFields()) {
            Object value = extractValue(idField, aggregatedData);
            if (value == null) {
                throw new IllegalArgumentException("Required identifier field missing: " + idField.getSolrField());
            }
            identifierParts.add(value.toString());
        }
        
        // Combine identifier parts
        String compositeId;
        if (identifier.getCompositeFunction() != null) {
            compositeId = transformationService.combineIdentifierParts(
                identifier.getCompositeFunction(), identifierParts);
        } else {
            compositeId = String.join("_", identifierParts);
        }
        
        doc.addField("id", compositeId);
    }
    
    private void processFieldMapping(SolrInputDocument doc, FieldMapping mapping, 
            Map<String, Object> aggregatedData) throws Exception {
        
        Object value = extractValue(mapping, aggregatedData);
        
        if (value == null) {
            if (mapping.isRequired()) {
                throw new IllegalArgumentException("Required field missing: " + mapping.getSolrField());
            }
            value = mapping.getDefaultValue();
            if (value == null) {
                return; // Skip this field
            }
        }
        
        // Transform value if needed
        if (mapping.getTransformFunction() != null) {
            value = transformationService.transform(mapping.getTransformFunction(), value.toString());
        }
        
        // Convert data type
        Object convertedValue = convertDataType(value.toString(), mapping.getDataType());
        
        // Create atomic update operation
        Map<String, Object> atomicUpdate = new HashMap<>();
        atomicUpdate.put("set", convertedValue);
        doc.addField(mapping.getSolrField(), atomicUpdate);
    }
    
    private Object extractValue(FieldMapping mapping, Map<String, Object> aggregatedData) {
        // Handle static values
        if (mapping.getStaticValue() != null) {
            return mapping.getStaticValue();
        }
        
        // Handle trigger field direct mapping
        if (mapping.getTriggerField() != null) {
            Map<String, Object> triggerData = (Map<String, Object>) aggregatedData.get("trigger");
            return getNestedValue(triggerData, mapping.getTriggerField());
        }
        
        // Handle composite fields
        if (mapping.getSourcePaths() != null && !mapping.getSourcePaths().isEmpty()) {
            List<String> values = new ArrayList<>();
            for (String sourcePath : mapping.getSourcePaths()) {
                Object value = getValueFromPath(aggregatedData, sourcePath);
                values.add(value != null ? value.toString() : "");
            }
            
            if (mapping.getCombineFunction() != null) {
                return transformationService.combineFields(mapping.getCombineFunction(), values);
            } else {
                return String.join(mapping.getSeparator(), values);
            }
        }
        
        // Handle single source path
        if (mapping.getSourcePath() != null) {
            return getValueFromPath(aggregatedData, mapping.getSourcePath());
        }
        
        return null;
    }
    
    private Object getValueFromPath(Map<String, Object> data, String path) {
        String[] parts = path.split("\\.");
        Object current = data;
        
        for (String part : parts) {
            if (current == null) return null;
            
            if (current instanceof Map) {
                current = ((Map<String, Object>) current).get(part);
            } else if (current instanceof List) {
                try {
                    int index = Integer.parseInt(part);
                    current = ((List<?>) current).get(index);
                } catch (NumberFormatException | IndexOutOfBoundsException e) {
                    return null;
                }
            } else {
                // Use reflection for object properties
                current = getObjectProperty(current, part);
            }
        }
        
        return current;
    }
    
    private Object getNestedValue(Map<String, Object> data, String path) {
        return getValueFromPath(data, path);
    }
    
    private Object getObjectProperty(Object obj, String property) {
        try {
            Field field = obj.getClass().getDeclaredField(property);
            field.setAccessible(true);
            return field.get(obj);
        } catch (Exception e) {
            try {
                Method getter = obj.getClass().getMethod("get" + 
                    property.substring(0, 1).toUpperCase() + property.substring(1));
                return getter.invoke(obj);
            } catch (Exception ex) {
                log.warn("Could not access property '{}' on object of type {}", 
                        property, obj.getClass().getSimpleName());
                return null;
            }
        }
    }
    
    // ... other helper methods remain similar ...
}

// Data Source Executor Service

@Service
@Slf4j
public class DataSourceExecutor {
    
    private final ApplicationContext applicationContext;
    private final ResultCacheService cacheService;
    
    public DataSourceExecutor(ApplicationContext applicationContext, ResultCacheService cacheService) {
        this.applicationContext = applicationContext;
        this.cacheService = cacheService;
    }
    
    public Object executeDataSource(DataSourceConfig dataSource, Map<String, Object> triggerData) 
            throws Exception {
        
        // Check cache first
        if (dataSource.getCacheTimeoutMs() > 0) {
            String cacheKey = buildCacheKey(dataSource, triggerData);
            Object cachedResult = cacheService.get(cacheKey);
            if (cachedResult != null) {
                log.debug("Returning cached result for data source: {}", dataSource.getName());
                return cachedResult;
            }
        }
        
        // Execute with retry logic
        Exception lastException = null;
        for (int attempt = 0; attempt <= dataSource.getRetryCount(); attempt++) {
            try {
                Object result = executeDataSourceInternal(dataSource, triggerData);
                
                // Cache result if configured
                if (dataSource.getCacheTimeoutMs() > 0 && result != null) {
                    String cacheKey = buildCacheKey(dataSource, triggerData);
                    cacheService.put(cacheKey, result, dataSource.getCacheTimeoutMs());
                }
                
                return processResult(result, dataSource);
                
            } catch (Exception e) {
                lastException = e;
                if (attempt < dataSource.getRetryCount()) {
                    log.warn("Attempt {} failed for data source {}, retrying...", 
                            attempt + 1, dataSource.getName());
                    Thread.sleep(1000 * (attempt + 1)); // Exponential backoff
                }
            }
        }
        
        throw new RuntimeException("Data source execution failed after " + 
                (dataSource.getRetryCount() + 1) + " attempts", lastException);
    }
    
    private Object executeDataSourceInternal(DataSourceConfig dataSource, Map<String, Object> triggerData) 
            throws Exception {
        
        // Get the bean
        Object bean = applicationContext.getBean(dataSource.getBeanName());
        
        // Prepare method parameters
        Object[] params = prepareMethodParameters(dataSource, triggerData);
        
        // Find and invoke the method
        Method method = findMethod(bean.getClass(), dataSource.getMethodName(), params);
        
        log.debug("Executing {}.{}() with {} parameters", 
                bean.getClass().getSimpleName(), dataSource.getMethodName(), params.length);
        
        return method.invoke(bean, params);
    }
    
    private Object[] prepareMethodParameters(DataSourceConfig dataSource, Map<String, Object> triggerData) {
        List<Object> params = new ArrayList<>();
        
        // Add input fields from trigger data
        for (String inputField : dataSource.getInputFields()) {
            Object value = getNestedValue(triggerData, inputField);
            params.add(value);
        }
        
        // Add static parameters
        for (Map.Entry<String, String> staticParam : dataSource.getStaticParams().entrySet()) {
            params.add(staticParam.getValue());
        }
        
        return params.toArray();
    }
    
    private Method findMethod(Class<?> clazz, String methodName, Object[] params) 
            throws NoSuchMethodException {
        
        Method[] methods = clazz.getMethods();
        for (Method method : methods) {
            if (method.getName().equals(methodName) && 
                method.getParameterCount() == params.length) {
                return method;
            }
        }
        
        throw new NoSuchMethodException("Method " + methodName + " with " + 
                params.length + " parameters not found in " + clazz.getSimpleName());
    }
    
    private Object processResult(Object result, DataSourceConfig dataSource) {
        if (result == null) return null;
        
        // Extract data based on result path
        if (dataSource.getResultPath() != null && !dataSource.getResultPath().isEmpty()) {
            return extractFromResult(result, dataSource.getResultPath());
        }
        
        return result;
    }
    
    private Object extractFromResult(Object result, String path) {
        // Similar to getValueFromPath but for method results
        String[] parts = path.split("\\.");
        Object current = result;
        
        for (String part : parts) {
            if (current == null) return null;
            
            if (current instanceof Map) {
                current = ((Map<String, Object>) current).get(part);
            } else if (current instanceof List) {
                try {
                    int index = Integer.parseInt(part);
                    current = ((List<?>) current).get(index);
                } catch (NumberFormatException | IndexOutOfBoundsException e) {
                    return null;
                }
            } else {
                current = getObjectProperty(current, part);
            }
        }
        
        return current;
    }
    
    private Object getNestedValue(Map<String, Object> data, String path) {
        String[] parts = path.split("\\.");
        Object current = data;
        
        for (String part : parts) {
            if (current instanceof Map) {
                current = ((Map<String, Object>) current).get(part);
            } else {
                return null;
            }
        }
        
        return current;
    }
    
    private Object getObjectProperty(Object obj, String property) {
        try {
            Field field = obj.getClass().getDeclaredField(property);
            field.setAccessible(true);
            return field.get(obj);
        } catch (Exception e) {
            try {
                Method getter = obj.getClass().getMethod("get" + 
                    property.substring(0, 1).toUpperCase() + property.substring(1));
                return getter.invoke(obj);
            } catch (Exception ex) {
                return null;
            }
        }
    }
    
    private String buildCacheKey(DataSourceConfig dataSource, Map<String, Object> triggerData) {
        StringBuilder keyBuilder = new StringBuilder();
        keyBuilder.append(dataSource.getName()).append(":");
        
        for (String inputField : dataSource.getInputFields()) {
            Object value = getNestedValue(triggerData, inputField);
            keyBuilder.append(inputField).append("=").append(value).append(";");
        }
        
        return keyBuilder.toString();
    }
}

// Simple cache service for DAO results
@Service
public class ResultCacheService {
    
    private final Map<String, CacheEntry> cache = new ConcurrentHashMap<>();
    
    public void put(String key, Object value, long timeoutMs) {
        long expiryTime = System.currentTimeMillis() + timeoutMs;
        cache.put(key, new CacheEntry(value, expiryTime));
    }
    
    public Object get(String key) {
        CacheEntry entry = cache.get(key);
        if (entry == null) return null;
        
        if (System.currentTimeMillis() > entry.expiryTime) {
            cache.remove(key);
            return null;
        }
        
        return entry.value;
    }
    
    @Scheduled(fixedRate = 60000) // Clean expired entries every minute
    public void cleanExpiredEntries() {
        long now = System.currentTimeMillis();
        cache.entrySet().removeIf(entry -> now > entry.getValue().expiryTime);
    }
    
    private static class CacheEntry {
        final Object value;
        final long expiryTime;
        
        CacheEntry(Object value, long expiryTime) {
            this.value = value;
            this.expiryTime = expiryTime;
        }
    }
}
// Updated Configuration Models to handle comma-separated values

@Data
@ConfigurationProperties(prefix = "solr.update")
public class SolrUpdateConfiguration {
    private Map<String, CollectionConfig> collections = new HashMap<>();
}

@Data
public class CollectionConfig {
    private String collectionName;
    private String entityClass;
    private IdentifierConfig identifier;
    private String partialUpdateFields;  // Changed to String for comma-separated
    private Map<String, SolrFieldMapping> solrFieldMappings = new HashMap<>();
    private Map<String, Object> defaultValues = new HashMap<>();
    private int batchSize = 1000;
    
    // Helper method to get partial update fields as list
    public List<String> getPartialUpdateFieldsList() {
        if (partialUpdateFields == null || partialUpdateFields.trim().isEmpty()) {
            return new ArrayList<>();
        }
        return Arrays.stream(partialUpdateFields.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .collect(Collectors.toList());
    }
}

@Data
public class IdentifierConfig {
    private String sourceFields;        // Changed to String for comma-separated
    private String separator = "_";
    private String solrField = "id";
    
    // Helper method to get source fields as list
    public List<String> getSourceFieldsList() {
        if (sourceFields == null || sourceFields.trim().isEmpty()) {
            return new ArrayList<>();
        }
        return Arrays.stream(sourceFields.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .collect(Collectors.toList());
    }
}

@Data
public class SolrFieldMapping {
    private String sourceField;
    private String solrField;
    private String tableName;
}

// Updated Service to use the new helper methods

@Service
@Slf4j
public class UpdatedTableBasedPartialUpdateService {
    
    private final SolrUpdateConfiguration config;
    private final SolrClient solrClient;
    private final CsvProcessingService csvService;
    private final BusinessDataPopulationService businessService;
    
    public UpdatedTableBasedPartialUpdateService(
            SolrUpdateConfiguration config,
            SolrClient solrClient,
            CsvProcessingService csvService,
            BusinessDataPopulationService businessService) {
        this.config = config;
        this.solrClient = solrClient;
        this.csvService = csvService;
        this.businessService = businessService;
    }
    
    public void processPartialUpdate(String fileName, String csvFilePath) {
        try {
            String collectionName = extractCollectionName(fileName);
            log.info("Processing partial update for collection: {}", collectionName);
            
            CollectionConfig collectionConfig = getCollectionConfig(collectionName);
            
            // Log configuration for debugging
            logConfigurationDetails(collectionConfig);
            
            List<Map<String, String>> csvRecords = csvService.readCsv(csvFilePath);
            log.info("Read {} records from CSV", csvRecords.size());
            
            processBatches(collectionConfig, csvRecords);
            
            solrClient.commit(collectionConfig.getCollectionName());
            log.info("Successfully processed {} records for collection {}", 
                    csvRecords.size(), collectionName);
            
        } catch (Exception e) {
            log.error("Error processing partial update for file: {}", fileName, e);
            throw new RuntimeException("Partial update failed for file: " + fileName, e);
        }
    }
    
    private void logConfigurationDetails(CollectionConfig config) {
        log.debug("Collection Configuration:");
        log.debug("  Collection Name: {}", config.getCollectionName());
        log.debug("  Entity Class: {}", config.getEntityClass());
        log.debug("  Identifier Fields: {}", config.getIdentifier().getSourceFieldsList());
        log.debug("  Identifier Separator: '{}'", config.getIdentifier().getSeparator());
        log.debug("  Partial Update Fields: {}", config.getPartialUpdateFieldsList());
        
        for (String field : config.getPartialUpdateFieldsList()) {
            SolrFieldMapping mapping = config.getSolrFieldMappings().get(field);
            if (mapping != null) {
                log.debug("  Field Mapping - {}: {} → {} (Table: {})", 
                        field, mapping.getSourceField(), mapping.getSolrField(), mapping.getTableName());
            }
        }
    }
    
    private void executeBusinessMethods(CollectionConfig config, Map<String, String> csvRecord, Object entity) 
            throws Exception {
        
        // Get unique tables for the partial update fields
        List<String> partialUpdateFields = config.getPartialUpdateFieldsList();
        Set<String> uniqueTables = getUniqueTablesForFields(partialUpdateFields, config.getSolrFieldMappings());
        
        log.debug("Unique tables to execute: {} for fields: {}", uniqueTables, partialUpdateFields);
        
        Set<String> executedTables = new HashSet<>();
        
        for (String field : partialUpdateFields) {
            SolrFieldMapping mapping = config.getSolrFieldMappings().get(field);
            if (mapping == null) {
                log.warn("No mapping found for field: {}", field);
                continue;
            }
            
            String tableName = mapping.getTableName();
            
            if (!executedTables.contains(tableName)) {
                log.debug("Executing business method for table: {} (needed by field: {})", tableName, field);
                
                businessService.populateFromTable(tableName, csvRecord, entity);
                executedTables.add(tableName);
                
                log.debug("Successfully executed table: {}", tableName);
            } else {
                log.debug("Skipping table: {} for field: {} (already executed)", tableName, field);
            }
        }
        
        log.info("Executed {} unique tables out of {} fields for collection: {}", 
                executedTables.size(), partialUpdateFields.size(), config.getCollectionName());
    }
    
    private Set<String> getUniqueTablesForFields(List<String> partialUpdateFields, 
            Map<String, SolrFieldMapping> solrFieldMappings) {
        
        return partialUpdateFields.stream()
                .map(field -> solrFieldMappings.get(field))
                .filter(Objects::nonNull)
                .map(SolrFieldMapping::getTableName)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());
    }
    
    private String createCompositeIdentifier(Object entity, IdentifierConfig identifier) throws Exception {
        List<String> sourceFields = identifier.getSourceFieldsList();
        List<String> idParts = new ArrayList<>();
        
        for (String sourceField : sourceFields) {
            Object value = getEntityFieldValue(entity, sourceField);
            if (value == null) {
                throw new IllegalArgumentException("Required identifier field is null: " + sourceField);
            }
            idParts.add(value.toString());
        }
        
        String compositeId = String.join(identifier.getSeparator(), idParts);
        log.debug("Created composite ID: {} from fields: {}", compositeId, sourceFields);
        
        return compositeId;
    }
    
    private SolrInputDocument createSolrDocument(CollectionConfig config, Object entity) throws Exception {
        SolrInputDocument doc = new SolrInputDocument();
        
        // Create composite identifier
        String compositeId = createCompositeIdentifier(entity, config.getIdentifier());
        doc.addField(config.getIdentifier().getSolrField(), compositeId);
        
        // Create atomic updates for partial update fields only
        List<String> partialUpdateFields = config.getPartialUpdateFieldsList();
        
        for (String field : partialUpdateFields) {
            SolrFieldMapping mapping = config.getSolrFieldMappings().get(field);
            if (mapping == null) {
                log.warn("No Solr field mapping found for field: {}", field);
                continue;
            }
            
            Object value = getEntityFieldValue(entity, mapping.getSourceField());
            
            if (value != null) {
                Map<String, Object> atomicUpdate = new HashMap<>();
                atomicUpdate.put("set", value);
                doc.addField(mapping.getSolrField(), atomicUpdate);
                
                log.debug("Added field to Solr update: {} = {}", mapping.getSolrField(), value);
            }
        }
        
        addDefaultValues(doc, config.getDefaultValues());
        
        return doc;
    }
    
    // ... rest of the methods remain the same ...
}

// Configuration Examples with comma-separated values

/*
Example Configuration:

# Simple single field identifier
solr.update.collections.product.identifier.source-fields=productId

# Two field composite identifier  
solr.update.collections.subscriber.identifier.source-fields=customerId,subscriberId
solr.update.collections.subscriber.identifier.separator=_

# Three field composite identifier
solr.update.collections.order.identifier.source-fields=customerId,orderId,regionCode
solr.update.collections.order.identifier.separator=_

# Multiple partial update fields
solr.update.collections.subscriber.partial-update-fields=fieldA,fieldB,fieldC,fieldD
solr.update.collections.customer.partial-update-fields=name,email,phone,address,subscription
solr.update.collections.product.partial-update-fields=name,price,category,inventory,description

Examples:
- productId → "P001"
- customerId,subscriberId with separator "_" → "CUST001_SUB123"  
- customerId,orderId,regionCode with separator "_" → "CUST001_ORD456_US"
- customerId,regionCode with separator "-" → "CUST001-US"

Partial update fields:
- fieldA,fieldB,fieldC,fieldD → ["fieldA", "fieldB", "fieldC", "fieldD"]
- name,email,phone → ["name", "email", "phone"]
*/
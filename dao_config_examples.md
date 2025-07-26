# DAO-Based Solr Update Configuration Examples

## Overview

Instead of reading from CSV files, this system calls DAO methods to fetch data and updates Solr documents. The system is fully configurable through YAML.

## Configuration Structure

```yaml
solr:
  update:
    collections:
      {collection_name}:
        collection-name: "actual_solr_collection"
        data-sources:          # Define which DAOs/services to call
          - name: "user_data"
            bean-name: "userDao"
            method-name: "getUserById"
            # ... more config
        identifier:            # How to build document ID
          identifier-fields:
            - solr-field: "id"
              data-source: "user_data"
              source-path: "userId"
        field-mappings:        # Map DAO results to Solr fields
          - solr-field: "user_name"
            data-source: "user_data"
            source-path: "fullName"
```

## Example 1: Simple DAO Call Configuration

### Scenario
- Trigger data contains: `{userId: "12345", action: "update"}`
- Need to call `userDao.getUserById(userId)` to get user details
- Update Solr with the fetched user information

### Configuration:
```yaml
solr:
  update:
    collections:
      user_profile:
        collection-name: "user_profile"
        batch-size: 1000
        
        # Define data sources (DAO calls)
        data-sources:
          - name: "user_data"
            type: "DAO"
            bean-name: "userDao"
            method-name: "getUserById"
            input-fields: ["userId"]           # Fields from trigger data
            result-type: "SINGLE"              # Returns single object
            required: true
            retry-count: 2
            cache-timeout-ms: 300000           # Cache for 5 minutes
        
        # Define document identifier
        identifier:
          identifier-fields:
            - solr-field: "id"
              data-source: "user_data"
              source-path: "id"                # user.getId()
        
        # Map DAO results to Solr fields
        field-mappings:
          - solr-field: "user_name"
            data-source: "user_data"
            source-path: "fullName"            # user.getFullName()
            data-type: "STRING"
            required: true
          
          - solr-field: "email"
            data-source: "user_data"
            source-path: "email"
            data-type: "STRING"
          
          - solr-field: "status"
            data-source: "user_data"
            source-path: "status"
            data-type: "STRING"
            allowed-values: ["ACTIVE", "INACTIVE", "SUSPENDED"]
          
          - solr-field: "last_login"
            data-source: "user_data"
            source-path: "lastLoginDate"
            data-type: "DATE"
            transform-function: "formatDate"
        
        default-values:
          updated_timestamp: "NOW"
          updated_by: "BATCH_PROCESS"
```

### Java DAO Interface:
```java
@Component("userDao")
public class UserDao {
    
    public User getUserById(String userId) {
        // Your existing DAO logic
        return userRepository.findById(userId);
    }
}

public class User {
    private String id;
    private String fullName;
    private String email;
    private String status;
    private Date lastLoginDate;
    // getters/setters
}
```

### Trigger Data:
```java
List<Map<String, Object>> triggerData = Arrays.asList(
    Map.of("userId", "12345", "action", "update"),
    Map.of("userId", "67890", "action", "update")
);

daoBasedService.processPartialUpdate("user_profile", triggerData);
```

## Example 2: Multiple DAO Calls Configuration

### Scenario
- Trigger: `{customerId: "C123", subscriptionId: "S456"}`
- Call `customerDao.getCustomerById(customerId)`
- Call `subscriptionDao.getSubscriptionById(subscriptionId)`
- Combine data from both calls into Solr document

### Configuration:
```yaml
solr:
  update:
    collections:
      customer_subscription:
        collection-name: "customer_subscription"
        
        # Multiple data sources
        data-sources:
          - name: "customer_data"
            bean-name: "customerDao"
            method-name: "getCustomerById"
            input-fields: ["customerId"]
            result-type: "SINGLE"
            required: true
            cache-timeout-ms: 600000           # 10 minutes
          
          - name: "subscription_data"
            bean-name: "subscriptionDao"
            method-name: "getSubscriptionById"
            input-fields: ["subscriptionId"]
            result-type: "SINGLE"
            required: true
            cache-timeout-ms: 300000           # 5 minutes
          
          - name: "billing_data"
            bean-name: "billingService"
            method-name: "getBillingInfo"
            input-fields: ["customerId", "subscriptionId"]
            result-type: "SINGLE"
            required: false                    # Optional data
        
        # Composite identifier from multiple sources
        identifier:
          identifier-fields:
            - data-source: "customer_data"
              source-path: "id"
            - data-source: "subscription_data"
              source-path: "id"
          composite-strategy: "COMBINE"        # Combine with underscore
        
        field-mappings:
          # Customer data
          - solr-field: "customer_name"
            data-source: "customer_data"
            source-path: "fullName"
            data-type: "STRING"
          
          - solr-field: "customer_email"
            data-source: "customer_data"
            source-path: "email"
            data-type: "STRING"
          
          # Subscription data
          - solr-field: "subscription_plan"
            data-source: "subscription_data"
            source-path: "planType"
            data-type: "STRING"
          
          - solr-field: "subscription_status"
            data-source: "subscription_data"
            source-path: "status"
            data-type: "STRING"
          
          # Billing data (optional)
          - solr-field: "monthly_cost"
            data-source: "billing_data"
            source-path: "monthlyAmount"
            data-type: "DOUBLE"
            default-value: "0.0"
          
          # Composite field from multiple sources
          - solr-field: "customer_subscription_key"
            source-paths: 
              - "customer_data.customerType"
              - "subscription_data.planType"
            separator: "-"
            data-type: "STRING"
          
          # Static field
          - solr-field: "record_type"
            static-value: "CUSTOMER_SUBSCRIPTION"
          
          # Field from trigger data
          - solr-field: "trigger_source"
            trigger-field: "action"
```

## Example 3: Complex Nested Data Extraction

### Scenario
- DAO returns complex nested objects
- Need to extract data from deep object hierarchies

### Configuration:
```yaml
solr:
  update:
    collections:
      order_details:
        collection-name: "order_details"
        
        data-sources:
          - name: "order_data"
            bean-name: "orderService"
            method-name: "getOrderWithDetails"
            input-fields: ["orderId"]
            result-type: "SINGLE"
            result-path: "data.orderInfo"      # Extract from response wrapper
        
        identifier:
          identifier-fields:
            - data-source: "order_data"
              source-path: "orderId"
        
        field-mappings:
          # Simple nested extraction
          - solr-field: "customer_name"
            data-source: "order_data"
            source-path: "customer.fullName"   # order.getCustomer().getFullName()
          
          # Deep nested extraction
          - solr-field: "shipping_address"
            data-source: "order_data"
            source-path: "shipping.address.fullAddress"
          
          # Array access
          - solr-field: "first_item_name"
            data-source: "order_data"
            source-path: "items.0.productName" # order.getItems().get(0).getProductName()
          
          # Multiple nested paths for composite field
          - solr-field: "order_summary"
            source-paths:
              - "order_data.orderNumber"
              - "order_data.customer.lastName"
              - "order_data.totalAmount"
            separator: "|"
```

## Example 4: DAO with Static Parameters

### Scenario
- DAO method needs both dynamic and static parameters
- Example: `getUserData(userId, includeHistory=true, maxRecords=100)`

### Configuration:
```yaml
solr:
  update:
    collections:
      user_history:
        collection-name: "user_history"
        
        data-sources:
          - name: "user_with_history"
            bean-name: "userService"
            method-name: "getUserData"
            input-fields: ["userId"]          # Dynamic parameter from trigger
            static-params:                    # Static parameters
              includeHistory: "true"
              maxRecords: "100"
              dataFormat: "FULL"
            result-type: "SINGLE"
        
        identifier:
          identifier-fields:
            - data-source: "user_with_history"
              source-path: "userId"
        
        field-mappings:
          - solr-field: "user_name"
            data-source: "user_with_history"
            source-path: "userName"
          
          - solr-field: "history_count"
            data-source: "user_with_history"
            source-path: "historyRecords.size"  # Call .size() method
            data-type: "INTEGER"
```

## Example 5: Error Handling and Fallbacks

### Configuration:
```yaml
solr:
  update:
    collections:
      robust_updates:
        collection-name: "robust_updates"
        
        data-sources:
          # Primary data source
          - name: "primary_data"
            bean-name: "primaryService"
            method-name: "getPrimaryData"
            input-fields: ["entityId"]
            required: true
            retry-count: 3
          
          # Fallback data source
          - name: "fallback_data"
            bean-name: "fallbackService"
            method-name: "getFallbackData"
            input-fields: ["entityId"]
            required: false                   # Optional fallback
            retry-count: 1
          
          # Cache-heavy data source
          - name: "reference_data"
            bean-name: "referenceService"
            method-name: "getReferenceData"
            input-fields: ["type"]
            cache-timeout-ms: 3600000         # Cache for 1 hour
            required: false
        
        identifier:
          identifier-fields:
            - data-source: "primary_data"
              source-path: "id"
        
        field-mappings:
          # Primary field with fallback
          - solr-field: "entity_name"
            data-source: "primary_data"
            source-path: "name"
            default-value: "UNKNOWN"
          
          # Use fallback if primary fails
          - solr-field: "description"
            data-source: "fallback_data"
            source-path: "description"
            default-value: "No description available"
          
          # Reference data lookup
          - solr-field: "category_name"
            data-source: "reference_data"
            source-path: "categoryName"
            default-value: "UNCATEGORIZED"
```

## Example 6: Real-World Complex Configuration

### Scenario: E-commerce Order Processing
- Trigger: Order update events
- Need data from: Customer, Product, Inventory, Pricing services
- Complex business logic for field combinations

### Configuration:
```yaml
solr:
  update:
    collections:
      order_search:
        collection-name: "order_search_index"
        batch-size: 500
        validate-before-update: true
        
        # Multiple data sources for comprehensive order data
        data-sources:
          # Customer information
          - name: "customer"
            bean-name: "customerService"
            method-name: "getCustomerProfile"
            input-fields: ["customerId"]
            result-type: "SINGLE"
            required: true
            retry-count: 2
            cache-timeout-ms: 1800000         # 30 minutes
          
          # Order details
          - name: "order"
            bean-name: "orderService"
            method-name: "getOrderDetails"
            input-fields: ["orderId"]
            result-type: "SINGLE"
            required: true
            retry-count: 3
          
          # Product information for all items in order
          - name: "products"
            bean-name: "productService"
            method-name: "getProductsByOrderId"
            input-fields: ["orderId"]
            result-type: "LIST"
            required: true
            cache-timeout-ms: 600000          # 10 minutes
          
          # Inventory status
          - name: "inventory"
            bean-name: "inventoryService"
            method-name: "getInventoryStatus"
            input-fields: ["orderId"]
            static-params:
              includeReservations: "true"
              warehouseScope: "ALL"
            result-type: "MAP"
            required: false
          
          # Pricing calculations
          - name: "pricing"
            bean-name: "pricingEngine"
            method-name: "calculateOrderPricing"
            input-fields: ["orderId", "customerId"]
            static-params:
              includeTax: "true"
              includeDiscounts: "true"
            result-type: "SINGLE"
            required: false
            retry-count: 1
        
        # Composite identifier: orderId_customerId
        identifier:
          identifier-fields:
            - data-source: "order"
              source-path: "orderId"
            - data-source: "customer"
              source-path: "customerId"
          composite-strategy: "COMBINE"
        
        # Comprehensive field mappings
        field-mappings:
          # Customer fields
          - solr-field: "customer_name"
            data-source: "customer"
            source-path: "profile.fullName"
            data-type: "STRING"
            required: true
          
          - solr-field: "customer_tier"
            data-source: "customer"
            source-path: "tier.level"
            data-type: "STRING"
            allowed-values: ["BRONZE", "SILVER", "GOLD", "PLATINUM"]
            default-value: "BRONZE"
          
          - solr-field: "customer_region"
            data-source: "customer"
            source-path: "address.region"
            data-type: "STRING"
            transform-function: "toUpperCase"
          
          # Order fields
          - solr-field: "order_date"
            data-source: "order"
            source-path: "orderDate"
            data-type: "DATE"
            required: true
          
          - solr-field: "order_status"
            data-source: "order"
            source-path: "status"
            data-type: "STRING"
            allowed-values: ["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"]
          
          - solr-field: "shipping_method"
            data-source: "order"
            source-path: "shipping.method"
            data-type: "STRING"
          
          # Product aggregations
          - solr-field: "product_count"
            data-source: "products"
            source-path: "size"               # products.size()
            data-type: "INTEGER"
          
          - solr-field: "product_categories"
            data-source: "products"
            source-path: "*.category"         # Extract all categories
            data-type: "STRING"
            transform-function: "uniqueList"   # Remove duplicates
          
          # Inventory fields
          - solr-field: "all_items_available"
            data-source: "inventory"
            source-path: "allAvailable"
            data-type: "BOOLEAN"
            default-value: "false"
          
          - solr-field: "backorder_count"
            data-source: "inventory"
            source-path: "backorderItems.count"
            data-type: "INTEGER"
            default-value: "0"
          
          # Pricing fields
          - solr-field: "total_amount"
            data-source: "pricing"
            source-path: "finalTotal"
            data-type: "DOUBLE"
            required: true
          
          - solr-field: "discount_applied"
            data-source: "pricing"
            source-path: "discounts.totalDiscount"
            data-type: "DOUBLE"
            default-value: "0.0"
          
          - solr-field: "tax_amount"
            data-source: "pricing"
            source-path: "tax.totalTax"
            data-type: "DOUBLE"
            default-value: "0.0"
          
          # Composite business fields
          - solr-field: "order_classification"
            source-paths:
              - "customer.tier.level"
              - "order.type"
              - "pricing.totalAmount"
            combine-function: "classifyOrder"   # Custom business logic
            data-type: "STRING"
          
          - solr-field: "search_keywords"
            source-paths:
              - "customer.profile.fullName"
              - "order.orderId"
              - "products.*.name"
            combine-function: "generateSearchKeywords"
            data-type: "STRING"
          
          # Static and trigger fields
          - solr-field: "index_type"
            static-value: "ORDER_DOCUMENT"
          
          - solr-field: "trigger_action"
            trigger-field: "action"
          
          - solr-field: "trigger_timestamp"
            trigger-field: "timestamp"
            data-type: "DATE"
        
        # Default values for all documents
        default-values:
          indexed_at: "NOW"
          indexed_by: "ORDER_INDEXER"
          version: "1.0"
```

## Example 7: Service Layer Integration

### Configuration for Spring Service Beans:
```yaml
solr:
  update:
    collections:
      user_analytics:
        collection-name: "user_analytics"
        
        data-sources:
          # Service with complex business logic
          - name: "analytics"
            bean-name: "userAnalyticsService"
            method-name: "getUserAnalytics"
            input-fields: ["userId", "dateRange"]
            static-params:
              includeMetrics: "all"
              format: "summary"
            result-type: "SINGLE"
          
          # Repository direct access
          - name: "user_profile"
            bean-name: "userRepository"
            method-name: "findByIdWithDetails"
            input-fields: ["userId"]
            result-type: "SINGLE"
          
          # External service call
          - name: "recommendations"
            bean-name: "recommendationClient"
            method-name: "getUserRecommendations"
            input-fields: ["userId"]
            static-params:
              limit: "10"
              type: "PERSONALIZED"
            result-type: "LIST"
            required: false                   # External service might be down
```

## Usage Examples

### Java Service Usage:
```java
@Service
public class OrderUpdateHandler {
    
    private final DaoBasedPartialUpdateService updateService;
    
    // Handle order update events
    public void handleOrderUpdate(OrderUpdateEvent event) {
        List<Map<String, Object>> triggerData = Arrays.asList(
            Map.of(
                "orderId", event.getOrderId(),
                "customerId", event.getCustomerId(),
                "action", "UPDATE",
                "timestamp", new Date()
            )
        );
        
        updateService.processPartialUpdate("order_search", triggerData);
    }
    
    // Handle batch updates
    public void handleBatchUpdate(List<String> orderIds) {
        List<Map<String, Object>> triggerData = orderIds.stream()
            .map(orderId -> Map.of(
                "orderId", orderId,
                "action", "BATCH_UPDATE"
            ))
            .collect(Collectors.toList());
        
        updateService.processPartialUpdate("order_search", triggerData);
    }
}
```

### Custom Transformation Functions:
```java
@Component
public class BusinessTransformations {
    
    @PostConstruct
    public void registerCustomFunctions() {
        transformationService.registerTransformFunction("classifyOrder", this::classifyOrder);
        transformationService.registerTransformFunction("generateSearchKeywords", this::generateKeywords);
        transformationService.registerTransformFunction("uniqueList", this::createUniqueList);
    }
    
    private String classifyOrder(String compositeValue) {
        String[] parts = compositeValue.split("\\|");
        String tier = parts[0];
        String orderType = parts[1];
        double amount = Double.parseDouble(parts[2]);
        
        if ("PLATINUM".equals(tier) && amount > 1000) {
            return "VIP_LARGE_ORDER";
        } else if (amount > 500) {
            return "LARGE_ORDER";
        } else {
            return "STANDARD_ORDER";
        }
    }
    
    private String generateKeywords(String compositeValue) {
        // Business logic to generate search keywords
        return Arrays.stream(compositeValue.split("\\|"))
                    .flatMap(s -> Arrays.stream(s.split("\\s+")))
                    .filter(s -> s.length() > 2)
                    .map(String::toLowerCase)
                    .distinct()
                    .collect(Collectors.joining(" "));
    }
    
    private String createUniqueList(String compositeValue) {
        return Arrays.stream(compositeValue.split("\\|"))
                    .distinct()
                    .collect(Collectors.joining(","));
    }
}
```

## Configuration Best Practices

### 1. Data Source Organization
```yaml
# Group related data sources
data-sources:
  # Core business data (required)
  - name: "primary_entity"
    required: true
    retry-count: 3
  
  # Enrichment data (optional)
  - name: "enrichment_data"
    required: false
    cache-timeout-ms: 3600000
  
  # External services (optional with fallbacks)
  - name: "external_service"
    required: false
    retry-count: 1
```

### 2. Caching Strategy
```yaml
# Cache frequently accessed, slowly changing data
- name: "reference_data"
  cache-timeout-ms: 3600000    # 1 hour for reference data

# Cache moderately for user data
- name: "user_profile"
  cache-timeout-ms: 1800000    # 30 minutes for user profiles

# No cache for real-time data
- name: "real_time_status"
  cache-timeout-ms: 0          # No caching for real-time data
```

### 3. Error Handling Strategy
```yaml
# Critical data with retries
- name: "critical_data"
  required: true
  retry-count: 3

# Nice-to-have data without retries
- name: "optional_data"
  required: false
  retry-count: 0
```

This DAO-based configuration system provides complete flexibility to integrate with any existing DAO/Service layer while maintaining the zero-code-change philosophy for new collections and field mappings!
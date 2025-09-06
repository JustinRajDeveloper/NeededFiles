package com.example.testlib

import com.datastax.oss.driver.api.core.CqlSession
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory
import org.springframework.data.redis.core.RedisTemplate
import org.springframework.data.redis.serializer.StringRedisSerializer
import org.springframework.kafka.core.DefaultKafkaProducerFactory
import org.springframework.kafka.core.KafkaTemplate
import org.springframework.kafka.core.ProducerFactory
import org.springframework.test.context.DynamicPropertyRegistry
import org.springframework.test.context.DynamicPropertySource
import org.springframework.test.context.TestPropertySource
import spock.lang.Shared
import spock.lang.Specification

import java.net.InetSocketAddress
import java.sql.Connection
import java.sql.DriverManager

/**
 * Base Spock specification that starts all embedded services
 * and provides convenient access methods for testing
 */
@SpringBootTest
@TestPropertySource(properties = [
    "logging.level.com.example.testlib=INFO",
    "spring.jpa.hibernate.ddl-auto=create-drop",
    "spring.jpa.show-sql=false"
])
abstract class BaseIntegrationSpec extends Specification {
    
    @Shared
    protected static EmbeddedServicesManager servicesManager
    
    @Shared
    protected static boolean servicesStarted = false
    
    // Connection objects
    @Shared
    protected CqlSession cassandraSession
    
    @Shared
    protected RedisTemplate<String, Object> redisTemplate
    
    @Shared
    protected Connection postgresConnection
    
    @Shared
    protected KafkaTemplate<String, Object> kafkaTemplate
    
    // Service URLs and properties
    @Shared
    protected String cassandraContactPoint
    
    @Shared
    protected String redisUrl
    
    @Shared
    protected String postgresUrl
    
    @Shared
    protected String kafkaBootstrapServers
    
    @Shared
    protected String cosmosEndpoint
    
    /**
     * Setup that runs once per test class
     */
    def setupSpec() {
        if (!servicesStarted) {
            println "=== Starting Embedded Services for Test Suite ==="
            
            servicesManager = EmbeddedServicesManager.getInstance()
            servicesManager.startAllServices()
            
            // Get connection details
            updateConnectionDetails()
            
            // Initialize client connections
            initializeConnections()
            
            servicesStarted = true
            
            println "=== All Services Ready for Testing ==="
        }
    }
    
    /**
     * Cleanup that runs once per test class
     */
    def cleanupSpec() {
        println "=== Cleaning up Test Suite ==="
        
        // Close connections
        closeConnections()
        
        println "=== Test Suite Cleanup Complete ==="
    }
    
    /**
     * Setup that runs before each test method
     */
    def setup() {
        // Override in subclasses for per-test setup
        def testName = specificationContext.currentIteration.displayName
        println "🧪 Starting test: ${testName}"
    }
    
    /**
     * Cleanup that runs after each test method
     */
    def cleanup() {
        // Override in subclasses for per-test cleanup
        def testName = specificationContext.currentIteration.displayName
        println "✅ Completed test: ${testName}"
    }
    
    /**
     * Dynamic property source for Spring Boot
     */
    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        if (servicesManager == null) {
            servicesManager = EmbeddedServicesManager.getInstance()
            servicesManager.startAllServices()
        }
        
        // Cassandra properties
        if (servicesManager.isServiceRunning("cassandra")) {
            def contactPoint = servicesManager.getCassandraContactPoint()
            def parts = contactPoint.split(":")
            registry.add("spring.cassandra.contact-points", { parts[0] })
            registry.add("spring.cassandra.port", { Integer.parseInt(parts[1]) })
            registry.add("spring.cassandra.local-datacenter", { "datacenter1" })
            registry.add("spring.cassandra.keyspace-name", { "test_keyspace" })
        }
        
        // Redis properties
        if (servicesManager.isServiceRunning("redis")) {
            registry.add("spring.redis.host", { "localhost" })
            registry.add("spring.redis.port", { servicesManager.getRedisPort() })
        }
        
        // PostgreSQL properties
        if (servicesManager.isServiceRunning("postgres")) {
            registry.add("spring.datasource.url", { servicesManager.getPostgresUrl() })
            registry.add("spring.datasource.username", { servicesManager.getPostgresUsername() })
            registry.add("spring.datasource.password", { servicesManager.getPostgresPassword() })
        }
        
        // Kafka properties
        if (servicesManager.isServiceRunning("kafka")) {
            registry.add("spring.kafka.bootstrap-servers", { servicesManager.getKafkaBootstrapServers() })
        }
        
        // Cosmos properties
        if (servicesManager.isServiceRunning("cosmos")) {
            registry.add("azure.cosmos.endpoint", { servicesManager.getCosmosEndpoint() })
        }
    }
    
    private void updateConnectionDetails() {
        cassandraContactPoint = servicesManager.getCassandraContactPoint()
        redisUrl = servicesManager.getRedisUrl()
        postgresUrl = servicesManager.getPostgresUrl()
        kafkaBootstrapServers = servicesManager.getKafkaBootstrapServers()
        cosmosEndpoint = servicesManager.getCosmosEndpoint()
    }
    
    private void initializeConnections() {
        initializeCassandraConnection()
        initializeRedisConnection()
        initializePostgresConnection()
        initializeKafkaConnection()
    }
    
    private void initializeCassandraConnection() {
        if (!servicesManager.isServiceRunning("cassandra")) {
            println "Cassandra not running, skipping connection setup"
            return
        }
        
        try {
            def parts = cassandraContactPoint.split(":")
            cassandraSession = CqlSession.builder()
                .addContactPoint(new InetSocketAddress(parts[0], Integer.parseInt(parts[1])))
                .withLocalDatacenter("datacenter1")
                .build()
            
            // Create test keyspace
            cassandraSession.execute(
                "CREATE KEYSPACE IF NOT EXISTS test_keyspace " +
                "WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}"
            )
            
            // Use the keyspace
            cassandraSession.execute("USE test_keyspace")
            
            println "✓ Cassandra connection established"
        } catch (Exception e) {
            println "✗ Failed to initialize Cassandra connection: ${e.message}"
        }
    }
    
    private void initializeRedisConnection() {
        if (!servicesManager.isServiceRunning("redis")) {
            println "Redis not running, skipping connection setup"
            return
        }
        
        try {
            LettuceConnectionFactory connectionFactory = new LettuceConnectionFactory("localhost", servicesManager.getRedisPort())
            connectionFactory.afterPropertiesSet()
            
            redisTemplate = new RedisTemplate<>()
            redisTemplate.setConnectionFactory(connectionFactory)
            redisTemplate.setKeySerializer(new StringRedisSerializer())
            redisTemplate.setValueSerializer(new StringRedisSerializer())
            redisTemplate.afterPropertiesSet()
            
            // Test connection
            redisTemplate.opsForValue().set("test:connection", "ok")
            
            println "✓ Redis connection established"
        } catch (Exception e) {
            println "✗ Failed to initialize Redis connection: ${e.message}"
        }
    }
    
    private void initializePostgresConnection() {
        if (!servicesManager.isServiceRunning("postgres")) {
            println "PostgreSQL not running, skipping connection setup"
            return
        }
        
        try {
            postgresConnection = DriverManager.getConnection(
                servicesManager.getPostgresUrl(),
                servicesManager.getPostgresUsername(), 
                servicesManager.getPostgresPassword()
            )
            
            // Test connection
            def stmt = postgresConnection.createStatement()
            def rs = stmt.executeQuery("SELECT 1")
            rs.next()
            
            println "✓ PostgreSQL connection established"
        } catch (Exception e) {
            println "✗ Failed to initialize PostgreSQL connection: ${e.message}"
        }
    }
    
    private void initializeKafkaConnection() {
        if (!servicesManager.isServiceRunning("kafka")) {
            println "Kafka not running, skipping connection setup"
            return
        }
        
        try {
            Map<String, Object> producerProps = [
                "bootstrap.servers": servicesManager.getKafkaBootstrapServers(),
                "key.serializer": "org.apache.kafka.common.serialization.StringSerializer",
                "value.serializer": "org.apache.kafka.common.serialization.StringSerializer",
                "acks": "all",
                "retries": 3,
                "batch.size": 16384,
                "linger.ms": 1,
                "buffer.memory": 33554432
            ]
            
            ProducerFactory<String, Object> producerFactory = new DefaultKafkaProducerFactory<>(producerProps)
            kafkaTemplate = new KafkaTemplate<>(producerFactory)
            
            println "✓ Kafka connection established"
        } catch (Exception e) {
            println "✗ Failed to initialize Kafka connection: ${e.message}"
        }
    }
    
    private void closeConnections() {
        try {
            if (cassandraSession != null) {
                cassandraSession.close()
            }
        } catch (Exception e) {
            println "Error closing Cassandra session: ${e.message}"
        }
        
        try {
            if (postgresConnection != null) {
                postgresConnection.close()
            }
        } catch (Exception e) {
            println "Error closing PostgreSQL connection: ${e.message}"
        }
    }
    
    // === Utility Methods ===
    
    /**
     * Get service status summary
     */
    protected Map<String, Boolean> getServiceStatus() {
        return [
            "cassandra": servicesManager.isServiceRunning("cassandra"),
            "redis": servicesManager.isServiceRunning("redis"),
            "postgres": servicesManager.isServiceRunning("postgres"),
            "kafka": servicesManager.isServiceRunning("kafka"),
            "cosmos": servicesManager.isServiceRunning("cosmos")
        ]
    }
    
    /**
     * Get all service ports
     */
    protected Map<String, Integer> getServicePorts() {
        return servicesManager.getAllServicePorts()
    }
    
    /**
     * Wait for services to be ready (if needed)
     */
    protected void waitForServicesReady() {
        println "Waiting for all services to be ready..."
        Thread.sleep(2000)
        println "All services should be ready"
    }
}
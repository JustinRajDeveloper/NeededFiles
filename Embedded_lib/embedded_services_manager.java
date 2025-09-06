package com.example.testlib;

import com.github.nosan.embedded.cassandra.EmbeddedCassandraFactory;
import com.github.nosan.embedded.cassandra.api.Cassandra;
import io.zonky.test.db.postgres.embedded.EmbeddedPostgres;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.test.EmbeddedKafkaBroker;
import org.testcontainers.containers.CassandraContainer;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.containers.KafkaContainer;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.utility.DockerImageName;
import redis.embedded.RedisServer;

import java.io.IOException;
import java.net.ServerSocket;
import java.util.HashMap;
import java.util.Map;

/**
 * Manages all embedded services for testing.
 * Tries embedded approach first, falls back to TestContainers when needed.
 */
public class EmbeddedServicesManager {
    private static final Logger log = LoggerFactory.getLogger(EmbeddedServicesManager.class);
    
    private static EmbeddedServicesManager instance;
    
    // Embedded service instances
    private Cassandra embeddedCassandra;
    private RedisServer embeddedRedis;
    private EmbeddedPostgres embeddedPostgres;
    private EmbeddedKafkaBroker embeddedKafka;
    
    // TestContainer instances (fallback)
    private CassandraContainer<?> cassandraContainer;
    private GenericContainer<?> redisContainer;
    private PostgreSQLContainer<?> postgresContainer;
    private KafkaContainer kafkaContainer;
    private GenericContainer<?> cosmosContainer;
    
    // Port assignments
    private int cassandraPort = 9042;
    private int redisPort = 6379;
    private int postgresPort = 5432;
    private int kafkaPort = 9092;
    private int cosmosPort = 8081;
    
    // Service status and connection details
    private final Map<String, Boolean> serviceStatus = new HashMap<>();
    private final Map<String, Integer> servicePorts = new HashMap<>();
    private final Map<String, String> connectionUrls = new HashMap<>();
    
    private EmbeddedServicesManager() {
        // Register shutdown hook to clean up services
        Runtime.getRuntime().addShutdownHook(new Thread(this::stopAllServices));
    }
    
    public static synchronized EmbeddedServicesManager getInstance() {
        if (instance == null) {
            instance = new EmbeddedServicesManager();
        }
        return instance;
    }
    
    /**
     * Start all embedded services
     */
    public void startAllServices() {
        log.info("Starting all embedded services...");
        
        assignAvailablePorts();
        
        startCassandra();
        startRedis();
        startPostgres();
        startKafka();
        startCosmos();
        
        log.info("Service startup completed");
        logServiceSummary();
    }
    
    /**
     * Stop all embedded services
     */
    public void stopAllServices() {
        log.info("Stopping all embedded services...");
        
        stopCassandra();
        stopRedis();
        stopPostgres();
        stopKafka();
        stopCosmos();
        
        serviceStatus.clear();
        servicePorts.clear();
        connectionUrls.clear();
        
        log.info("All services stopped");
    }
    
    private void assignAvailablePorts() {
        cassandraPort = findAvailablePort(9042);
        redisPort = findAvailablePort(6379);
        postgresPort = findAvailablePort(5432);
        kafkaPort = findAvailablePort(9092);
        cosmosPort = findAvailablePort(8081);
    }
    
    private void startCassandra() {
        try {
            log.info("Starting Cassandra (embedded approach)...");
            
            EmbeddedCassandraFactory factory = new EmbeddedCassandraFactory();
            factory.setPort(cassandraPort);
            factory.setJmxPort(findAvailablePort(7199));
            
            embeddedCassandra = factory.create();
            embeddedCassandra.start();
            
            // Wait for Cassandra to be ready
            Thread.sleep(8000);
            
            servicePorts.put("cassandra", cassandraPort);
            connectionUrls.put("cassandra", "127.0.0.1:" + cassandraPort);
            serviceStatus.put("cassandra", true);
            
            log.info("✓ Cassandra started successfully (embedded) on port {}", cassandraPort);
            
        } catch (Exception e) {
            log.warn("Embedded Cassandra failed, trying TestContainers: {}", e.getMessage());
            
            try {
                cassandraContainer = new CassandraContainer<>(DockerImageName.parse("cassandra:4.1"))
                    .withExposedPorts(9042);
                cassandraContainer.start();
                
                cassandraPort = cassandraContainer.getMappedPort(9042);
                servicePorts.put("cassandra", cassandraPort);
                connectionUrls.put("cassandra", cassandraContainer.getHost() + ":" + cassandraPort);
                serviceStatus.put("cassandra", true);
                
                log.info("✓ Cassandra started successfully (container) on port {}", cassandraPort);
                
            } catch (Exception containerException) {
                log.error("✗ Failed to start Cassandra: {}", containerException.getMessage());
                serviceStatus.put("cassandra", false);
            }
        }
    }
    
    private void startRedis() {
        try {
            log.info("Starting Redis (embedded approach)...");
            
            embeddedRedis = RedisServer.builder()
                .port(redisPort)
                .setting("maxmemory 128m")
                .build();
            embeddedRedis.start();
            
            servicePorts.put("redis", redisPort);
            connectionUrls.put("redis", "redis://localhost:" + redisPort);
            serviceStatus.put("redis", true);
            
            log.info("✓ Redis started successfully (embedded) on port {}", redisPort);
            
        } catch (Exception e) {
            log.warn("Embedded Redis failed (common on Mac), trying TestContainers: {}", e.getMessage());
            
            try {
                redisContainer = new GenericContainer<>(DockerImageName.parse("redis:7-alpine"))
                    .withExposedPorts(6379);
                redisContainer.start();
                
                redisPort = redisContainer.getMappedPort(6379);
                servicePorts.put("redis", redisPort);
                connectionUrls.put("redis", "redis://" + redisContainer.getHost() + ":" + redisPort);
                serviceStatus.put("redis", true);
                
                log.info("✓ Redis started successfully (container) on port {}", redisPort);
                
            } catch (Exception containerException) {
                log.error("✗ Failed to start Redis: {}", containerException.getMessage());
                serviceStatus.put("redis", false);
            }
        }
    }
    
    private void startPostgres() {
        try {
            log.info("Starting PostgreSQL (embedded approach)...");
            
            embeddedPostgres = EmbeddedPostgres.builder()
                .setPort(postgresPort)
                .start();
            
            String jdbcUrl = embeddedPostgres.getJdbcUrl("postgres", "postgres");
            
            servicePorts.put("postgres", postgresPort);
            connectionUrls.put("postgres", jdbcUrl);
            serviceStatus.put("postgres", true);
            
            log.info("✓ PostgreSQL started successfully (embedded) on port {}", postgresPort);
            
        } catch (Exception e) {
            log.warn("Embedded PostgreSQL failed, trying TestContainers: {}", e.getMessage());
            
            try {
                postgresContainer = new PostgreSQLContainer<>(DockerImageName.parse("postgres:15-alpine"))
                    .withDatabaseName("testdb")
                    .withUsername("test")
                    .withPassword("test");
                postgresContainer.start();
                
                postgresPort = postgresContainer.getMappedPort(5432);
                servicePorts.put("postgres", postgresPort);
                connectionUrls.put("postgres", postgresContainer.getJdbcUrl());
                serviceStatus.put("postgres", true);
                
                log.info("✓ PostgreSQL started successfully (container) on port {}", postgresPort);
                
            } catch (Exception containerException) {
                log.error("✗ Failed to start PostgreSQL: {}", containerException.getMessage());
                serviceStatus.put("postgres", false);
            }
        }
    }
    
    private void startKafka() {
        try {
            log.info("Starting Kafka (embedded approach)...");
            
            embeddedKafka = new EmbeddedKafkaBroker(1)
                .kafkaPorts(kafkaPort)
                .brokerProperty("listeners", "PLAINTEXT://localhost:" + kafkaPort)
                .brokerProperty("advertised.listeners", "PLAINTEXT://localhost:" + kafkaPort);
                
            embeddedKafka.afterPropertiesSet();
            
            servicePorts.put("kafka", kafkaPort);
            connectionUrls.put("kafka", "localhost:" + kafkaPort);
            serviceStatus.put("kafka", true);
            
            log.info("✓ Kafka started successfully (embedded) on port {}", kafkaPort);
            
        } catch (Exception e) {
            log.warn("Embedded Kafka failed, trying TestContainers: {}", e.getMessage());
            
            try {
                kafkaContainer = new KafkaContainer(DockerImageName.parse("confluentinc/cp-kafka:7.4.0"));
                kafkaContainer.start();
                
                kafkaPort = kafkaContainer.getMappedPort(9093);
                servicePorts.put("kafka", kafkaPort);
                connectionUrls.put("kafka", kafkaContainer.getBootstrapServers());
                serviceStatus.put("kafka", true);
                
                log.info("✓ Kafka started successfully (container) on port {}", kafkaPort);
                
            } catch (Exception containerException) {
                log.error("✗ Failed to start Kafka: {}", containerException.getMessage());
                serviceStatus.put("kafka", false);
            }
        }
    }
    
    private void startCosmos() {
        try {
            log.info("Starting Cosmos DB Emulator (container only)...");
            
            cosmosContainer = new GenericContainer<>(DockerImageName.parse("mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest"))
                .withEnv("AZURE_COSMOS_EMULATOR_PARTITION_COUNT", "2")
                .withEnv("AZURE_COSMOS_EMULATOR_ENABLE_DATA_PERSISTENCE", "false")
                .withExposedPorts(8081, 10251, 10252, 10253, 10254);
                
            cosmosContainer.start();
            
            cosmosPort = cosmosContainer.getMappedPort(8081);
            servicePorts.put("cosmos", cosmosPort);
            connectionUrls.put("cosmos", "https://" + cosmosContainer.getHost() + ":" + cosmosPort);
            
            // Wait for Cosmos to be ready
            Thread.sleep(45000);
            
            serviceStatus.put("cosmos", true);
            log.info("✓ Cosmos DB Emulator started successfully on port {}", cosmosPort);
            
        } catch (Exception e) {
            log.warn("✗ Cosmos DB Emulator failed (Docker required): {}", e.getMessage());
            serviceStatus.put("cosmos", false);
        }
    }
    
    private void stopCassandra() {
        if (embeddedCassandra != null) {
            try {
                embeddedCassandra.stop();
                log.debug("Embedded Cassandra stopped");
            } catch (Exception e) {
                log.error("Error stopping embedded Cassandra", e);
            }
        }
        if (cassandraContainer != null) {
            try {
                cassandraContainer.stop();
                log.debug("Cassandra container stopped");
            } catch (Exception e) {
                log.error("Error stopping Cassandra container", e);
            }
        }
    }
    
    private void stopRedis() {
        if (embeddedRedis != null) {
            try {
                embeddedRedis.stop();
                log.debug("Embedded Redis stopped");
            } catch (Exception e) {
                log.error("Error stopping embedded Redis", e);
            }
        }
        if (redisContainer != null) {
            try {
                redisContainer.stop();
                log.debug("Redis container stopped");
            } catch (Exception e) {
                log.error("Error stopping Redis container", e);
            }
        }
    }
    
    private void stopPostgres() {
        if (embeddedPostgres != null) {
            try {
                embeddedPostgres.close();
                log.debug("Embedded PostgreSQL stopped");
            } catch (Exception e) {
                log.error("Error stopping embedded PostgreSQL", e);
            }
        }
        if (postgresContainer != null) {
            try {
                postgresContainer.stop();
                log.debug("PostgreSQL container stopped");
            } catch (Exception e) {
                log.error("Error stopping PostgreSQL container", e);
            }
        }
    }
    
    private void stopKafka() {
        if (embeddedKafka != null) {
            try {
                embeddedKafka.destroy();
                log.debug("Embedded Kafka stopped");
            } catch (Exception e) {
                log.error("Error stopping embedded Kafka", e);
            }
        }
        if (kafkaContainer != null) {
            try {
                kafkaContainer.stop();
                log.debug("Kafka container stopped");
            } catch (Exception e) {
                log.error("Error stopping Kafka container", e);
            }
        }
    }
    
    private void stopCosmos() {
        if (cosmosContainer != null) {
            try {
                cosmosContainer.stop();
                log.debug("Cosmos container stopped");
            } catch (Exception e) {
                log.error("Error stopping Cosmos container", e);
            }
        }
    }
    
    private int findAvailablePort(int preferredPort) {
        if (isPortAvailable(preferredPort)) {
            return preferredPort;
        }
        
        try (ServerSocket socket = new ServerSocket(0)) {
            return socket.getLocalPort();
        } catch (IOException e) {
            throw new RuntimeException("Could not find available port", e);
        }
    }
    
    private boolean isPortAvailable(int port) {
        try (ServerSocket socket = new ServerSocket(port)) {
            return true;
        } catch (IOException e) {
            return false;
        }
    }
    
    private void logServiceSummary() {
        log.info("=== Service Summary ===");
        serviceStatus.forEach((service, running) -> {
            Integer port = servicePorts.get(service);
            String url = connectionUrls.get(service);
            log.info("{}: {} | Port: {} | URL: {}", 
                service.toUpperCase(), 
                running ? "✓ RUNNING" : "✗ FAILED",
                port != null ? port : "N/A",
                url != null ? url : "N/A");
        });
        log.info("=====================");
    }
    
    // Public accessors
    public int getCassandraPort() { return cassandraPort; }
    public int getRedisPort() { return redisPort; }
    public int getPostgresPort() { return postgresPort; }
    public int getKafkaPort() { return kafkaPort; }
    public int getCosmosPort() { return cosmosPort; }
    
    public String getCassandraContactPoint() {
        return connectionUrls.getOrDefault("cassandra", "127.0.0.1:" + cassandraPort);
    }
    
    public String getRedisUrl() {
        return connectionUrls.getOrDefault("redis", "redis://localhost:" + redisPort);
    }
    
    public String getPostgresUrl() {
        return connectionUrls.getOrDefault("postgres", "jdbc:postgresql://localhost:" + postgresPort + "/postgres");
    }
    
    public String getPostgresUsername() {
        return postgresContainer != null ? postgresContainer.getUsername() : "postgres";
    }
    
    public String getPostgresPassword() {
        return postgresContainer != null ? postgresContainer.getPassword() : "postgres";
    }
    
    public String getKafkaBootstrapServers() {
        return connectionUrls.getOrDefault("kafka", "localhost:" + kafkaPort);
    }
    
    public String getCosmosEndpoint() {
        return connectionUrls.getOrDefault("cosmos", "https://localhost:" + cosmosPort);
    }
    
    public boolean isServiceRunning(String serviceName) {
        return serviceStatus.getOrDefault(serviceName, false);
    }
    
    public Map<String, Integer> getAllServicePorts() {
        return new HashMap<>(servicePorts);
    }
    
    public Map<String, String> getAllConnectionUrls() {
        return new HashMap<>(connectionUrls);
    }
}
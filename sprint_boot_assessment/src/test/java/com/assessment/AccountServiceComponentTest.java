package com.assessment;

import com.assessment.dto.AccountDto;
import com.assessment.entity.Account;
import com.assessment.service.AccountService;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.tomakehurst.wiremock.client.WireMock;
import org.apache.kafka.clients.consumer.Consumer;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.data.cassandra.core.CassandraTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.kafka.core.DefaultKafkaConsumerFactory;
import org.springframework.kafka.test.utils.KafkaTestUtils;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.Collections;
import java.util.Map;
import java.util.UUID;

import static com.github.tomakehurst.wiremock.client.WireMock.*;
import static org.junit.jupiter.api.Assertions.*;

class AccountServiceComponentTest extends ComponentTestBase {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private AccountService accountService;

    @Autowired
    private CassandraTemplate cassandraTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @LocalServerPort
    private int port;

    @Test
    void testCreateAccount_EndToEnd_ShouldFailInitially() {
        // Setup WireMock for external validation service
        wireMockServer.stubFor(post(urlEqualTo("/validate"))
                .willReturn(aResponse()
                        .withStatus(200)
                        .withHeader("Content-Type", "application/json")
                        .withBody("{\"valid\": true, \"riskScore\": 25}")
                ));

        // Prepare test data
        AccountDto accountDto = new AccountDto();
        accountDto.setAccountNumber("ACC-TEST-001");
        accountDto.setAccountHolderName("Test User");
        accountDto.setEmail("test@example.com");
        accountDto.setBalance(new BigDecimal("5000.00"));
        accountDto.setAccountType("CHECKING");

        // This test will FAIL until developer implements createAccount method
        assertThrows(RuntimeException.class, () -> {
            ResponseEntity<Account> response = restTemplate.postForEntity(
                    "http://localhost:" + port + "/api/accounts",
                    accountDto,
                    Account.class
            );
        });
    }

    @Test
    void testCreateAccount_FullFlow_WhenImplemented() {
        // This test shows what should happen when properly implemented

        // 1. Mock external validation service
        wireMockServer.stubFor(post(urlEqualTo("/validate"))
                .willReturn(aResponse()
                        .withStatus(200)
                        .withHeader("Content-Type", "application/json")
                        .withBody("{\"valid\": true}")
                ));

        AccountDto accountDto = new AccountDto();
        accountDto.setAccountNumber("ACC-IMPL-001");
        accountDto.setAccountHolderName("Implemented User");
        accountDto.setEmail("implemented@example.com");
        accountDto.setBalance(new BigDecimal("3000.00"));
        accountDto.setAccountType("SAVINGS");

        // When properly implemented, this should:
        // 1. Validate account via external service
        // 2. Save to Cassandra
        // 3. Send Kafka event
        // 4. Return created account

        try {
            ResponseEntity<Account> response = restTemplate.postForEntity(
                    "http://localhost:" + port + "/api/accounts",
                    accountDto,
                    Account.class
            );

            // Verify HTTP response
            assertEquals(HttpStatus.CREATED, response.getStatusCode());
            assertNotNull(response.getBody());
            assertEquals("ACC-IMPL-001", response.getBody().getAccountNumber());

            // Verify account saved in Cassandra
            Account savedAccount = cassandraTemplate.selectOneById(
                    response.getBody().getId(), Account.class);
            assertNotNull(savedAccount);
            assertEquals("ACTIVE", savedAccount.getStatus());

            // Verify external service was called
            wireMockServer.verify(postRequestedFor(urlEqualTo("/validate")));

            // Verify Kafka message sent (would need Kafka consumer setup)
            // This part would be implemented when Kafka producer is working

        } catch (RuntimeException e) {
            // Expected to fail until implementation is complete
            assertTrue(e.getMessage().contains("Method not implemented"));
        }
    }

    @Test
    void testGetAllAccounts_ShouldFailInitially() {
        // This will fail until getAllAccounts is implemented
        assertThrows(RuntimeException.class, () -> {
            ResponseEntity<Account[]> response = restTemplate.getForEntity(
                    "http://localhost:" + port + "/api/accounts",
                    Account[].class
            );
        });
    }

    @Test
    void testUpdateAccountBalance_WithKafkaValidation() {
        // Create test account first (this will fail until createAccount works)
        UUID testId = UUID.randomUUID();

        assertThrows(RuntimeException.class, () -> {
            ResponseEntity<Account> response = restTemplate.postForEntity(
                    "http://localhost:" + port + "/api/accounts/" + testId + "/balance?balance=2500.00",
                    null,
                    Account.class
            );
        });
    }

    private Consumer<String, String> createKafkaConsumer() {
        Map<String, Object> consumerProps = KafkaTestUtils.consumerProps(
                kafka.getBootstrapServers(), "test-group", "true");
        consumerProps.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        consumerProps.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);

        Consumer<String, String> consumer = new DefaultKafkaConsumerFactory<String, String>(consumerProps)
                .createConsumer();
        consumer.subscribe(Collections.singletonList("account-events"));
        return consumer;
    }
}
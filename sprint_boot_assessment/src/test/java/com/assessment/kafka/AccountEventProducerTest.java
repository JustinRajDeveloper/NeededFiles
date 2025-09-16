package com.assessment.kafka;

import com.assessment.entity.Account;
import com.assessment.service.kafka.AccountEventProducer;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.kafka.core.KafkaTemplate;

import java.math.BigDecimal;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class AccountEventProducerTest {

    @Mock
    private KafkaTemplate<String, String> kafkaTemplate;

    @Mock
    private ObjectMapper objectMapper;

    @InjectMocks
    private AccountEventProducer accountEventProducer;

    private Account account;

    @BeforeEach
    void setUp() {
        account = new Account();
        account.setId(UUID.randomUUID());
        account.setAccountNumber("ACC-123456");
        account.setAccountHolderName("John Doe");
        account.setEmail("john.doe@example.com");
        account.setBalance(new BigDecimal("1000.00"));
        account.setAccountType("SAVINGS");
    }

    @Test
    void testSendAccountCreatedEvent() {
        // This test will fail until sendAccountCreatedEvent is implemented
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            accountEventProducer.sendAccountCreatedEvent(account);
        });
        assertTrue(exception.getMessage().contains("Method not implemented"));
    }

    @Test
    void testSendAccountUpdatedEvent() {
        // This test will fail until sendAccountUpdatedEvent is implemented
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            accountEventProducer.sendAccountUpdatedEvent(account);
        });
        assertTrue(exception.getMessage().contains("Method not implemented"));
    }

    @Test
    void testSendAccountDeletedEvent() {
        // This test will fail until sendAccountDeletedEvent is implemented
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            accountEventProducer.sendAccountDeletedEvent("account-id");
        });
        assertTrue(exception.getMessage().contains("Method not implemented"));
    }
}
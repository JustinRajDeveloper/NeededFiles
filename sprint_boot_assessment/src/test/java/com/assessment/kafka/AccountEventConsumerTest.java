package com.assessment.kafka;

import com.assessment.service.kafka.AccountEventConsumer;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class AccountEventConsumerTest {

    @Mock
    private ObjectMapper objectMapper;

    @InjectMocks
    private AccountEventConsumer accountEventConsumer;

    @Test
    void testConsumeAccountEvent() {
        String testMessage = "{\"eventType\":\"ACCOUNT_CREATED\",\"accountId\":\"123\"}";

        // This test will fail until consumeAccountEvent is implemented
        assertThrows(RuntimeException.class, () -> {
            accountEventConsumer.consumeAccountEvent(testMessage);
        });
    }
}
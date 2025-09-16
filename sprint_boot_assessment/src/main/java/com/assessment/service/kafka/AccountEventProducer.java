package com.assessment.service.kafka;

import com.assessment.entity.Account;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class AccountEventProducer {
    
    private static final String ACCOUNT_TOPIC = "account-events";
    
    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    // TODO: Implement this method
    // Should send account created event to Kafka topic
    public void sendAccountCreatedEvent(Account account) {
        // Implementation needed:
        // 1. Create event object with account details and event type
        // 2. Convert to JSON
        // 3. Send to Kafka topic
        throw new RuntimeException("Method not implemented");
    }
    
    // TODO: Implement this method
    // Should send account updated event to Kafka topic  
    public void sendAccountUpdatedEvent(Account account) {
        // Implementation needed:
        // 1. Create event object with account details and event type
        // 2. Convert to JSON
        // 3. Send to Kafka topic
        throw new RuntimeException("Method not implemented");
    }
    
    // TODO: Implement this method
    // Should send account deleted event to Kafka topic
    public void sendAccountDeletedEvent(String accountId) {
        // Implementation needed:
        // 1. Create event object with account ID and event type
        // 2. Convert to JSON  
        // 3. Send to Kafka topic
        throw new RuntimeException("Method not implemented");
    }
}
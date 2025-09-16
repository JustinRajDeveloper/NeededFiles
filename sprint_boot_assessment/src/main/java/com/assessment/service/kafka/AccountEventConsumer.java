package com.assessment.service.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Service
public class AccountEventConsumer {
    
    private static final Logger logger = LoggerFactory.getLogger(AccountEventConsumer.class);
    
    @Autowired
    private ObjectMapper objectMapper;
    
    // TODO: Implement this method
    // Should consume messages from account-events topic and process them
    @KafkaListener(topics = "account-events", groupId = "account-service-group")
    public void consumeAccountEvent(String message) {
        // Implementation needed:
        // 1. Parse JSON message
        // 2. Extract event type and account details
        // 3. Process based on event type (created, updated, deleted)
        // 4. Log the processed event
        throw new RuntimeException("Method not implemented");
    }
}
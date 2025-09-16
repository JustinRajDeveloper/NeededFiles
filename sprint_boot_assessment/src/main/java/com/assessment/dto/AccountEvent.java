package com.assessment.dto;

import java.time.LocalDateTime;
import java.util.UUID;

public class AccountEvent {
    private String eventType;
    private UUID accountId;
    private String accountNumber;
    private LocalDateTime timestamp;
    private Object eventData;
    
    public AccountEvent() {
        this.timestamp = LocalDateTime.now();
    }
    
    public AccountEvent(String eventType, UUID accountId, String accountNumber, Object eventData) {
        this();
        this.eventType = eventType;
        this.accountId = accountId;
        this.accountNumber = accountNumber;
        this.eventData = eventData;
    }
    
    // Getters and Setters
    public String getEventType() { return eventType; }
    public void setEventType(String eventType) { this.eventType = eventType; }
    
    public UUID getAccountId() { return accountId; }
    public void setAccountId(UUID accountId) { this.accountId = accountId; }
    
    public String getAccountNumber() { return accountNumber; }
    public void setAccountNumber(String accountNumber) { this.accountNumber = accountNumber; }
    
    public LocalDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(LocalDateTime timestamp) { this.timestamp = timestamp; }
    
    public Object getEventData() { return eventData; }
    public void setEventData(Object eventData) { this.eventData = eventData; }
}
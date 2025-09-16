package com.assessment.service.external;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
public class ExternalValidationService {
    
    @Autowired
    private RestTemplate restTemplate;
    
    @Value("${external.validation.url:http://localhost:8080/validate}")
    private String validationUrl;
    
    // TODO: Implement this method
    // Should make REST call to external service to validate account
    // Return true if valid, false otherwise
    public boolean validateAccount(String accountNumber, String email) {
        // Implementation needed:
        // 1. Create validation request
        // 2. Make REST call to external validation service
        // 3. Parse response and return validation result
        throw new RuntimeException("Method not implemented");
    }
    
    // TODO: Implement this method  
    // Should make REST call to get account risk score
    // Return risk score as integer (0-100)
    public int getAccountRiskScore(String accountNumber) {
        // Implementation needed:
        // 1. Make REST call to risk assessment service
        // 2. Parse response and return risk score
        throw new RuntimeException("Method not implemented");
    }
}
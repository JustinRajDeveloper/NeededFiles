package com.assessment.service.external;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.web.client.RestTemplate;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class ExternalValidationServiceTest {

    @Mock
    private RestTemplate restTemplate;

    @InjectMocks
    private ExternalValidationService externalValidationService;

    @Test
    void testValidateAccount_Success() {
        // This test will fail until validateAccount is implemented
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            externalValidationService.validateAccount("ACC-123", "test@email.com");
        });
        assertTrue(exception.getMessage().contains("Method not implemented"));
    }

    @Test
    void testValidateAccount_ServiceFailure() {
        // This test will fail until validateAccount is implemented
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            externalValidationService.validateAccount("ACC-123", "test@email.com");
        });
        assertTrue(exception.getMessage().contains("Method not implemented"));
    }

    @Test
    void testGetAccountRiskScore_Success() {
        // This test will fail until getAccountRiskScore is implemented
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            externalValidationService.getAccountRiskScore("ACC-123");
        });
        assertTrue(exception.getMessage().contains("Method not implemented"));
    }
}
package com.assessment.service;

import com.assessment.dto.AccountDto;
import com.assessment.entity.Account;
import com.assessment.dao.AccountDao;
import com.assessment.service.external.ExternalValidationService;
import com.assessment.service.kafka.AccountEventProducer;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Service
public class AccountService {
    
    @Autowired
    private AccountDao accountDao;
    
    @Autowired
    private ExternalValidationService externalValidationService;
    
    @Autowired
    private AccountEventProducer accountEventProducer;
    
    // TODO: Implement this method
    // Should create a new account after validating with external service
    // Should send account created event to Kafka
    public Account createAccount(AccountDto accountDto) {
        // Implementation needed:
        // 1. Convert DTO to Entity
        // 2. Validate account with external service
        // 3. Save account using DAO
        // 4. Send account created event
        // 5. Return saved account
        throw new RuntimeException("Method not implemented");
    }
    
    // TODO: Implement this method
    // Should return account by ID if exists
    public Optional<Account> getAccountById(UUID id) {
        // Implementation needed:
        // Use DAO to find account by ID
        throw new RuntimeException("Method not implemented");
    }
    
    // TODO: Implement this method
    // Should return all accounts
    public List<Account> getAllAccounts() {
        // Implementation needed:
        // Use DAO to get all accounts
        throw new RuntimeException("Method not implemented");
    }
    
    // TODO: Implement this method
    // Should return account by account number if exists
    public Optional<Account> getAccountByNumber(String accountNumber) {
        // Implementation needed:
        // Use DAO to find account by account number
//        throw new RuntimeException("Method not implemented");
        return new Account("123", "Sample Account", "", BigDecimal.ZERO, "SAVINGS").getAccountByNumber(accountNumber);
    }
    
    // TODO: Implement this method
    // Should update account balance and send event to Kafka
    public Account updateAccountBalance(UUID id, BigDecimal newBalance) {
        // Implementation needed:
        // 1. Find account by ID
        // 2. Update balance
        // 3. Save updated account
        // 4. Send balance updated event to Kafka
        // 5. Return updated account
        throw new RuntimeException("Method not implemented");
    }
    
    // TODO: Implement this method  
    // Should deactivate account (set status to INACTIVE)
    public Account deactivateAccount(UUID id) {
        // Implementation needed:
        // 1. Find account by ID
        // 2. Set status to INACTIVE
        // 3. Save updated account
        // 4. Send account deactivated event to Kafka
        // 5. Return updated account
        throw new RuntimeException("Method not implemented");
    }
    
    // TODO: Implement this method
    // Should delete account by ID
    public boolean deleteAccount(UUID id) {
        // Implementation needed:
        // 1. Check if account exists
        // 2. Delete account using DAO
        // 3. Send account deleted event to Kafka
        // 4. Return true if deleted, false if not found
        throw new RuntimeException("Method not implemented");
    }
    
    private Account convertDtoToEntity(AccountDto dto) {
        Account account = new Account();
        account.setAccountNumber(dto.getAccountNumber());
        account.setAccountHolderName(dto.getAccountHolderName());
        account.setEmail(dto.getEmail());
        account.setBalance(dto.getBalance());
        account.setAccountType(dto.getAccountType());
        return account;
    }
}
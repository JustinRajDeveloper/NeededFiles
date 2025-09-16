package com.assessment.controller;

import com.assessment.dto.AccountDto;
import com.assessment.entity.Account;
import com.assessment.service.AccountService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@RestController
@RequestMapping("/api/accounts")
public class AccountController {
    
    @Autowired
    private AccountService accountService;
    
    @PostMapping
    public ResponseEntity<Account> createAccount(@Valid @RequestBody AccountDto accountDto) {
        Account createdAccount = accountService.createAccount(accountDto);
        return new ResponseEntity<>(createdAccount, HttpStatus.CREATED);
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<Account> getAccountById(@PathVariable UUID id) {
        Optional<Account> account = accountService.getAccountById(id);
        return account.map(acc -> ResponseEntity.ok(acc))
                     .orElse(ResponseEntity.notFound().build());
    }
    
    @GetMapping
    public ResponseEntity<List<Account>> getAllAccounts() {
        List<Account> accounts = accountService.getAllAccounts();
        return ResponseEntity.ok(accounts);
    }
    
    @GetMapping("/number/{accountNumber}")
    public ResponseEntity<Account> getAccountByNumber(@PathVariable String accountNumber) {
        Optional<Account> account = accountService.getAccountByNumber(accountNumber);
        return account.map(acc -> ResponseEntity.ok(acc))
                     .orElse(ResponseEntity.notFound().build());
    }
    
    @PutMapping("/{id}/balance")
    public ResponseEntity<Account> updateAccountBalance(@PathVariable UUID id, 
                                                       @RequestParam BigDecimal balance) {
        Account updatedAccount = accountService.updateAccountBalance(id, balance);
        return ResponseEntity.ok(updatedAccount);
    }
    
    @PutMapping("/{id}/deactivate")
    public ResponseEntity<Account> deactivateAccount(@PathVariable UUID id) {
        Account deactivatedAccount = accountService.deactivateAccount(id);
        return ResponseEntity.ok(deactivatedAccount);
    }
    
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteAccount(@PathVariable UUID id) {
        boolean deleted = accountService.deleteAccount(id);
        return deleted ? ResponseEntity.noContent().build() : ResponseEntity.notFound().build();
    }
}
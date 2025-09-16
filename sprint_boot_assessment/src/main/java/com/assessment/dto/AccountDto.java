package com.assessment.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.UUID;

public class AccountDto {
    private UUID id;
    
    @NotBlank(message = "Account number cannot be blank")
    private String accountNumber;
    
    @NotBlank(message = "Account holder name cannot be blank")
    private String accountHolderName;
    
    @Email(message = "Email should be valid")
    @NotBlank(message = "Email cannot be blank")
    private String email;
    
    @NotNull(message = "Balance cannot be null")
    private BigDecimal balance;
    
    @NotBlank(message = "Account type cannot be blank")
    private String accountType;
    
    // Constructors, getters, and setters
    public AccountDto() {}
    
    public AccountDto(String accountNumber, String accountHolderName, String email, 
                     BigDecimal balance, String accountType) {
        this.accountNumber = accountNumber;
        this.accountHolderName = accountHolderName;
        this.email = email;
        this.balance = balance;
        this.accountType = accountType;
    }
    
    // Getters and Setters
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }
    
    public String getAccountNumber() { return accountNumber; }
    public void setAccountNumber(String accountNumber) { this.accountNumber = accountNumber; }
    
    public String getAccountHolderName() { return accountHolderName; }
    public void setAccountHolderName(String accountHolderName) { this.accountHolderName = accountHolderName; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    
    public BigDecimal getBalance() { return balance; }
    public void setBalance(BigDecimal balance) { this.balance = balance; }
    
    public String getAccountType() { return accountType; }
    public void setAccountType(String accountType) { this.accountType = accountType; }
}
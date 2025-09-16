package com.assessment.entity;

import org.springframework.data.cassandra.core.mapping.Column;
import org.springframework.data.cassandra.core.mapping.PrimaryKey;
import org.springframework.data.cassandra.core.mapping.Table;
import com.fasterxml.jackson.annotation.JsonFormat;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Table("accounts")
public class Account {
    
    @PrimaryKey
    private UUID id;
    
    @Column("account_number")
    @NotBlank(message = "Account number cannot be blank")
    private String accountNumber;
    
    @Column("account_holder_name")
    @NotBlank(message = "Account holder name cannot be blank")
    private String accountHolderName;
    
    @Column("email")
    @Email(message = "Email should be valid")
    @NotBlank(message = "Email cannot be blank")
    private String email;
    
    @Column("balance")
    @NotNull(message = "Balance cannot be null")
    private BigDecimal balance;
    
    @Column("account_type")
    @NotBlank(message = "Account type cannot be blank")
    private String accountType;
    
    @Column("status")
    private String status;
    
    @Column("created_at")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createdAt;
    
    @Column("updated_at")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime updatedAt;
    
    // Constructors
    public Account() {
        this.id = UUID.randomUUID();
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
        this.status = "ACTIVE";
    }
    
    public Account(String accountNumber, String accountHolderName, String email, 
                  BigDecimal balance, String accountType) {
        this();
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
    public void setBalance(BigDecimal balance) { 
        this.balance = balance;
        this.updatedAt = LocalDateTime.now();
    }
    
    public String getAccountType() { return accountType; }
    public void setAccountType(String accountType) { this.accountType = accountType; }
    
    public String getStatus() { return status; }
    public void setStatus(String status) { 
        this.status = status;
        this.updatedAt = LocalDateTime.now();
    }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
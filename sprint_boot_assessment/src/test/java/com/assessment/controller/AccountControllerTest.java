package com.assessment.controller;

import com.assessment.dto.AccountDto;
import com.assessment.entity.Account;
import com.assessment.service.AccountService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.Optional;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(AccountController.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class AccountControllerTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @MockBean
    private AccountService accountService;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    private AccountDto accountDto;
    private Account account;
    
    @BeforeEach
    void setUp() {
        accountDto = new AccountDto();
        accountDto.setAccountNumber("ACC-123456");
        accountDto.setAccountHolderName("John Doe");
        accountDto.setEmail("john.doe@example.com");
        accountDto.setBalance(new BigDecimal("1000.00"));
        accountDto.setAccountType("SAVINGS");
        
        account = new Account();
        account.setId(UUID.randomUUID());
        account.setAccountNumber("ACC-123456");
        account.setAccountHolderName("John Doe");
        account.setEmail("john.doe@example.com");
        account.setBalance(new BigDecimal("1000.00"));
        account.setAccountType("SAVINGS");
    }
    
    @Test
    void testCreateAccount_Success() throws Exception {
        when(accountService.createAccount(any(AccountDto.class))).thenReturn(account);
        
        mockMvc.perform(post("/api/accounts")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(accountDto)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.accountNumber").value("ACC-123456"));
    }
    
    @Test
    void testCreateAccount_ValidationError() throws Exception {
        accountDto.setEmail("invalid-email");
        
        mockMvc.perform(post("/api/accounts")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(accountDto)))
                .andExpect(status().isBadRequest());
    }
    
    @Test
    void testGetAccountById_Found() throws Exception {
        UUID accountId = UUID.randomUUID();
        when(accountService.getAccountById(accountId)).thenReturn(Optional.of(account));
        
        mockMvc.perform(get("/api/accounts/{id}", accountId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accountNumber").value("ACC-123456"));
    }
    
    @Test
    void testGetAccountById_NotFound() throws Exception {
        UUID accountId = UUID.randomUUID();
        when(accountService.getAccountById(accountId)).thenReturn(Optional.empty());
        
        mockMvc.perform(get("/api/accounts/{id}", accountId))
                .andExpect(status().isNotFound());
    }
    
    @Test
    void testGetAllAccounts() throws Exception {
        when(accountService.getAllAccounts()).thenReturn(Arrays.asList(account));
        
        mockMvc.perform(get("/api/accounts"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].accountNumber").value("ACC-123456"));
    }
}
package com.assessment.dao;

import com.assessment.entity.Account;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.cassandra.core.CassandraTemplate;
import org.springframework.data.cassandra.core.query.Criteria;
import org.springframework.data.cassandra.core.query.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public class AccountDao {
    
    @Autowired
    private CassandraTemplate cassandraTemplate;
    
    public Account save(Account account) {
        return cassandraTemplate.insert(account);
    }
    
    public Optional<Account> findById(UUID id) {
        Account account = cassandraTemplate.selectOneById(id, Account.class);
        return Optional.ofNullable(account);
    }
    
    public List<Account> findAll() {
        return cassandraTemplate.select(Query.empty(), Account.class);
    }
    
    public Optional<Account> findByAccountNumber(String accountNumber) {
        Query query = Query.query(Criteria.where("account_number").is(accountNumber));
        Account account = cassandraTemplate.selectOne(query, Account.class);
        return Optional.ofNullable(account);
    }
    
    public List<Account> findByAccountType(String accountType) {
        Query query = Query.query(Criteria.where("account_type").is(accountType));
        return cassandraTemplate.select(query, Account.class);
    }
    
    public Account update(Account account) {
        return cassandraTemplate.update(account);
    }
    
    public void delete(Account account) {
        cassandraTemplate.delete(account);
    }
    
    public void deleteById(UUID id) {
        cassandraTemplate.deleteById(id, Account.class);
    }
}
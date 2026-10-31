-- ============================================================================
-- BUS RESERVATION & MANAGEMENT SYSTEM (BRMS)
-- Script 01: Database Creation and Character Set Configuration
-- Target Database: MySQL 8.x
-- Storage Engine: InnoDB
-- ============================================================================

DROP DATABASE IF EXISTS brms_db;
CREATE DATABASE brms_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE brms_db;

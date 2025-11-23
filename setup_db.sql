-- Run this in PostgreSQL to create user and database
-- Open psql as superuser and run: \i setup_db.sql

-- Create user
CREATE USER fileflow WITH PASSWORD 'fileflow123';

-- Create database
CREATE DATABASE fileflow OWNER fileflow;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE fileflow TO fileflow;

-- Connect to database
\c fileflow

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO fileflow;

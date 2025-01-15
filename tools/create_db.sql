-- Create the database
CREATE DATABASE attendees_db;
USE attendees_db;

-- Create departments table
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT
);

-- Create people table
CREATE TABLE people (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    department_id INT,
    linkedin VARCHAR(255),
    social_links JSON,
    year_graduated INT,
    description TEXT,
    photo_url VARCHAR(255),
    FOREIGN KEY (department_id) REFERENCES departments(id)
);
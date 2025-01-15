require('dotenv').config();
const express = require('express');
const mysql = require('mysql2/promise');
const path = require('path');
const crypto = require('crypto');

const app = express();
const PORT = process.env.PORT || 3000;

// Database connection configuration
const dbConfig = {
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    port: process.env.DB_PORT
};

// Middleware to parse JSON and serve static files
app.use(express.json());
app.use(express.static(path.join(__dirname)));

// Admin authentication middleware
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'default_admin_password';

function authenticateAdmin(req, res, next) {
    const providedPassword = req.headers['x-admin-password'];
    
    if (!providedPassword || providedPassword !== ADMIN_PASSWORD) {
        return res.status(401).json({ error: 'Unauthorized: Admin access required' });
    }
    
    next();
}

// API endpoint to fetch attendees
app.get('/api/attendees', async (req, res) => {
    try {
        const connection = await mysql.createConnection(dbConfig);

        const [rows] = await connection.execute(`
            SELECT 
                p.id, 
                p.full_name AS fullName, 
                p.company, 
                d.name AS department, 
                p.linkedin, 
                p.social_links AS socialLinks, 
                p.year_graduated AS yearGraduated, 
                p.description, 
                p.photo_url AS photo
            FROM people p
            JOIN departments d ON p.department_id = d.id
        `);

        await connection.end();
        res.json({ attendees: rows });
    } catch (error) {
        console.error('Error fetching attendees:', error);
        res.status(500).json({ error: 'Failed to fetch attendees' });
    }
});

// API endpoint to add a new attendee (admin-only)
app.post('/api/attendees', authenticateAdmin, async (req, res) => {
    const { 
        fullName, 
        company, 
        department, 
        linkedin, 
        socialLinks, 
        yearGraduated, 
        description, 
        photo 
    } = req.body;

    try {
        const connection = await mysql.createConnection(dbConfig);

        // First, ensure the department exists
        const [departmentRows] = await connection.execute(
            'INSERT IGNORE INTO departments (name) VALUES (?)', 
            [department]
        );

        // Get the department ID
        const [departmentResult] = await connection.execute(
            'SELECT id FROM departments WHERE name = ?', 
            [department]
        );
        const departmentId = departmentResult[0].id;

        // Insert the new attendee
        const [result] = await connection.execute(
            `INSERT INTO people 
            (full_name, company, department_id, linkedin, social_links, year_graduated, description, photo_url) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
            [
                fullName, 
                company, 
                departmentId, 
                linkedin, 
                JSON.stringify(socialLinks), 
                yearGraduated, 
                description, 
                photo
            ]
        );

        await connection.end();

        res.status(201).json({ 
            message: 'Attendee added successfully', 
            id: result.insertId 
        });
    } catch (error) {
        console.error('Error adding attendee:', error);
        res.status(500).json({ error: 'Failed to add attendee' });
    }
});

// API endpoint to fetch departments
app.get('/api/departments', async (req, res) => {
    try {
        const connection = await mysql.createConnection(dbConfig);

        const [rows] = await connection.execute(
            'SELECT DISTINCT name FROM departments ORDER BY name'
        );

        await connection.end();

        res.json({ departments: rows.map(row => row.name) });
    } catch (error) {
        console.error('Error fetching departments:', error);
        res.status(500).json({ error: 'Failed to fetch departments' });
    }
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
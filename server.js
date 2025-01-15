require('dotenv').config();
const express = require('express');
const mysql = require('mysql2/promise');
const path = require('path');
const crypto = require('crypto');
const jwt = require('jsonwebtoken');

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
const JWT_SECRET = process.env.JWT_SECRET || crypto.randomBytes(64).toString('hex');

function generateAdminToken() {
    return jwt.sign({ role: 'admin' }, JWT_SECRET, { expiresIn: '2h' });
}

function authenticateAdmin(req, res, next) {
    const token = req.headers['x-admin-token'];
    
    if (!token) {
        return res.status(401).json({ error: 'No token provided' });
    }

    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        if (decoded.role !== 'admin') {
            return res.status(403).json({ error: 'Insufficient permissions' });
        }
        next();
    } catch (error) {
        return res.status(401).json({ error: 'Invalid or expired token' });
    }
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

// API endpoint to update an attendee (admin-only)
app.put('/api/attendees/:id', authenticateAdmin, async (req, res) => {
    const { id } = req.params;
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

        // Update the attendee
        const [result] = await connection.execute(
            `UPDATE people 
            SET full_name = ?, company = ?, department_id = ?, 
                linkedin = ?, social_links = ?, year_graduated = ?, 
                description = ?, photo_url = ? 
            WHERE id = ?`,
            [
                fullName, 
                company, 
                departmentId, 
                linkedin, 
                JSON.stringify(socialLinks), 
                yearGraduated, 
                description, 
                photo,
                id
            ]
        );

        await connection.end();

        res.json({ 
            message: 'Attendee updated successfully', 
            affectedRows: result.affectedRows 
        });
    } catch (error) {
        console.error('Error updating attendee:', error);
        res.status(500).json({ error: 'Failed to update attendee' });
    }
});

// API endpoint to delete an attendee (admin-only)
app.delete('/api/attendees/:id', authenticateAdmin, async (req, res) => {
    const { id } = req.params;

    try {
        const connection = await mysql.createConnection(dbConfig);

        const [result] = await connection.execute(
            'DELETE FROM people WHERE id = ?', 
            [id]
        );

        await connection.end();

        res.json({ 
            message: 'Attendee deleted successfully', 
            affectedRows: result.affectedRows 
        });
    } catch (error) {
        console.error('Error deleting attendee:', error);
        res.status(500).json({ error: 'Failed to delete attendee' });
    }
});

// API endpoint to get a single attendee by ID
app.get('/api/attendees/:id', authenticateAdmin, async (req, res) => {
    const { id } = req.params;

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
            WHERE p.id = ?
        `, [id]);

        await connection.end();

        if (rows.length === 0) {
            return res.status(404).json({ error: 'Attendee not found' });
        }

        // Parse social links if it's a string
        const attendee = rows[0];
        attendee.socialLinks = typeof attendee.socialLinks === 'string' 
            ? JSON.parse(attendee.socialLinks) 
            : attendee.socialLinks;

        res.json(attendee);
    } catch (error) {
        console.error('Error fetching attendee:', error);
        res.status(500).json({ error: 'Failed to fetch attendee' });
    }
});

// API endpoint to fetch departments
app.get('/api/departments', async (req, res) => {
    try {
        const connection = await mysql.createConnection(dbConfig);

        const [rows] = await connection.execute(
            'SELECT id, name FROM departments ORDER BY name'
        );

        await connection.end();

        res.json({ 
            departments: rows.map(row => ({
                id: row.id,
                name: row.name
            }))
        });
    } catch (error) {
        console.error('Error fetching departments:', error);
        res.status(500).json({ error: 'Failed to fetch departments' });
    }
});

// API endpoint to get a single department by ID
app.get('/api/departments/:id', authenticateAdmin, async (req, res) => {
    const { id } = req.params;

    try {
        const connection = await mysql.createConnection(dbConfig);

        const [rows] = await connection.execute(
            'SELECT id, name FROM departments WHERE id = ?',
            [id]
        );

        await connection.end();

        if (rows.length === 0) {
            return res.status(404).json({ error: 'Department not found' });
        }

        res.json({
            id: rows[0].id,
            name: rows[0].name
        });
    } catch (error) {
        console.error('Error fetching department:', error);
        res.status(500).json({ error: 'Failed to fetch department' });
    }
});

// API endpoint to add a new department (admin-only)
app.post('/api/departments', authenticateAdmin, async (req, res) => {
    const { name } = req.body;

    try {
        const connection = await mysql.createConnection(dbConfig);

        const [result] = await connection.execute(
            'INSERT INTO departments (name) VALUES (?)', 
            [name]
        );

        await connection.end();

        res.status(201).json({ 
            message: 'Department added successfully', 
            id: result.insertId 
        });
    } catch (error) {
        console.error('Error adding department:', error);
        res.status(500).json({ error: 'Failed to add department' });
    }
});

// API endpoint to update a department (admin-only)
app.put('/api/departments/:id', authenticateAdmin, async (req, res) => {
    const { id } = req.params;
    const { name } = req.body;

    try {
        const connection = await mysql.createConnection(dbConfig);

        const [result] = await connection.execute(
            'UPDATE departments SET name = ? WHERE id = ?', 
            [name, id]
        );

        await connection.end();

        res.json({ 
            message: 'Department updated successfully', 
            affectedRows: result.affectedRows 
        });
    } catch (error) {
        console.error('Error updating department:', error);
        res.status(500).json({ error: 'Failed to update department' });
    }
});

// API endpoint to delete a department (admin-only)
app.delete('/api/departments/:id', authenticateAdmin, async (req, res) => {
    const { id } = req.params;

    try {
        const connection = await mysql.createConnection(dbConfig);

        // First, check if the department is empty
        const [peopleCount] = await connection.execute(
            'SELECT COUNT(*) as count FROM people WHERE department_id = ?', 
            [id]
        );

        if (peopleCount[0].count > 0) {
            await connection.end();
            return res.status(400).json({ 
                error: 'Cannot delete department with existing attendees' 
            });
        }

        // If no attendees, proceed with deletion
        const [result] = await connection.execute(
            'DELETE FROM departments WHERE id = ?', 
            [id]
        );

        await connection.end();

        res.json({ 
            message: 'Department deleted successfully', 
            affectedRows: result.affectedRows 
        });
    } catch (error) {
        console.error('Error deleting department:', error);
        res.status(500).json({ error: 'Failed to delete department' });
    }
});

// API endpoint to login
app.post('/api/login', (req, res) => {
    const { password } = req.body;
    
    // Use environment variable for admin password
    const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'default_admin_password';
    
    if (password === ADMIN_PASSWORD) {
        const token = generateAdminToken();
        res.json({ token });
    } else {
        res.status(401).json({ error: 'Invalid admin password' });
    }
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
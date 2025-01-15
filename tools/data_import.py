import json
import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MySQL connection configuration
config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# Read attendees JSON
with open('../data/attendees.json', 'r') as f:
    data = json.load(f)

# Connect to MySQL
conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# Track unique departments
department_ids = {}

# Import departments first
for attendee in data['attendees']:
    dept_name = attendee['department']
    if dept_name not in department_ids:
        cursor.execute(
            "INSERT INTO departments (name) VALUES (%s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)", 
            (dept_name,)
        )
        department_ids[dept_name] = cursor.lastrowid

# Import people
for attendee in data['attendees']:
    cursor.execute("""
        INSERT INTO people 
        (full_name, company, department_id, linkedin, social_links, year_graduated, description, photo_url) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        attendee['fullName'], 
        attendee['company'], 
        department_ids[attendee['department']], 
        attendee['linkedin'], 
        json.dumps(attendee['socialLinks']), 
        attendee['yearGraduated'], 
        attendee['description'], 
        attendee['photo']
    ))

# Commit changes and close connection
conn.commit()
cursor.close()
conn.close()
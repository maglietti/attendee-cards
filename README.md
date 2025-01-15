# Event Attendees Page

## Overview
This is a mockup for an event attendees page designed to be integrated with a Drupal site. The page displays attendee information in a responsive grid layout with the ability to add new attendees.

## Features
- Responsive grid layout for attendee cards
- Modal form for adding new attendees
- Dynamic rendering of attendee information
- Fallback for missing photos
- Social media link integration

## Technical Considerations for Drupal Integration
- Vanilla JavaScript used for maximum compatibility
- CSS variables for easy theming
- Modular file structure
- Minimal external dependencies

## MySQL Setup and Configuration

### Prerequisites
- Docker
- Docker Compose
- Python 3.8+
- Node.js 14+

### Database Setup with Docker

1. **Start MySQL Container**
   ```bash
   cd tools
   docker-compose up -d
   ```

2. **Verify Container is Running**
   ```bash
   docker ps
   ```

3. **Install Python Dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install mysql-connector-python python-dotenv
   ```

4. **Install Node.js Dependencies**
   ```bash
   npm install
   ```

### Database Import

1. **Import Initial Data**
   ```bash
   python tools/data_import.py
   ```

### Environment Configuration

1. Copy `.env.example` to `.env`
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your database credentials:
   ```
   DB_HOST=localhost
   DB_USER=attendee_app
   DB_PASSWORD=app_password
   DB_NAME=attendees_db
   DB_PORT=3306
   ```

### Stopping the Database

```bash
cd tools
docker-compose down
```

### Persistent Data

The MySQL data is stored in a Docker volume `mysql-data`. This ensures your data persists between container restarts.

### Troubleshooting

- Ensure Docker is running
- Check container logs: `docker logs attendees-mysql`
- Verify network ports are not blocked

## Development

### Running the Application

1. **Start the MySQL Database**
   ```bash
   cd tools
   docker-compose up -d
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Start the Development Server**
   ```bash
   npm run dev
   ```
   - This will start the server using Nodemon, which automatically restarts when files change
   - The application will be available at `http://localhost:3000`

4. **Production Deployment**
   ```bash
   npm start
   ```

### Server Configuration

The server uses environment variables defined in `.env`:
- `PORT`: Server port (defaults to 3000)
- `DB_HOST`: MySQL database host
- `DB_USER`: MySQL database username
- `DB_PASSWORD`: MySQL database password
- `DB_NAME`: MySQL database name
- `DB_PORT`: MySQL database port

### Troubleshooting

- Ensure MySQL container is running
- Check server logs for any connection or startup errors
- Verify `.env` file contains correct database credentials
- Confirm all dependencies are installed correctly


## Admin Access

### Adding New Attendees (Admin Function)

To add a new attendee, send a POST request to `/api/attendees` with the following requirements:

1. Include the admin password in the `x-admin-password` header
2. Provide attendee details in the request body:
   ```json
   {
     "fullName": "John Doe",
     "company": "Tech Company",
     "department": "Computer Science (CS)",
     "linkedin": "https://linkedin.com/in/johndoe",
     "socialLinks": [
       "https://twitter.com/johndoe",
       "https://github.com/johndoe"
     ],
     "yearGraduated": 2022,
     "description": "Software engineer passionate about innovation",
     "photo": "https://example.com/photo.jpg"
   }

For example:
``` bash
curl -X POST http://localhost:3000/api/attendees \
     -H "Content-Type: application/json" \
     -H "x-admin-password: your_admin_password" \
     -d '{
         "fullName": "New Attendee",
         "company": "New Company",
         "department": "Computer Science (CS)",
         "linkedin": "https://linkedin.com/in/newattendee",
         "socialLinks": ["https://twitter.com/newattendee"],
         "yearGraduated": 2023,
         "description": "Passionate about technology",
         "photo": "https://example.com/newattendee.jpg"
     }'
```

### Adding New Attendees

The "Add Attendee" button is hidden by default for security reasons. To access the button and add new attendees, append the `admin` query parameter to the URL:

```
http://localhost:3000/?admin=true
```

#### Example URLs
- Local development: `http://localhost:3000/?admin=true`
- Deployed site: `https://yoursite.com/attendees?admin=true`

**Note:** Only use the admin parameter in secure, controlled environments. Do not share admin URLs publicly.

## Future Improvements
- Backend integration for persistent data storage
- Server-side rendering
- Enhanced form validation
- LinkedIn profile photo API integration

## Dependencies
- No external libraries required
- Recommended to add Font Awesome for social media icons in production

## Browser Compatibility
Tested on modern browsers (Chrome, Firefox, Safari, Edge)

## Drupal Integration Notes
- Replace `fetch()` with Drupal's AJAX methods
- Use Drupal's form API for attendee submission
- Adapt CSS to match Drupal theme

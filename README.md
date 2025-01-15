# Attendee Cards Application

## Overview
Attendee Cards is a dynamic web application designed to showcase and manage professional profiles for graduates, students, or team members. The application provides an interactive platform to display attendee information with a clean, modern interface.

## Features

### User-Facing Features
- **Interactive Attendee Grid**: Browse through professional profiles
- **Responsive Design**: Fully responsive layout for desktop and mobile devices
- **Pagination**: Easily navigate through multiple attendee profiles
- **Social Media Integration**: Display links to various social platforms
- **Department and Graduation Year Display**

### Admin Dashboard Features
- **Secure Admin Authentication**: JWT-based login system
- **Attendee Management**:
  - Add new attendees
  - Edit existing attendee profiles
  - Delete attendee records
- **Department Management**:
  - Add, edit, and delete departments
  - Manage department associations for attendees

## Technology Stack
- **Frontend**: 
  - HTML5
  - CSS3
  - Vanilla JavaScript
- **Backend**: 
  - Node.js
  - Express.js
- **Database**: 
  - MySQL
- **Authentication**: 
  - JSON Web Tokens (JWT)

## Prerequisites
- Node.js (v14 or later)
- MySQL
- npm (Node Package Manager)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/attendee-cards.git
cd attendee-cards
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Configure Environment Variables
Create a `.env` file in the project root with the following variables:
```
# MySQL Database Configuration
DB_HOST=localhost
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=attendees_db
DB_PORT=3306

# Admin Configuration
ADMIN_PASSWORD=your_secure_admin_password
JWT_SECRET=a_very_long_random_string_for_jwt_signing
```

### 4. Set Up Database
Ensure MySQL is running and create the necessary database and tables. Refer to the database schema in your project documentation.

### 5. Start the Application
```bash
npm start
```

## Usage

### Accessing the Application
- **Main Page**: View attendee profiles
- **Admin Dashboard**: 
  - URL: `/admin.html`
  - Login with the admin password configured in `.env`

### Admin Dashboard Capabilities
- Add, edit, and remove attendees
- Manage departments
- Update profile information
- Handle social media links

## Social Media Link Support
The application supports the following social media platforms:
- LinkedIn
- GitHub
- X (formerly Twitter)
- Instagram
- Facebook
- Medium

## Customization
- Modify `styles.css` to change the application's look and feel
- Update environment variables for database and authentication settings

## Security Considerations
- Admin access is protected by JWT authentication
- Passwords are securely managed
- Sensitive information is not exposed in client-side code

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License
Distributed under the MIT License. See `LICENSE` for more information.

## Contact
Your Name - maglietti@me.com

Project Link: [https://github.com/your-username/attendee-cards](https://github.com/your-username/attendee-cards)

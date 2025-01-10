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

## Setup
1. Ensure you have a local web server (e.g., Python's `http.server` or PHP's built-in server)
2. Clone the repository
3. Run a local server in this directory
4. Open `index.html` in a browser

## Admin Access

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

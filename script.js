document.addEventListener('DOMContentLoaded', () => {
    const attendeesGrid = document.getElementById('attendees-grid');
    const addAttendeeBtn = document.getElementById('add-attendee-btn');
    const attendeeFormModal = document.getElementById('attendee-form-modal');
    const closeModalBtn = document.querySelector('.close');
    const attendeeForm = document.getElementById('attendee-form');

    // Check for admin query parameter
    function checkAdminAccess() {
        const urlParams = new URLSearchParams(window.location.search);
        const isAdmin = urlParams.get('admin') === 'true';
        
        // Hide or show add attendee button based on admin status
        if (addAttendeeBtn) {
            addAttendeeBtn.style.display = isAdmin ? 'block' : 'none';
        }
    }

    // Pagination variables
    let currentPage = 1;
    const attendeesPerPage = 12;
    let allAttendees = [];

    // Fetch and render attendees
    async function fetchAttendees() {
        try {
            const response = await fetch('attendees.json');
            const data = await response.json();
            // Shuffle the attendees array
            allAttendees = shuffleArray(data.attendees);
            
            // Initial render of first page
            renderAttendeesPage(currentPage);
            
            // Create pagination controls
            createPaginationControls();
        } catch (error) {
            console.error('Error fetching attendees:', error);
        }
    }

    // Fisher-Yates (Knuth) shuffle algorithm
    function shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }

    // Render specific page of attendees
    function renderAttendeesPage(page) {
        attendeesGrid.innerHTML = ''; // Clear existing cards
        
        // Calculate start and end indices for the current page
        const startIndex = (page - 1) * attendeesPerPage;
        const endIndex = startIndex + attendeesPerPage;
        
        // Get attendees for current page
        const pageAttendees = allAttendees.slice(startIndex, endIndex);
        
        // Render attendees
        pageAttendees.forEach(attendee => {
            const card = createAttendeeCard(attendee);
            attendeesGrid.appendChild(card);
        });
    }

    // Create pagination controls
    function createPaginationControls() {
        // Calculate total pages
        const totalPages = Math.ceil(allAttendees.length / attendeesPerPage);
        
        // Create pagination container
        const paginationContainer = document.createElement('div');
        paginationContainer.id = 'pagination-controls';
        paginationContainer.classList.add('pagination');
        
        // Previous button
        const prevButton = document.createElement('button');
        prevButton.textContent = 'Previous';
        prevButton.addEventListener('click', goToPreviousPage);
        
        // Next button
        const nextButton = document.createElement('button');
        nextButton.textContent = 'Next';
        nextButton.addEventListener('click', goToNextPage);
        
        // Page number display
        const pageDisplay = document.createElement('span');
        pageDisplay.id = 'page-display';
        
        // Add elements to container
        paginationContainer.appendChild(prevButton);
        paginationContainer.appendChild(pageDisplay);
        paginationContainer.appendChild(nextButton);
        
        // Add to document
        const gridContainer = document.querySelector('.container');
        gridContainer.appendChild(paginationContainer);
        
        // Initial update of pagination buttons
        updatePaginationButtons();
    }

    // Update pagination button states and page display
    function updatePaginationButtons() {
        const totalPages = Math.ceil(allAttendees.length / attendeesPerPage);
        const prevButton = document.querySelector('.pagination button:first-child');
        const nextButton = document.querySelector('.pagination button:last-child');
        const pageDisplay = document.getElementById('page-display');
        
        // Update page display
        pageDisplay.textContent = `Page ${currentPage} of ${totalPages}`;
        
        // Disable/enable buttons based on current page
        prevButton.disabled = (currentPage === 1);
        nextButton.disabled = (currentPage === totalPages);
        
        // Scroll to top of the page
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }

    // Previous page handler
    function goToPreviousPage() {
        if (currentPage > 1) {
            currentPage--;
            renderAttendeesPage(currentPage);
            updatePaginationButtons();
        }
    }

    // Next page handler
    function goToNextPage() {
        const totalPages = Math.ceil(allAttendees.length / attendeesPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            renderAttendeesPage(currentPage);
            updatePaginationButtons();
        }
    }

    // Create attendee card
    function createAttendeeCard(attendee) {
        const card = document.createElement('div');
        card.classList.add('attendee-card');

        // Use provided photo or fallback to a default
        const photoUrl = attendee.photo || 'https://via.placeholder.com/300x300';

        // Create social links HTML with icons
        const socialLinksHtml = attendee.socialLinks 
            ? attendee.socialLinks.map(link => 
                `<a href="${link}" target="_blank" rel="noopener noreferrer" title="${new URL(link).hostname}">
                    <i class="${getSocialPlatform(link)}"></i>
                </a>`
            ).join('') 
            : '';

        // Update graduation year display to include department
        const departmentDisplay = `
            <p id="graduation-year">
                <strong> ${attendee.yearGraduated} </strong> <br> 
                ${attendee.department || 'Department Not Specified'}
            </p>`;

        card.innerHTML = `
            <img src="${photoUrl}" alt="${attendee.fullName}" onerror="this.src='https://via.placeholder.com/300x300'">
            <div class="attendee-card-content">
                <h2>${attendee.fullName}</h2>
                <h3>${attendee.company ? `${attendee.company}` : ''}</h3>
                ${departmentDisplay}
                <p id="attendee-description">${attendee.description}</p>
                <div class="social-links">
                    ${attendee.linkedin ? `<a href="${attendee.linkedin}" target="_blank" rel="noopener noreferrer" title="LinkedIn">
                        <i class="fab fa-linkedin-in"></i>
                    </a>` : ''}
                    ${socialLinksHtml}
                </div>
            </div>
        `;

        return card;
    }

    // Determine social platform from URL and return icon class
    function getSocialPlatform(url) {
        if (url.includes('twitter.com')) return 'fab fa-twitter';
        if (url.includes('github.com')) return 'fab fa-github';
        if (url.includes('linkedin.com')) return 'fab fa-linkedin-in';
        if (url.includes('instagram.com')) return 'fab fa-instagram';
        if (url.includes('facebook.com')) return 'fab fa-facebook-f';
        if (url.includes('medium.com')) return 'fab fa-medium';
        return 'fas fa-link';
    }

    // Modal functionality
    addAttendeeBtn.addEventListener('click', () => {
        attendeeFormModal.style.display = 'block';
    });

    closeModalBtn.addEventListener('click', () => {
        attendeeFormModal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target === attendeeFormModal) {
            attendeeFormModal.style.display = 'none';
        }
    });

    // Form submission (for mockup, just logs data)
    attendeeForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(attendeeForm);
        const newAttendee = {
            fullName: formData.get('fullName'),
            company: formData.get('company'),
            linkedin: formData.get('linkedin'),
            socialLinks: formData.get('socialLinks') ? formData.get('socialLinks').split(',') : [],
            yearGraduated: parseInt(formData.get('yearGraduated')),
            description: formData.get('description'),
            photo: formData.get('photo') ? URL.createObjectURL(formData.get('photo')) : null
        };

        // In a real app, you'd send this to a backend
        console.log('New Attendee:', newAttendee);
        attendeeFormModal.style.display = 'none';
        attendeeForm.reset();
    });

    // Initial fetch
    fetchAttendees();

    // Check for admin access
    checkAdminAccess();
});

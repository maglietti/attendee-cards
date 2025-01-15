document.addEventListener('DOMContentLoaded', () => {
    // DOM Element Selections
    const loginModal = document.getElementById('loginModal');
    const loginForm = document.getElementById('loginForm');
    const adminPassword = document.getElementById('adminPassword');
    const adminContent = document.getElementById('adminContent');

    const attendeeModal = document.getElementById('attendeeModal');
    const attendeeForm = document.getElementById('attendeeForm');
    const addAttendeeBtn = document.getElementById('addAttendeeBtn');
    const closeAttendeeModal = document.getElementById('closeAttendeeModal');
    const cancelAttendeeBtn = document.getElementById('cancelAttendeeBtn');

    const departmentModal = document.getElementById('departmentModal');
    const departmentForm = document.getElementById('departmentForm');
    const addDepartmentBtn = document.getElementById('addDepartmentBtn');
    const closeDepartmentModal = document.getElementById('closeDepartmentModal');
    const cancelDepartmentBtn = document.getElementById('cancelDepartmentBtn');

    const attendeesTableBody = document.getElementById('attendeesTableBody');
    const departmentsTableBody = document.getElementById('departmentsTableBody');
    const departmentSelect = document.getElementById('department');

    let adminToken = null;
    let currentAttendeeId = null;
    let currentDepartmentId = null;

    // Authentication
    function showLoginModal() {
        loginModal.style.display = 'flex';
        adminContent.style.display = 'none';
        adminToken = null;
        localStorage.removeItem('adminToken');
    }

    function hideLoginModal() {
        loginModal.style.display = 'none';
        adminContent.style.display = 'block';
    }

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ password: adminPassword.value })
            });

            if (response.ok) {
                const data = await response.json();
                adminToken = data.token;
                localStorage.setItem('adminToken', adminToken);
                hideLoginModal();
                loadInitialData();
            } else {
                alert('Invalid admin password');
                adminPassword.value = ''; // Clear password field
                adminToken = null;
                localStorage.removeItem('adminToken');
            }
        } catch (error) {
            console.error('Login error:', error);
            alert('Login failed');
            adminPassword.value = ''; // Clear password field
            adminToken = null;
            localStorage.removeItem('adminToken');
        }
    });

    // Check authentication on page load
    function checkAuthentication() {
        // Always show login modal initially
        showLoginModal();
    }

    // Data Fetching
    async function loadInitialData() {
        try {
            await Promise.all([
                fetchAttendees(),
                fetchDepartments()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            showLoginModal();
        }
    }

    async function fetchAttendees() {
        try {
            const response = await fetch('/api/attendees', {
                headers: {
                    'X-Admin-Token': adminToken
                }
            });
            const data = await response.json();
            renderAttendees(data.attendees);
        } catch (error) {
            console.error('Error fetching attendees:', error);
        }
    }

    async function fetchDepartments() {
        try {
            const response = await fetch('/api/departments', {
                headers: {
                    'X-Admin-Token': adminToken
                }
            });
            const data = await response.json();
            renderDepartments(data.departments);
            populateDepartmentSelect(data.departments);
        } catch (error) {
            console.error('Error fetching departments:', error);
        }
    }

    // Rendering Functions
    function renderAttendees(attendees) {
        attendeesTableBody.innerHTML = '';
        attendees.forEach(attendee => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${attendee.fullName}</td>
                <td>${attendee.department}</td>
                <td>${attendee.company || 'N/A'}</td>
                <td>
                    <button onclick="editAttendee(${attendee.id})">Edit</button>
                    <button onclick="deleteAttendee(${attendee.id})">Delete</button>
                </td>
            `;
            attendeesTableBody.appendChild(row);
        });
    }

    function renderDepartments(departments) {
        departmentsTableBody.innerHTML = '';
        departments.forEach(dept => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${dept.name || 'Unknown Department'}</td>
                <td>
                    <button onclick="editDepartment(${dept.id})">Edit</button>
                    <button onclick="deleteDepartment(${dept.id})">Delete</button>
                </td>
            `;
            departmentsTableBody.appendChild(row);
        });
    }

    function populateDepartmentSelect(departments) {
        departmentSelect.innerHTML = '';
        departments.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept.name;
            option.textContent = dept.name;
            departmentSelect.appendChild(option);
        });
    }

    // Attendee Modal Handlers
    addAttendeeBtn.addEventListener('click', () => {
        document.getElementById('attendeeModalTitle').textContent = 'Add New Attendee';
        attendeeForm.reset();
        currentAttendeeId = null;
        attendeeModal.style.display = 'flex';
    });

    closeAttendeeModal.addEventListener('click', () => {
        attendeeModal.style.display = 'none';
    });

    cancelAttendeeBtn.addEventListener('click', () => {
        attendeeModal.style.display = 'none';
    });

    attendeeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Check if admin token exists
        if (!adminToken) {
            alert('Please log in first');
            showLoginModal();
            return;
        }

        const formData = {
            fullName: document.getElementById('fullName').value,
            company: document.getElementById('company').value,
            department: document.getElementById('department').value,
            linkedin: document.getElementById('linkedin').value,
            socialLinks: document.getElementById('socialLinks').value.split(',').map(link => link.trim()),
            yearGraduated: document.getElementById('yearGraduated').value,
            description: document.getElementById('description').value,
            photo: document.getElementById('photoUrl').value
        };

        try {
            const url = currentAttendeeId 
                ? `/api/attendees/${currentAttendeeId}` 
                : '/api/attendees';
            const method = currentAttendeeId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Token': adminToken
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                await fetchAttendees();
                attendeeModal.style.display = 'none';
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.error || 'Failed to save attendee'}`);
            }
        } catch (error) {
            console.error('Error saving attendee:', error);
            alert('Failed to save attendee. Please check your connection and try again.');
        }
    });

    // Department Modal Handlers
    addDepartmentBtn.addEventListener('click', () => {
        document.getElementById('departmentModalTitle').textContent = 'Add New Department';
        departmentForm.reset();
        currentDepartmentId = null;
        departmentModal.style.display = 'flex';
    });

    closeDepartmentModal.addEventListener('click', () => {
        departmentModal.style.display = 'none';
    });

    cancelDepartmentBtn.addEventListener('click', () => {
        departmentModal.style.display = 'none';
    });

    departmentForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const departmentId = document.getElementById('departmentId').value;
        const departmentName = document.getElementById('departmentName').value;

        try {
            const url = currentDepartmentId 
                ? `/api/departments/${currentDepartmentId}` 
                : '/api/departments';
            const method = currentDepartmentId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Token': adminToken
                },
                body: JSON.stringify({ id: departmentId, name: departmentName })
            });

            if (response.ok) {
                await Promise.all([
                    fetchDepartments(),
                    fetchAttendees()  // Refresh attendees in case department changed
                ]);
                departmentModal.style.display = 'none';
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error saving department:', error);
            alert('Failed to save department');
        }
    });

    // Edit and Delete Functions (global scope for onclick handlers)
    window.editAttendee = async (id) => {
        try {
            const response = await fetch(`/api/attendees/${id}`, {
                headers: {
                    'X-Admin-Token': adminToken
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to fetch attendee');
            }

            const attendee = await response.json();

            document.getElementById('attendeeModalTitle').textContent = 'Edit Attendee';
            document.getElementById('attendeeId').value = id;
            document.getElementById('fullName').value = attendee.fullName;
            document.getElementById('company').value = attendee.company || '';
            document.getElementById('department').value = attendee.department;
            document.getElementById('linkedin').value = attendee.linkedin || '';
            document.getElementById('socialLinks').value = 
                Array.isArray(attendee.socialLinks) 
                    ? attendee.socialLinks.join(', ') 
                    : (attendee.socialLinks || '');
            document.getElementById('yearGraduated').value = attendee.yearGraduated || '';
            document.getElementById('description').value = attendee.description || '';
            document.getElementById('photoUrl').value = attendee.photo || '';

            currentAttendeeId = id;
            attendeeModal.style.display = 'flex';
        } catch (error) {
            console.error('Error fetching attendee details:', error);
            alert(error.message || 'Failed to load attendee details');
        }
    };

    window.deleteAttendee = async (id) => {
        if (!confirm('Are you sure you want to delete this attendee?')) return;

        try {
            const response = await fetch(`/api/attendees/${id}`, {
                method: 'DELETE',
                headers: {
                    'X-Admin-Token': adminToken
                }
            });

            if (response.ok) {
                await fetchAttendees();
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error deleting attendee:', error);
            alert('Failed to delete attendee');
        }
    };

    window.editDepartment = async (id) => {
        try {
            const response = await fetch(`/api/departments/${id}`, {
                headers: {
                    'X-Admin-Token': adminToken
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to fetch department');
            }

            const department = await response.json();

            document.getElementById('departmentModalTitle').textContent = 'Edit Department';
            document.getElementById('departmentId').value = department.id;
            document.getElementById('departmentName').value = department.name;
            currentDepartmentId = department.id;
            departmentModal.style.display = 'flex';
        } catch (error) {
            console.error('Error fetching department details:', error);
            alert(error.message || 'Failed to load department details');
        }
    };

    window.deleteDepartment = async (id) => {
        if (!confirm('Are you sure you want to delete this department?')) return;

        try {
            const response = await fetch(`/api/departments/${id}`, {
                method: 'DELETE',
                headers: {
                    'X-Admin-Token': adminToken
                }
            });

            if (response.ok) {
                await Promise.all([
                    fetchDepartments(),
                    fetchAttendees()
                ]);
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error deleting department:', error);
            alert('Failed to delete department');
        }
    };

    // Initial authentication check
    checkAuthentication();
});
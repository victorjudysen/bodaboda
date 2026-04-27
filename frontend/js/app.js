// BodaConnect Frontend JS
// All page logic is modular and separated by page

// Utility: Show status messages
function showStatusMessage(container, message, type) {
  container.innerHTML = `<div class="status-message status-${type}">${message}</div>`;
}

// Homepage: No JS needed

// Request Ride Page Logic
function setupRequestForm() {
  const form = document.getElementById('request-form');
  const statusDiv = document.getElementById('request-status');

  if (!form) return;

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    // Get form values
    const pickup = form.elements['pickup'].value.trim();
    const destination = form.elements['destination'].value.trim();

    // Validate
    if (!pickup || !destination) {
      showStatusMessage(statusDiv, 'Please fill in both pickup and destination.', 'error');
      return;
    }

    showStatusMessage(statusDiv, 'Requesting ride...', 'loading');

    try {
      const res = await fetch('http://localhost:5000/request-ride', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pickup, destination })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.message || 'Failed to request ride.');
      }
      showStatusMessage(statusDiv, data.message || 'Ride requested successfully!', 'success');
      form.reset();
    } catch (err) {
      showStatusMessage(statusDiv, err.message || 'Network error. Please try again.', 'error');
    }
  });
}

// Dashboard Page Logic
function loadDashboard() {
  const statusDiv = document.getElementById('dashboard-status');
  const riderNameDiv = document.getElementById('rider-name');
  const tripsList = document.getElementById('trips-list');

  if (!statusDiv || !riderNameDiv || !tripsList) return;

  showStatusMessage(statusDiv, 'Loading dashboard...', 'loading');

  fetch('http://localhost:5000/rider-dashboard')
    .then(async res => {
      if (!res.ok) {
        let msg = 'Failed to load dashboard.';
        try {
          const data = await res.json();
          msg = data.message || msg;
        } catch {}
        throw new Error(msg);
      }
      return res.json();
    })
    .then(data => {
      // Validate response
      if (!data || !data.riderName || !Array.isArray(data.trips)) {
        throw new Error('Invalid dashboard data.');
      }
      riderNameDiv.textContent = data.riderName;
      tripsList.innerHTML = '';
      if (data.trips.length === 0) {
        tripsList.innerHTML = '<li>No trips found.</li>';
      } else {
        data.trips.forEach(trip => {
          const li = document.createElement('li');
          li.innerHTML = `<span>${trip.pickup}</span> <span>→</span> <span>${trip.destination}</span>`;
          tripsList.appendChild(li);
        });
      }
      statusDiv.innerHTML = '';
    })
    .catch(err => {
      showStatusMessage(statusDiv, err.message || 'Network error. Please try again.', 'error');
    });
}

// Page router
function init() {
  if (document.body.classList.contains('request-page')) {
    setupRequestForm();
  } else if (document.body.classList.contains('dashboard-page')) {
    loadDashboard();
  }
}

document.addEventListener('DOMContentLoaded', init);

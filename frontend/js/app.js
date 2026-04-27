// BodaConnect - Realistic, Clean, Product UI JS

// Utility: Show status messages
function showStatusMessage(container, message, type) {
  container.innerHTML = `<div class="status-message status-${type}">${message}</div>`;
}

// Request Ride Logic
function handleRequestRide() {
  const form = document.getElementById('request-form');
  const statusDiv = document.getElementById('request-status');
  const submitBtn = document.getElementById('submit-btn');

  if (!form) return;

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    const pickup = form.elements['pickup'].value.trim();
    const destination = form.elements['destination'].value.trim();

    if (!pickup || !destination) {
      showStatusMessage(statusDiv, 'Please enter both pickup and destination.', 'error');
      return;
    }

    showStatusMessage(statusDiv, 'Requesting ride...', 'loading');
    submitBtn.disabled = true;

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
    } finally {
      submitBtn.disabled = false;
    }
  });
}

// Dashboard Logic
function loadDashboard() {
  const statusDiv = document.getElementById('dashboard-status');
  const riderNameDiv = document.getElementById('rider-name');
  const tripsList = document.getElementById('trips-list');

  if (!statusDiv || !riderNameDiv || !tripsList) return;

  showStatusMessage(statusDiv, 'Loading...', 'loading');

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
      if (!data || !data.riderName || !Array.isArray(data.trips)) {
        throw new Error('Invalid dashboard data.');
      }
      riderNameDiv.textContent = data.riderName;
      tripsList.innerHTML = '';
      if (data.trips.length === 0) {
        tripsList.innerHTML = '<li class="muted">No trips assigned.</li>';
      } else {
        data.trips.forEach(trip => {
          const li = document.createElement('li');
          li.innerHTML = `<span>${trip.pickup}</span> <span style="color:#888;">→</span> <span>${trip.destination}</span>`;
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
    handleRequestRide();
  } else if (document.body.classList.contains('dashboard-page')) {
    loadDashboard();
  }
}

document.addEventListener('DOMContentLoaded', init);

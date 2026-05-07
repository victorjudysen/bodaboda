// ── Auth helpers ─────────────────────────────────────────────────────────────

function storeUser(data) {
  localStorage.setItem('boda_user', JSON.stringify(data));
}

function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem('boda_user'));
  } catch {
    return null;
  }
}

function logout() {
  localStorage.removeItem('boda_user');
  window.location.href = '/';
}

/**
 * Redirect to login if no user is stored.
 * Optionally enforce a specific role ('customer' | 'rider').
 */
function requireLogin(role) {
  const user = getStoredUser();
  if (!user) {
    window.location.href = 'login.html';
    return;
  }
  if (role && user.role !== role) {
    // Wrong role — send to correct dashboard
    window.location.href = user.role === 'rider' ? 'rider-dashboard.html' : 'dashboard.html';
  }
}

/** Redirect already-logged-in users away from auth pages. */
function redirectIfLoggedIn() {
  const user = getStoredUser();
  if (user) {
    window.location.href = user.role === 'rider' ? 'rider-dashboard.html' : 'dashboard.html';
  }
}

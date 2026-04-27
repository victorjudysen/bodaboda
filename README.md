# BodaConnect Frontend

A minimal, functional web frontend for the BodaBoda project.

## 📁 Project Structure

```
bodaboda/
├── frontend/
│   ├── index.html
│   ├── request.html
│   ├── dashboard.html
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── app.js
├── backend/
│   └── ... (backend files)
├── README.md
```

## 🚀 How to Run

1. **Ensure the backend is running at `http://localhost:5000`**
   - Start the backend server as per backend instructions.
2. **Open the frontend:**
   - Open `index.html` in your browser directly, or
   - For best results, use a local server (e.g. VS Code Live Server, or `python -m http.server` in this folder).
3. **Navigate the app:**
   - Homepage: Welcome and navigation
   - Request Ride: Fill the form and submit
   - Rider Dashboard: View rider name and trips

## 📝 Features

- **No frameworks:** Pure HTML, CSS, and vanilla JS
- **Responsive, clean UI**
- **API integration:**
  - POST `/request-ride`
  - GET `/rider-dashboard`
- **Error handling and loading states**

## 🛠️ Development

- All JS in `js/app.js`
- All CSS in `css/styles.css`
- Edit HTML files for page content

## 🤝 Contributing

- Make changes in a feature branch, open a PR for review.
- Keep UI minimal and functional.
- No frameworks or unnecessary libraries.

---

For any issues, contact the team lead or open an issue in the repository.

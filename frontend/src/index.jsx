// src/main.jsx

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css"; // Optional: for global styles

// 1. Find the root DOM element from index.html (usually <div id="root"></div>)
const rootElement = document.getElementById("root");

// 2. Create a React root to manage rendering into that DOM element
const root = ReactDOM.createRoot(rootElement);

// 3. Render the main App component into the root
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

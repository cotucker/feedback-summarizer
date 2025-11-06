<div align="center">
  <img src="https://i.imgur.com/your-project-logo-or-screenshot.png" alt="Project Banner" width="800"/>
  <h1>AI Feedback Analysis Dashboard</h1>
  <p>
    An intelligent dashboard to upload, analyze, and visualize customer feedback using large language models.
  </p>
  <p>
    <a href="#-introduction">Introduction</a> •
    <a href="#-key-features">Key Features</a> •
    <a href="#-tech-stack">Tech Stack</a> •
    <a href="#-getting-started">Getting Started</a> •
    <a href="#-usage">Usage</a> •
    <a href="#-api-endpoints">API</a> •
    <a href="#-contributing">Contributing</a>
  </p>

  <!-- Badges -->
  <p>
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
    <img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python Version">
    <img src="https://img.shields.io/badge/react-19.2.0-61DAFB.svg?logo=react" alt="React">
    <img src="https://img.shields.io/badge/fastapi-0.119.0-009688.svg?logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/status-in%20development-orange" alt="Status">
  </p>
</div>

---

## 📖 Introduction

In today's data-driven world, customer feedback is a very valuable and informative resource for any business. However, manually sifting through thousands of reviews, survey responses is inefficient and often impractical. Key insights can be easily missed, and emerging trends can go unnoticed.

This project introduces an **AI-powered dashboard** designed to solve this exact problem. Using Text Clustering with Language Models (LLMs), this application transforms raw, unstructured feedback from a simple CSV file into a rich, interactive dashboard.

It provides product managers, marketing teams, and customer service leaders with insights into customer sentiment, identifies emerging themes, and even helps shape responses, enabling teams to make faster and more informed decisions.

## ✨ Key Features

- **📄 Simple CSV Upload:** Easily upload customer feedback in a CSV format.
- **🧠 Automated Topic Clustering:** Texts are clustered, and each cluster is assigned a name.
- **🎭 Sentiment Analysis:** Determines if feedback is positive, negative, or neutral.
- **🤖 AI-Generated Replies:** Generates context-aware replies to appease customers.
- **📊 Interactive Dashboard:** Visualizes data with interactive charts for topics and sentiment.
- **📝 Exportable Insights:** Download a text summary of all key insights with one click.

## 🚀 Demo

Here's a quick look at the dashboard in action. The user uploads a CSV, and the system automatically generates a complete analysis.

https://github.com/user-attachments/assets/c2446584-f543-4b3b-ba11-6aeb0f245acb


## 🛠️ Tech Stack

This project uses a modern, decoupled architecture with a React frontend and a FastAPI backend.

| Frontend                               | Backend                             |
| -------------------------------------- | ----------------------------------- |
| **React.js**                           | **Python 3.9+**                     |
| **MUI X** (for UI components & Charts) | **FastAPI** (for the REST API)      |
| **Axios** (for API requests)           | **Uvicorn** (as the ASGI server)    |
| **JavaScript**                         | **Pandas** (for data manipulation)  |
|                                        | **Gemini APIs** (for AI processing) |

## 🏁 Getting Started

Follow these instructions to get the project up and running on your local machine.

### Prerequisites

- **Node.js** (v19 or newer)
- **Python** (v3.10 or newer)
- Gemini API key

### ⚙️ Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/feedback-summarizer.git
    cd feedback-summarizer
    ```

2.  **Set up the Backend:**
    - Create a virtual environment and install Python dependencies.

    ```bash
    # Create and activate a virtual environment (recommended)
    python -m venv .venv
    source .venv/bin/activate

    # Install dependencies using uv
    pip install uv
    uv sync
    uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
    ```

3.  **Set up the Frontend:**
    - Navigate to the frontend directory and install Node.js dependencies.

    ```bash
    cd frontend
    npm install
    ```

4.  **Configure Environment Variables:**
    - Create a `.env` file in the root directory of the project.
    - Add your Gemini API key to the file:
    ```env
    GEMINI_API_KEY="your_gemini_api_key_here"
    MODEL="gemini_model_name (e.g. gemini-flash-lite-latest)"
    ```

### 🏃‍♀️ Running the Application

You can run the application in two ways: locally for development or using Docker for a containerized environment.

**Option 1: Running Locally**

This method uses `concurrently` to run both the frontend and backend servers with a single command.

1.  Navigate to the `frontend` directory:

    ```bash
    cd frontend
    ```

2.  Run the `dev` script:

    ```bash
    npm run dev
    ```

    - The frontend will be available at `http://localhost:3000`.
    - The backend server will be running at `http://localhost:8000`.

**Option 2: Running with Docker Compose**

This is the recommended way to run the application in a stable, isolated environment.

1.  Make sure you have Docker and Docker Compose installed.

2.  From the root of the project, run:

    ```bash
    docker-compose up --build
    ```

    - The frontend will be available at `http://localhost:3000`.
    - The backend API will be available at `http://localhost:8000`.

## 🎈 Usage

1.  **Open the Application:** Navigate to `http://localhost:3000` in your web browser.
2.  **Upload a File:** Click the "Upload CSV" button and select a CSV file containing customer feedback. The file should have a column with the feedback text.
3.  **(Optional) Add Topics:** Enter a list of topics you are interested in (e.g., "pricing, support, performance"). This helps the AI focus its analysis.
4.  **Analyze:** Click the "Analyze" button. The application will send the data to the backend for processing.
5.  **View Dashboard:** Once the analysis is complete, the dashboard will populate with:
    - A high-level summary.
    - Sentiment distribution charts.
    - Topic clusters
    - Key topics and their summaries.
    - AI-generated replies to specific feedback points.

## 📡 API Endpoints

The backend exposes a single primary REST API endpoint for feedback analysis.

#### `POST /api/feedback/analyze`

Analyzes a CSV file of customer feedback.

- **Request Type:** `multipart/form-data`
- **Query Parameters:**
  - `topics` (optional, string): A string of topics to guide the analysis.
- **Form Data:**
  - `file` (required, File): The CSV file containing the feedback.
- **Successful Response (`200 OK`):**
  ```json
  {
    "summary": "A high-level summary of all feedback.",
    "sentiment": { "positive": 10, "negative": 5, "neutral": 2 },
    "topics": [
      {
        "topic": "Pricing",
        "count": 5,
        "summary": "Summary of feedback related to pricing."
      }
    ],
    "feedback_analysis": [
      {
        "text": "The app is too expensive.",
        "topic": "Pricing",
        "sentiment": "negative"
      }
    ],
    "feedback_replies": [
      {
        "feedback_text": "The app is too expensive.",
        "feedback_reply": "Thank you for your feedback...",
        "score": 4
      }
    ]
  }
  ```

## 📂 Project Structure

The project is organized into a separate frontend and backend, promoting a clean separation of concerns.

```
feedback-summarizer/
├── .dockerignore         # Files to ignore in the backend Docker image
├── .gitignore            # Files to ignore for Git
├── Dockerfile            # Dockerfile for the Python backend
├── docker-compose.yml    # Docker Compose file to run both services
├── main.py               # FastAPI application entry point
├── pyproject.toml        # Python project metadata and dependencies
├── README.md             # This file
├── models/               # Classes for structured output
│   ├── models.py
├── services/             # Backend business logic
│   ├── analysis_service.py
│   └── ...
├── frontend/
│   ├── .dockerignore     # Files to ignore in the frontend Docker image
│   ├── Dockerfile        # Dockerfile for the React frontend
│   ├── package.json      # Frontend dependencies and scripts
│   ├── public/           # Public assets for the React app
│   └── src/              # React application source code
│       ├── api/          # API client (axios)
│       ├── components/   # React components
│       └── App.jsx       # Main React app component
└── ...
```

## ✅ Running Tests

_(**In Progress**)_

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

<div align="center">
  <small>Inspired by <a href="https://github.com/matiassingers/awesome-readme">awesome-readme</a>.</small>
</div>

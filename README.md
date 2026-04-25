# ScoutAI — Agentic Hybrid-RAG Recruitment Engine

ScoutAI is an advanced, local-first AI recruitment engine designed to automate the screening and ranking of job applicants. It leverages **FastAPI**, **FAISS**, and **Ollama (Mistral)** to perform hybrid search (semantic + keyword), candidate scoring, and engagement simulation, all while keeping data completely local and secure.

## 🌟 Key Features

*   **Job Description Parsing**: Automatically extracts key skills and requirements from unstructured job descriptions using Mistral.
*   **Hybrid-RAG Candidate Retrieval**: Uses FAISS vector search combined with keyword matching to find the most relevant candidates from the database.
*   **Intelligent Scoring**: Evaluates candidates based on skill overlap, experience level, and semantic fit.
*   **Agentic Profiling**: Computes the candidate's "propensity to switch" jobs and generates personalized "engagement messages" for recruiters to use.
*   **Explainable AI**: Provides a transparent, human-readable reason for why each candidate was matched to the role.
*   **Premium Local UI**: A beautiful, dark-mode glassmorphic frontend built with pure HTML/CSS/JS that interacts directly with the local FastAPI backend.
*   **100% Local**: No data leaves your machine. Powered by Ollama and Sentence-Transformers.

## 🛠️ Tech Stack

*   **Backend**: Python, FastAPI
*   **Frontend**: HTML5, Vanilla CSS (Glassmorphism), Vanilla JavaScript
*   **AI/ML**: Ollama (Mistral 7B), `sentence-transformers` (`all-MiniLM-L6-v2`)
*   **Vector Database**: FAISS (CPU)

## 🚀 Getting Started

### Prerequisites

1.  **Python 3.9+** installed.
2.  **Ollama** installed on your machine.
    *   Download from [ollama.com](https://ollama.com).
    *   Pull the Mistral model: `ollama run mistral`

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/scoutai.git
    cd scoutai
    ```

2.  **Set up a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the App

1.  Ensure **Ollama** is running in the background.
2.  Start the **FastAPI** backend:
    ```bash
    uvicorn backend.main:app --reload --port 8000
    ```
3.  Open your browser and navigate to: [http://localhost:8000](http://localhost:8000)

## 📁 Project Structure

```text
scoutai/
├── backend/                  # FastAPI Application
│   ├── modules/              # Core Logic (Parsing, Retrieval, Scoring, etc.)
│   ├── main.py               # API Endpoints
│   ├── config.py             # Configuration and Weights
│   └── llm_client.py         # Ollama API Wrapper
├── frontend/                 # UI Assets
│   ├── index.html
│   ├── style.css
│   └── app.js
├── data/                     # Mock Candidate Database
├── requirements.txt
└── README.md
```

## ⚖️ Hackathon Disclaimer

This tool is built as a proof-of-concept for a hackathon. AI-generated scores and explanations are for screening assistance only. All rankings should be reviewed by a human recruiter before making hiring decisions to prevent bias.

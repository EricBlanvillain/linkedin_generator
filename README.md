# LinkedIn Style Syncer & Post Generator

This project helps users generate LinkedIn posts that match their unique writing style.

## Project Structure

- `backend/`: Contains the Flask backend API.
- `frontend/`: Contains the React frontend application.
- `instructions.md`: The Product Requirements Document.

## Setup

### Backend (Flask)

1.  Navigate to the `backend` directory:
    ```bash
    cd linkedin_project/backend
    ```
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Copy the example environment file and fill in your details:
    ```bash
    cp .env.example .env
    # Edit .env with your MONGO_URI and ANTHROPIC_API_KEY
    ```
5.  Ensure you have a MongoDB instance running and accessible via the `MONGO_URI`.
6.  Run the Flask development server:
    ```bash
    flask run # Or python app.py
    ```
    The backend will run on `http://127.0.0.1:5001` by default.

### Frontend (React + Vite)

1.  Navigate to the `frontend` directory:
    ```bash
    cd linkedin_project/frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm run dev
    ```
    The frontend will be accessible at `http://localhost:5173` (or the next available port).

## Usage

- Access the web application through the frontend URL.
- Follow the on-screen instructions to analyze your LinkedIn post style and generate new posts.

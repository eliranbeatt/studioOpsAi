# GEMINI.md

## Project Overview

This is a full-stack web application with a Next.js frontend and a FastAPI backend. The project is containerized using Docker.

**Frontend:**
- **Framework:** Next.js
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Testing:** Jest, Playwright, React Testing Library

**Backend:**
- **Framework:** FastAPI
- **Language:** Python
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Testing:** Pytest

**Other Key Technologies:**
- Docker
- `trello-mcp`
- `gateway`

## Building and Running

### Prerequisites

- Docker
- Node.js
- Python

### Development Environment

The development environment is managed with Docker Compose.

- **Start all services:** `make dev-up`
- **Stop all services:** `make dev-down`
- **View logs:** `make logs`
- **Check service health:** `make health`

### Running the Application

You can run the application using the provided scripts:

- **Windows (Command Prompt):** `run_dev.bat`
- **Windows (PowerShell):** `./run_dev.ps1`
- **Linux/Mac:** `chmod +x run_dev.sh && ./run_dev.sh`

This will start:
- Web app on http://localhost:3000
- API server on http://localhost:8001
- API documentation on http://localhost:8001/docs

### Manual Startup

- **Web app:** `make web`
- **API server:** `make api`

### Database

- **Run migrations:** `make db-migrate`
- **Seed the database:** `make db-seed`

## Development Conventions

### Frontend

- **Package Manager:** `npm` is used for dependency management.
- **Scripts:**
  - `dev`: Starts the development server.
  - `build`: Creates a production build.
  - `start`: Starts the production server.
  - `lint`: Lints the code.
  - `test`: Runs unit tests with Jest.
  - `test:e2e`: Runs end-to-end tests with Playwright.

### Backend

- **Package Manager:** `pip` and `requirements.txt` are used for dependency management.
- **Testing:** `pytest` is used for testing. Run tests with the `pytest` command.

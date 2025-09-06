# Project

A brief description of your project.

## Getting Started

These instructions will help you get a copy of the project up and running on your local machine.

### Prerequisites

What you need to install:
- Node.js (version X.X.X or higher)
- npm or yarn

### Installation

1. Clone the repository
2. Install dependencies for web app: `cd apps/web && npm install`
3. Install dependencies for API: `cd apps/api && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`

### Running the Application

You can start both the web app and API server using one of the provided run scripts:

**Windows (Command Prompt):**
```bash
run_dev.bat
```

**Windows (PowerShell):**
```powershell
./run_dev.ps1
```

**Linux/Mac:**
```bash
chmod +x run_dev.sh
./run_dev.sh
```

This will start:
- Web app on http://localhost:3000
- API server on http://localhost:8001
- API documentation on http://localhost:8001/docs

## Usage

How to use the project.

## Contributing

Guidelines for contributing to the project.

## License

This project is licensed under the MIT License.
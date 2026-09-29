# Engineering Thesis Project: Project Management App (Jira-style)

A full-stack project management web application inspired by Jira, built as an engineering thesis project. It helps teams track tasks, manage workflows, and leverages external AI to assist with project management tasks.

---

## Key Features

- **Task & Project Management** — Create, assign, and track tasks within a board/workflow system (similar to Jira).
- **User Authentication & Security** — Secure registration and login flow with email confirmation tokens.
- **Git Integration** — Connects with Git repositories to link activity/commits with tasks.
- **AI Assistant (Mistral LLM)** — Integrated with an external LLM API (Mistral) to help generate or summarize task details.
- **Relational Database** — Structured data storage using PostgreSQL.

---

## Tech Stack

- **Backend**: Python, Django, Django REST Framework (lub standardowy Django)
- **Frontend**: Vue.js, Vite
- **Database**: PostgreSQL
- **AI/External APIs**: Mistral AI API, Email service integration
- **Containerization**: Docker & Docker Compose

---

## Getting Started

You can run this project either natively or using Docker.

### Prerequisites
- Python (v3.10+)
- Node.js & Yarn
- PostgreSQL
- Docker & Docker Compose (optional)

### Option 1: Running Locally (Native)

#### 1. Database Setup
Create a PostgreSQL database:
```bash
psql -U postgres
CREATE DATABASE inz_project;

#### 2. Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

pip install -r requirements.txt

# Configure your environment variables (database URL, Mistral API key, etc.) in a .env file

python manage.py migrate
python manage.py runserver

The backend will be available at http://localhost:8000

#### 3. Frontend

cd frontend
yarn install
yarn dev
# or: yarn start

The frontend will be available at http://localhost:5173.

### Option 2: Running with Docker
# Build and start containers
docker-compose up --build

# Run migrations inside the container
docker-compose exec backend python manage.py migrate

# Stop and clean up containers (including volumes)
docker-compose down -v


## Note
*This is a legacy university engineering thesis project developed under tight constraints. While it demonstrates a standard three-tier architecture (Vue + Django + PostgreSQL) and external API integrations, I am well aware of its design flaws, technical debt, and limitations. It is published as-is for educational and portfolio purposes, rather than production use.*

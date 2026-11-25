# OTU Smart Parking Management System

## Project Overview

The Smart Parking Management System is a distributed application developed for our final project.

The system allows users to view parking availability, reserve parking spots, and release existing reservations through a web-based dashboard.

The application uses a central Flask server that communicates with five independent parking lot servers. Each parking lot maintains its own SQLite database.

## Technologies Used

- Python
- Flask
- SQLite
- React
- JavaScript
- Vite
- HTML and CSS
- REST APIs
- Git and GitHub

## System Architecture

The application consists of three main components:

### 1. React Frontend

Provides the user interface for:
- Viewing parking lot availability
- Selecting parking spaces
- Reserving parking spots
- Releasing reservations
- Viewing active reservations
- Monitoring server availability

### 2. Central Flask Server

Runs on port 5000 and:
- Coordinates communication with parking lot servers
- Handles frontend API requests
- Tracks server availability
- Receives heartbeat messages
- Detects server failures

### 3. Parking Lot Servers

Five independent Flask servers manage individual parking lots.

| Parking Lot | Port | Capacity |
|---|---|---|
| Lot A | 5001 | 20 |
| Lot B | 5002 | 35 |
| Lot C | 5003 | 50 |
| Lot D | 5004 | 25 |
| Lot E | 5005 | 40 |

Total capacity: 170 parking spaces.

Each parking lot uses a separate SQLite database.

## Installation

### Requirements

- Python 3
- Node.js and npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/m-usman2004/OTUSmartParkingSystem
cd OTUSmartParkingSystem
```

### 2. Create Python Virtual Environment

On Windows PowerShell:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 3. Install Python Dependencies

```powershell
python -m pip install -r requirements.txt
```

## Running the Application

Open three separate terminals in VS Code.

### Terminal 1 – Central Server

From the project root:

```powershell
.\.venv\Scripts\python.exe central_server/app.py
```

The central server runs at:

http://127.0.0.1:5000

### Terminal 2 – Parking Lot Servers

From the project root:

```powershell
.\.venv\Scripts\python.exe start_lots.py
```

This launches all five parking lot servers.

### Terminal 3 – React Frontend

From the project root:

```powershell
cd frontend
npm install
npm run dev
```

The frontend is configured to run at:

http://localhost:5174

The Vite development server forwards `/api` requests to the central Flask server on port 5000.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/lots | View all parking lots |
| GET | /api/lots/status | View server statuses |
| GET | /api/lots/{lot_id}/spots | View parking spaces |
| GET | /api/lots/{lot_id}/reservations | View active reservations |
| POST | /api/lots/{lot_id}/reserve | Reserve a parking space |
| POST | /api/lots/{lot_id}/release | Release a reservation |

## Running the Concurrency Test

With the central server and all parking lot servers running, execute the following command from the project root:

```powershell
.\.venv\Scripts\python.exe tests/test_concurrency.py
```

This test simulates 20 concurrent reservation requests targeting the same parking space to verify that double-booking is prevented.
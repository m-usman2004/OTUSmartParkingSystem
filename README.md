# OTU Smart Parking Management System

## Project Overview

The Smart Parking Management System is a distributed application developed for our final project.

The system allows users to view parking availability, reserve parking spots, and release existing reservations through a web-based dashboard.

The application uses a primary central Flask server and a backup central Flask server that communicate with five independent parking lot servers. Each parking lot maintains its own SQLite database.

If the primary central server fails, the application automatically switches to the backup central server to continue operating.

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

The application consists of four main components:

### 1. React Frontend

Provides the user interface for:
- Viewing parking lot availability
- Selecting parking spaces
- Reserving parking spots
- Releasing reservations
- Viewing active reservations
- Monitoring server availability
- Automatically switching to the backup central server

### 2. Primary Central Flask Server

Runs on port 5000 and:
- Coordinates communication with parking lot servers
- Handles frontend API requests
- Tracks server availability
- Receives heartbeat messages
- Detects server failures

### 3. Backup Central Flask Server

Runs on port 5100 and:
- Provides a backup if the primary central server fails
- Communicates with all five parking lot servers
- Receives heartbeat messages
- Handles frontend API requests when the primary server is unavailable
- Allows users to continue reserving and releasing parking spaces during primary server failure

### 4. Parking Lot Servers

Five independent Flask servers manage individual parking lots.

| Parking Lot | Port | Capacity |
|---|---|---|
| Lot A | 5001 | 20 |
| Lot B | 5002 | 35 |
| Lot C | 5003 | 50 |
| Lot D | 5004 | 25 |
| Lot E | 5005 | 40 |

Total capacity: 170 parking spaces.

Each parking lot uses a separate SQLite database and communicates with both central servers.

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

Open four separate terminals in VS Code.

### Terminal 1 – Primary Central Server

From the project root:

```powershell
.\.venv\Scripts\python.exe central_server/app.py
```

The primary central server runs at:

http://127.0.0.1:5000

### Terminal 2 – Backup Central Server

From the project root:

```powershell
.\.venv\Scripts\python.exe start_backup.py
```

The backup central server runs at:

http://127.0.0.1:5100

### Terminal 3 – Parking Lot Servers

From the project root:

```powershell
.\.venv\Scripts\python.exe start_lots.py
```

This launches all five parking lot servers.

### Terminal 4 – React Frontend

From the project root:

```powershell
cd frontend
npm install
npm run dev
```

The frontend is configured to run at:

http://localhost:5174

The Vite development server forwards `/api` requests to the primary central Flask server on port 5000 and `/backup-api` requests to the backup central Flask server on port 5100.

If the primary central server becomes unavailable, the frontend automatically switches to the backup central server.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/lots | View all parking lots |
| GET | /api/lots/status | View server statuses |
| GET | /api/lots/{lot_id}/spots | View parking spaces |
| GET | /api/lots/{lot_id}/reservations | View active reservations |
| POST | /api/lots/{lot_id}/reserve | Reserve a parking space |
| POST | /api/lots/{lot_id}/release | Release a reservation |

Both central servers support the same API endpoints.

## Running the Concurrency Test

With the primary central server and all parking lot servers running, execute the following command from the project root:

```powershell
.\.venv\Scripts\python.exe tests/test_concurrency.py
```

This test simulates 20 concurrent reservation requests targeting the same parking space to verify that double-booking is prevented.

## Testing the Backup Central Server

With all four terminals running:

1. Open the parking dashboard.
2. Confirm that all five parking lots are online.
3. Stop the primary central server by pressing Ctrl+C in Terminal 1.
4. Refresh the parking dashboard.
5. Reserve and release a parking space.

The frontend should automatically switch to the backup central server, allowing the system to continue operating while the primary server is offline.

Both central servers currently run on the same computer, so this protects against central server process failures rather than complete computer failures.
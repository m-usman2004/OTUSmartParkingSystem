# OTU Smart Parking Management System

## Project Overview

The Smart Parking Management System is a distributed application developed for SOFE 4790U – Distributed Systems at Ontario Tech University.

The system allows users to view parking availability, reserve parking spots, and release existing reservations through a web-based dashboard.

The application uses a primary central Flask server, a backup central Flask server, and five independent parking lot servers. Each parking lot maintains its own SQLite database.

If the primary central server becomes unavailable, the application automatically switches to the backup central server, allowing users to continue viewing, reserving, and releasing parking spaces.

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
- Automatically switching between central servers
- Accessing parking assistance contact information

### 2. Primary Central Flask Server

Runs on port 5000 and:

- Coordinates communication with parking lot servers
- Handles frontend API requests
- Tracks server availability
- Receives heartbeat messages
- Detects parking lot server failures

### 3. Backup Central Flask Server

Runs on port 5100 and:

- Provides redundancy for the primary central server
- Receives registration and heartbeat information
- Handles frontend requests when the primary server is unavailable
- Communicates with all five parking lot servers
- Allows reservations and releases to continue during primary server failure

The backup server runs the same central server application on a different port.

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

Reservation data is stored at the parking lot level, allowing both central servers to access the same reservation information without maintaining separate copies of the parking databases.

### Server Configuration

| Component | Port |
|---|---|
| Primary Central Server | 5000 |
| Backup Central Server | 5100 |
| Lot A | 5001 |
| Lot B | 5002 |
| Lot C | 5003 |
| Lot D | 5004 |
| Lot E | 5005 |
| React Frontend | 5174 |

## Installation

### Requirements

- Python 3
- Node.js and npm
- Git
- VS Code (recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/m-usman2004/OTUSmartParkingSystem.git
cd OTUSmartParkingSystem
```

### 2. Create Python Virtual Environment

On Windows PowerShell:

```powershell
python -m venv .venv
```

### 3. Install Python Dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
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

If PowerShell prevents npm scripts from running, use:

```powershell
npm.cmd install
npm.cmd run dev
```

The frontend is configured to run at:

http://localhost:5174

The Vite development server forwards `/api` requests to the primary central server on port 5000 and `/backup-api` requests to the backup central server on port 5100.

The frontend automatically switches to the other central server when its current central server becomes unreachable.

Keep all four terminals running while using the application.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/health | Check central server availability |
| GET | /api/lots | View all parking lots |
| GET | /api/lots/status | View server statuses |
| GET | /api/lots/{lot_id}/spots | View parking spaces |
| GET | /api/lots/{lot_id}/reservations | View active reservations |
| POST | /api/lots/{lot_id}/reserve | Reserve a parking space |
| POST | /api/lots/{lot_id}/release | Release a reservation |
| POST | /api/register | Register a parking lot server |
| POST | /api/heartbeat | Receive parking lot heartbeat |

Both central servers provide the same API endpoints.

### Reservation Request Example

```json
{
  "spot_id": 5,
  "user_name": "Test User"
}
```

### Release Request Example

```json
{
  "reservation_id": 1
}
```

## Distributed Systems Features

### Concurrency Control

The system uses SQLite transactions to prevent multiple users from reserving the same parking space simultaneously.

When multiple requests attempt to reserve the same available parking spot, only one reservation should succeed. The remaining requests receive an HTTP 409 conflict response.

### Heartbeat Monitoring

Parking lot servers send heartbeat messages to both central servers approximately every five seconds.

If a parking lot server stops communicating for approximately 15 seconds, it is marked offline.

### Fault Tolerance

If one parking lot server fails, the remaining parking lot servers continue operating independently.

The dashboard identifies the unavailable parking lot and prevents users from reserving spaces through that server.

### Central Server Redundancy

The system includes a primary and backup central server to reduce the dependency on a single central server.

Both central servers communicate with the same independent parking lot servers.

If the primary central server fails, the backup central server can continue handling application requests.

### Automatic Failover

The frontend initially communicates with the primary central server.

If the primary central server becomes unreachable, the frontend automatically attempts to send requests through the backup central server.

Users do not need to manually change server addresses or restart the application.

Since reservation data is stored in the individual parking lot databases, existing reservations remain available when the application switches central servers.

### Automatic Recovery

When a failed parking lot server restarts, it automatically reconnects to the central servers.

### Distributed Data Storage

Each parking lot maintains its own SQLite database rather than using one shared database for every parking lot.

This allows parking lots to manage their own reservation records independently.

## Testing Results

### Reservation Testing

Users successfully reserved and released parking spaces through the React dashboard.

Parking availability and active reservations were updated following successful requests.

### Concurrency Testing

Twenty simultaneous reservation requests were sent for the same parking spot.

Results:

- Successful reservations: 1
- Conflicts prevented: 19
- Unexpected responses: 0

To run the concurrency test, make sure the primary central server and parking lot servers are running and that the parking spot being tested is available.

From the project root:

```powershell
.\.venv\Scripts\python.exe tests/test_concurrency.py
```

### Failure Detection Testing

Lot A was temporarily disabled.

Results:

- Lot A was marked offline.
- The central dashboard displayed 4/5 online servers.
- Lots B, C, D, and E remained operational.

### Recovery Testing

Lot A was restarted and automatically re-registered.

All five parking lot servers returned to online status.

### Central Server Failover Testing

The primary central server was intentionally shut down while the backup central server, parking lot servers, and React frontend remained running.

Results:

- The primary central server became unavailable.
- The backup central server remained online.
- The frontend automatically switched to the backup central server.
- All five parking lot servers remained available.
- Users successfully created new reservations.
- Users successfully released reservations.
- The application continued operating without being restarted.

This demonstrated that the system could tolerate a primary central server process failure.

### How to Test Central Server Failover

1. Start the primary central server.
2. Start the backup central server.
3. Start all five parking lot servers.
4. Start the React frontend.
5. Open the parking dashboard at http://localhost:5174.
6. Confirm that all five parking lots are online.
7. Reserve an available parking space.
8. Stop the primary central server by pressing Ctrl+C in its terminal.
9. Verify that http://127.0.0.1:5000/api/health is unavailable.
10. Verify that http://127.0.0.1:5100/api/health remains available.
11. Refresh the parking dashboard.
12. Reserve another parking space.
13. Release a reservation.
14. Confirm that parking availability updates correctly.

The backup central server, parking lot servers, and frontend must remain running throughout the test.

### Performance Testing

One hundred sequential GET requests were sent to the central server.

| Metric | Result |
|---|---|
| Total Requests | 100 |
| Successful Requests | 100 |
| Average Response Time | 144.50 ms |
| Minimum Response Time | 64.43 ms |
| Maximum Response Time | 176.19 ms |
| Median Response Time | 148.48 ms |

These results represent local development testing and were collected before the backup central server was introduced.

The performance test measures sequential request response times rather than maximum concurrent user capacity.

## Known Limitations

- The application is designed for local demonstration.
- Authentication is not implemented.
- Parking availability is simulated through reservations rather than physical IoT sensors.
- Dynamic pricing is not implemented.
- Both central servers currently run on the same computer.
- A complete computer failure would affect both central servers.
- If both central servers become unavailable, the frontend cannot access the parking lot servers.
- Interrupted reservation requests during failover require further testing.
- Flask development servers are not intended for production deployment.

## Future Improvements

- User authentication and authorization
- Real IoT parking sensors
- Dynamic parking pricing
- Cloud deployment
- Deploying central servers on separate machines
- Additional parking lot servers
- Concurrent load testing
- Improved security and monitoring
- Improved handling of interrupted requests during failover
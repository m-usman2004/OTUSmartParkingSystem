from flask import Flask, jsonify, request
import requests, sys, time, threading
from pathlib import Path
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

#import our shared parking lot configuration
from lots_config import LOT_CONFIG

app = Flask(__name__)

#allow the React frontend to communicate with the central server
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ]
    }
})

#stores information about parking lot servers that have registered
registered_lots = {}

#lock to protect the shared registry from concurrent updates
registry_lock = threading.Lock()


#endpoint - checks if the central server is running
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "message": "Central server is running"
    })


#endpoint - retrieves parking spots from a specified parking lot
@app.route("/api/lots/<lot_id>/spots", methods=["GET"])
def get_lot_spots(lot_id):

    #retrieve the lot URL using the heartbeat registry
    lot_url, status = get_online_lot_url(lot_id)

    if status == 404:
        return jsonify({"error": "Parking lot not found"}), 404

    if status == 503:
        return jsonify({
            "error": f"Parking Lot {lot_id} is currently unavailable"
        }), 503

    try:
        #send a GET request to the specified parking lot server
        response = requests.get(
            f"{lot_url}/api/spots",
            timeout=3
        )

        response.raise_for_status()

        return jsonify(response.json()), 200

    except requests.RequestException:
        #handle cases where the parking lot server is unavailable
        return jsonify({
            "error": f"Parking Lot {lot_id} is currently unavailable"
        }), 503
    
#endpoint - forwards reservation requests to the specified parking lot
@app.route("/api/lots/<lot_id>/reserve", methods=["POST"])
def reserve_lot_spot(lot_id):

    #retrieve the lot URL using the heartbeat registry
    lot_url, status = get_online_lot_url(lot_id)

    if status == 404:
        return jsonify({"error": "Parking lot not found"}), 404

    if status == 503:
        return jsonify({
            "error": f"Parking Lot {lot_id} is currently unavailable"
        }), 503

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    try:
        #forward the reservation request to the specified lot server
        response = requests.post(
            f"{lot_url}/api/reserve",
            json=data,
            timeout=3
        )

        #return the lot server's response and HTTP status code
        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        #handle cases where the parking lot server is unreachable
        return jsonify({
            "error": f"Parking Lot {lot_id} is currently unavailable"
        }), 503


#endpoint - forwards reservation release requests to a specified parking lot
@app.route("/api/lots/<lot_id>/release", methods=["POST"])
def release_lot_spot(lot_id):

    #retrieve the lot URL using the heartbeat registry
    lot_url, status = get_online_lot_url(lot_id)

    if status == 404:
        return jsonify({"error": "Parking lot not found"}), 404

    if status == 503:
        return jsonify({
            "error": f"Parking Lot {lot_id} is currently unavailable"
        }), 503
    
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    try:
        #forward the release request to the appropriate lot server
        response = requests.post(
            f"{lot_url}/api/release",
            json=data,
            timeout=3
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        #handle cases where the lot server cannot be reached
        return jsonify({
            "error": f"Parking Lot {lot_id} is currently unavailable"
        }), 503

#endpoint - retrieves active reservations from a specified parking lot
@app.route("/api/lots/<lot_id>/reservations", methods=["GET"])
def get_lot_reservations(lot_id):

    #retrieve the lot URL using the heartbeat registry
    lot_url, status = get_online_lot_url(lot_id)

    if status == 404:
        return jsonify({"error": "Parking lot not found"}), 404

    if status == 503:
        return jsonify({
            "error": f"Parking Lot {lot_id} is currently unavailable"
        }), 503

    try:
        #request active reservations from the specified lot server
        response = requests.get(
            f"{lot_url}/api/reservations",
            timeout=3
        )

        response.raise_for_status()

        return jsonify(response.json()), 200

    except requests.RequestException:
        #handle cases where the lot server is unavailable
        return jsonify({
            "error": f"Parking Lot {lot_id} is currently unavailable"
        }), 503

#endpoint - retrieves an overview of all parking lots
@app.route("/api/lots", methods=["GET"])
def get_all_lots():

    lots = []

    #loop through every configured parking lot
    for lot_id in LOT_CONFIG:

        #check whether the lot is online based on its heartbeats
        if not is_lot_online(lot_id):
            lots.append({
                "lot_id": lot_id,
                "status": "offline",
                "capacity": LOT_CONFIG[lot_id]["capacity"],
                "available": None,
                "reserved": None
            })
            continue

        #get the registered server's address
        with registry_lock:
            lot_url = registered_lots[lot_id]["url"]

        try:
            #request parking spots from the registered lot server
            response = requests.get(
                f"{lot_url}/api/spots",
                timeout=3
            )

            response.raise_for_status()
            spots = response.json()

            #count available and reserved parking spaces
            available = sum(
                1 for spot in spots
                if spot["status"] == "available"
            )

            reserved = sum(
                1 for spot in spots
                if spot["status"] == "reserved"
            )

            lots.append({
                "lot_id": lot_id,
                "status": "online",
                "capacity": len(spots),
                "available": available,
                "reserved": reserved
            })

        except (requests.RequestException, ValueError, KeyError, TypeError):
            #the server did not respond successfully
            lots.append({
                "lot_id": lot_id,
                "status": "offline",
                "capacity": LOT_CONFIG[lot_id]["capacity"],
                "available": None,
                "reserved": None
            })

    return jsonify(lots), 200


#endpoint - allows parking lot servers to register with the central server
@app.route("/api/register", methods=["POST"])
def register_lot():

    #get the registration information from the lot server
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    lot_id = data.get("lot_id")
    port = data.get("port")

    #validate the parking lot ID and port
    if not isinstance(lot_id, str) or not lot_id.strip():
        return jsonify({"error": "Invalid lot ID"}), 400

    if type(port) is not int or not (1 <= port <= 65535):
        return jsonify({"error": "Invalid port"}), 400

    #only accept known parking lots for now
    if lot_id not in LOT_CONFIG:
        return jsonify({"error": "Unknown parking lot"}), 404

    #use the configured address rather than trusting an arbitrary URL
    lot_url = f"http://127.0.0.1:{LOT_CONFIG[lot_id]['port']}"

    #ensure the supplied port matches this lot's configuration
    if port != LOT_CONFIG[lot_id]["port"]:
        return jsonify({"error": "Port does not match configuration"}), 400

    #register the parking lot and record when it was last seen
    with registry_lock:
        registered_lots[lot_id] = {
            "url": lot_url,
            "status": "online",
            "last_heartbeat": time.monotonic()
        }

    return jsonify({
        "message": f"Parking Lot {lot_id} registered successfully",
        "lot_id": lot_id
    }), 200

#maximum time allowed without a heartbeat before a lot is considered offline
HEARTBEAT_TIMEOUT = 15


#check whether a registered parking lot is still online
def is_lot_online(lot_id):

    #protect the shared registry while accessing it
    with registry_lock:
        lot = registered_lots.get(lot_id)

        #a lot that hasn't registered is considered offline
        if lot is None:
            return False

        #calculate how long it's been since the last heartbeat
        elapsed = time.monotonic() - lot["last_heartbeat"]

        #mark the lot offline if its heartbeat has expired
        if elapsed > HEARTBEAT_TIMEOUT:
            lot["status"] = "offline"
            return False

        lot["status"] = "online"
        return True

#retrieve the URL of a registered parking lot if its heartbeat is valid
def get_online_lot_url(lot_id):

    #check if the requested lot exists
    if lot_id not in LOT_CONFIG:
        return None, 404

    #check the registry and retrieve the URL under the same lock
    with registry_lock:
        lot = registered_lots.get(lot_id)

        if lot is None:
            return None, 503

        #check how long ago the last heartbeat was received
        elapsed = time.monotonic() - lot["last_heartbeat"]

        if elapsed > HEARTBEAT_TIMEOUT:
            lot["status"] = "offline"
            return None, 503

        lot["status"] = "online"

        return lot["url"], 200

#endpoint - receives heartbeat messages from parking lot servers
@app.route("/api/heartbeat", methods=["POST"])
def receive_heartbeat():

    #retrieve the heartbeat data
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    lot_id = data.get("lot_id")

    #validate the parking lot ID
    if not isinstance(lot_id, str) or lot_id not in LOT_CONFIG:
        return jsonify({"error": "Invalid lot ID"}), 400

    #update the last heartbeat time for the registered lot
    with registry_lock:

        if lot_id not in registered_lots:
            return jsonify({
                "error": "Parking lot is not registered"
            }), 404

        registered_lots[lot_id]["last_heartbeat"] = time.monotonic()
        registered_lots[lot_id]["status"] = "online"

    return jsonify({
        "message": f"Heartbeat received from Lot {lot_id}"
    }), 200

#endpoint - retrieves the heartbeat status of all parking lot servers
@app.route("/api/lots/status", methods=["GET"])
def get_lot_status():

    statuses = []

    #check each parking lot's heartbeat status
    for lot_id in LOT_CONFIG:

        online = is_lot_online(lot_id)

        statuses.append({
            "lot_id": lot_id,
            "status": "online" if online else "offline"
        })

    return jsonify(statuses), 200

if __name__ == "__main__":
    #start the central server on port 5000
    app.run(port=5000, debug=False)
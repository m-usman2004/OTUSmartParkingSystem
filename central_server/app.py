from flask import Flask, jsonify, request
import requests, sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

#import our shared parking lot configuration
from lots_config import LOT_CONFIG

app = Flask(__name__)

#parking lot server registry
#generate the lot server registry from our shared configuration
LOT_SERVERS = {
    lot_id: f"http://127.0.0.1:{config['port']}"
    for lot_id, config in LOT_CONFIG.items()
}


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

    #check if the requested lot exists in our registry
    if lot_id not in LOT_SERVERS:
        return jsonify({"error": "Parking lot not found"}), 404

    lot_url = LOT_SERVERS[lot_id]

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

    #check if the parking lot exists in our registry
    if lot_id not in LOT_SERVERS:
        return jsonify({"error": "Parking lot not found"}), 404

    lot_url = LOT_SERVERS[lot_id]

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

    except requests.RequestException:
        #handle cases where Lot As server is unreachable
        return jsonify({
            "error": "Parking Lot A is currently unavailable"
        }), 503


#endpoint - forwards reservation release requests to a specified parking lot
@app.route("/api/lots/<lot_id>/release", methods=["POST"])
def release_lot_spot(lot_id):

    #check if the requested lot exists
    if lot_id not in LOT_SERVERS:
        return jsonify({"error": "Parking lot not found"}), 404

    #get the address of the requested parking lot server
    lot_url = LOT_SERVERS[lot_id]
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

    #check if the requested parking lot exists
    if lot_id not in LOT_SERVERS:
        return jsonify({"error": "Parking lot not found"}), 404

    #get the parking lot server address
    lot_url = LOT_SERVERS[lot_id]

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

    #loop through every registered parking lot
    for lot_id, lot_url in LOT_SERVERS.items():

        try:
            #request parking spots from this lot server
            response = requests.get(
                f"{lot_url}/api/spots",
                timeout=3
            )

            response.raise_for_status()
            spots = response.json()

            #calculate the number of available and reserved spots
            available = sum(
                1 for spot in spots
                if spot["status"] == "available"
            )

            reserved = sum(
                1 for spot in spots
                if spot["status"] == "reserved"
            )

            #add the lot's information to our list
            lots.append({
                "lot_id": lot_id,
                "status": "online",
                "capacity": len(spots),
                "available": available,
                "reserved": reserved
            })

        except (requests.RequestException, ValueError, KeyError, TypeError):
            #if a lot is unreachable or returns invalid data, mark it offline
            lots.append({
                "lot_id": lot_id,
                "status": "offline",
                "capacity": LOT_CONFIG[lot_id]["capacity"],
                "available": None,
                "reserved": None
            })

    return jsonify(lots), 200

if __name__ == "__main__":
    #start the central server on port 5000
    app.run(port=5000, debug=True)
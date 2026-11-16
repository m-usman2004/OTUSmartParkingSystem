from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

#address of the first parking lot server
LOT_A_URL = "http://127.0.0.1:5001"


#endpoint - checks if the central server is running
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "message": "Central server is running"
    })


#endpoint - retrieves parking spots from Lot A
@app.route("/api/lots/A/spots", methods=["GET"])
def get_lot_a_spots():
    try:
        #sends a GET request to the parking lot server
        response = requests.get(
            f"{LOT_A_URL}/api/spots",
            timeout=3
        )

        response.raise_for_status()

        #return the parking spots received from the lot server
        return jsonify(response.json()), 200

    except requests.RequestException:
      
        return jsonify({
            "error": "Parking Lot A is currently unavailable"
        }), 503

#endpoint - forwards reservation requests to Lot A
@app.route("/api/lots/A/reserve", methods=["POST"])
def reserve_lot_a_spot():

    #gets the JSON data sent by the user
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    try:
        #forward the reservation request to Lot As server
        response = requests.post(
            f"{LOT_A_URL}/api/reserve",
            json=data,
            timeout=3
        )

        #return the lot server's response and HTTP status code
        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        #handle cases where Lot As server is unreachable
        return jsonify({
            "error": "Parking Lot A is currently unavailable"
        }), 503


#endpoint - forwards reservation release requests to Lot A
@app.route("/api/lots/A/release", methods=["POST"])
def release_lot_a_spot():

    #get the JSON data sent by the user
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    try:
        #forward the release request to Lot A's server
        response = requests.post(
            f"{LOT_A_URL}/api/release",
            json=data,
            timeout=3
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        #handle cases where Lot As server is unreachable
        return jsonify({
            "error": "Parking Lot A is currently unavailable"
        }), 503


#endpoint - retrieves active reservations from Lot A
@app.route("/api/lots/A/reservations", methods=["GET"])
def get_lot_a_reservations():

    try:
        #send a GET request to Lot A's server
        response = requests.get(
            f"{LOT_A_URL}/api/reservations",
            timeout=3
        )

        #check if the lot server returned an HTTP error
        response.raise_for_status()

        return jsonify(response.json()), 200

    except requests.RequestException:
        #handle cases where Lot A's server is unavailable
        return jsonify({
            "error": "Parking Lot A is currently unavailable"
        }), 503
    
if __name__ == "__main__":
    #start the central server on port 5000
    app.run(port=5000, debug=True)
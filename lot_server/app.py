from flask import Flask, jsonify, request
from database import initialize_database, DB_PATH
import sqlite3
import os

app = Flask(__name__)

#endpoint - returns server health info
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "message": "Parking lot server is running"
    })

#endpoint - get parking spots
#retrives all spots, available AND not available
@app.route("/api/spots", methods=["GET"])
def get_spots():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parking_spots")

    spots = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify(spots)

#endpoint - creating reservations
@app.route("/api/reserve", methods=["POST"])
def reserve_spot():
    data = request.get_json(silent=True)

    #checks if request has valid json object
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    #gets the spot Id and username of user booking
    spot_id = data.get("spot_id")
    user_name = data.get("user_name")

    if type(spot_id) is not int or spot_id <= 0:
        return jsonify({"error": "Invalid spot ID"}), 400

    if not isinstance(user_name, str) or not user_name.strip():
        return jsonify({"error": "User name is required"}), 400

    #connecting to DB
    conn = sqlite3.connect(DB_PATH, timeout=5)

    try:
        #begins a write transaction to prevent concurrent reservations
        #only one connection can hold the SQLite write lock at a time
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()

        #attempts to reserve the spot, only updates if spot is avaiable
        cursor.execute(
            """
            UPDATE parking_spots
            SET status = 'reserved'
            WHERE id = ? AND status = 'available'
            """,
            (spot_id,)
        )

        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({
                "error": "Spot does not exist or is already reserved"
            }), 409

        #creates a reservation record associated with the user and parking spot
        cursor.execute(
            """
            INSERT INTO reservations (spot_id, user_name, status)
            VALUES (?, ?, 'active')
            """,
            (spot_id, user_name.strip())
        )

        reservation_id = cursor.lastrowid
        conn.commit()

        return jsonify({
            "message": "Spot reserved successfully",
            "reservation_id": reservation_id,
            "spot_id": spot_id
        }), 201

    except sqlite3.Error:
        conn.rollback()
        return jsonify({"error": "Database operation failed"}), 500

    finally:
        conn.close()

#endpoint - releasing a parking reservation
@app.route("/api/release", methods=["POST"])
def release_spot():

    
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    reservation_id = data.get("reservation_id")

    #validate reservation ID
    if type(reservation_id) is not int or reservation_id <= 0:
        return jsonify({"error": "Invalid reservation ID"}), 400

    #connect to the database
    conn = sqlite3.connect(DB_PATH, timeout=5)

    try:
        #begin a write transaction - locks it 
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()

        #find the active reservation
        cursor.execute(
            """
            SELECT spot_id FROM reservations
            WHERE id = ? AND status = 'active'
            """,
            (reservation_id,)
        )

        reservation = cursor.fetchone()

        #check whether an active reservation exists
        if reservation is None:
            conn.rollback()
            return jsonify({
                "error": "Active reservation not found"
            }), 404

        spot_id = reservation[0]

        #mark the reservation as released
        cursor.execute(
            """
            UPDATE reservations
            SET status = 'released'
            WHERE id = ?
            """,
            (reservation_id,)
        )

        #make the parking spot avaiable again
        cursor.execute(
            """
            UPDATE parking_spots
            SET status = 'available'
            WHERE id = ?
            """,
            (spot_id,)
        )

        #save both database changes
        conn.commit()

        return jsonify({
            "message": "Reservation released successfully",
            "reservation_id": reservation_id,
            "spot_id": spot_id
        }), 200

    except sqlite3.Error:
        #undo changes if a database error occurs
        conn.rollback()
        return jsonify({"error": "Database operation failed"}), 500

    finally:
        conn.close()

#endpoint - retrieves active parking reservations
@app.route("/api/reservations", methods=["GET"])
def get_reservations():

    #connect to the SQLite database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    #retrieve all active reservations and their spot numbers
    cursor.execute(
        """
        SELECT
            reservations.id,
            reservations.spot_id,
            parking_spots.spot_number,
            reservations.user_name,
            reservations.status
        FROM reservations
        JOIN parking_spots
            ON reservations.spot_id = parking_spots.id
        WHERE reservations.status = 'active'
        """
    )

    #convert the database rows into dictionaries
    reservations = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify(reservations)

if __name__ == "__main__":
     #initialize this lot's database
    initialize_database()

    #get the port from an environment variable
    port = int(os.getenv("PORT", "5001"))

    #start the parking lot server
    app.run(port=port, debug=False)
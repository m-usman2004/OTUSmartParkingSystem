import sqlite3
from pathlib import Path
import os

LOT_ID = os.getenv("LOT_ID", "A")
LOT_CAPACITY = int(os.getenv("LOT_CAPACITY", "10")) 
DB_PATH = Path(__file__).parent / f"parking_{LOT_ID}.db"


def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    #creates table to store parking space if table isn't made yet
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_number TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'available'
        )
    """)

    #creates table to store reservations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY (spot_id) REFERENCES parking_spots(id)
        )
    """)

    #adds any missing parking spots up to the configured capacity
    #existing spots and reservations remain unchanged
    for i in range(1, LOT_CAPACITY + 1):
        spot_number = f"{LOT_ID}{i}"

        cursor.execute(
            """
            INSERT OR IGNORE INTO parking_spots (spot_number)
            VALUES (?)
            """,
            (spot_number,)
        )

    #saving db changes
    conn.commit()
    conn.close()
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "parking.db"


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

    #Insert 10 parking spots if the table is empty
    cursor.execute("SELECT COUNT(*) FROM parking_spots")
    count = cursor.fetchone()[0]

    if count == 0:
        for i in range(1, 11):
            cursor.execute(
                "INSERT INTO parking_spots (spot_number) VALUES (?)",
                (f"A{i}",)
            )

    #saving db changes
    conn.commit()
    conn.close()
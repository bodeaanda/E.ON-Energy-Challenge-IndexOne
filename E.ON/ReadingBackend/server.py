from flask import Flask, request, jsonify, send_file
import sqlite3
import cv2
import numpy as np
import os
from meter_reader import GasMeterReader

app = Flask(__name__)
ai_reader = GasMeterReader()

# Global variable to hold the target RTC interval (in seconds). 
TARGET_INTERVAL = 60 

def init_db():
    """Creates a simple database table to store our readings."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reading_value TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# --- ESP32 ENDPOINT ---
@app.route('/upload', methods=['POST'])
def receive_image():
    global TARGET_INTERVAL
    print("\n[SERVER] ESP32 woke up and sent an image!")
    
    image_data = request.data
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return "Failed to decode", 400

    # === THE NEW VISUAL TESTING FIX ===
    # Save the exact image the ESP32 took directly to your folder
    cv2.imwrite("latest_capture.jpg", img)
    print("[SERVER] SUCCESS: Saved what the camera saw to 'latest_capture.jpg'")

    # 1. Ask the AI to read it
    reading = ai_reader.process_image(img)

    if reading:
        print(f"[SERVER] AI successfully read: {reading}")
        # 2. Save it to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO readings (reading_value) VALUES (?)", (reading,))
        conn.commit()
        conn.close()
    else:
        print("[SERVER] AI could not find numbers. Check the picture!")

    # 3. Tell the ESP32 what interval to set its RTC to
    response_string = f"INTERVAL={TARGET_INTERVAL}"
    return response_string, 200


# --- MOBILE APP ENDPOINTS ---
@app.route('/api/latest', methods=['GET'])
def get_latest_reading():
    """The App calls this to see the most recent gas meter reading."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT reading_value, timestamp FROM readings ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({"reading": row[0], "time": row[1]}), 200
    else:
        return jsonify({"message": "No readings yet"}), 404

@app.route('/api/set_interval', methods=['POST'])
def set_interval():
    """The App calls this to change how often the ESP32 wakes up."""
    global TARGET_INTERVAL
    data = request.json
    new_interval = data.get('interval')
    
    if new_interval:
        TARGET_INTERVAL = int(new_interval)
        return jsonify({"message": f"Interval updated. ESP32 will switch to {TARGET_INTERVAL}s on its next wakeup."}), 200
    return jsonify({"error": "Bad request"}), 400

# === BRAND NEW ROUTE FOR TESTING ===
@app.route('/latest-image', methods=['GET'])
def serve_latest_image():
    """Open this in your browser to physically see the last photo taken!"""
    if os.path.exists("latest_capture.jpg"):
        return send_file("latest_capture.jpg", mimetype='image/jpeg')
    else:
        return "No image captured yet. Jump-start the ESP32!", 404


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
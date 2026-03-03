import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import shutil
import cv2
import numpy as np
import os
from datetime import datetime

from . import models, database

# Import AI logic
try:
    from .meter_reader import GasMeterReader
except ImportError:
    from meter_reader import GasMeterReader

app = FastAPI()

# Init AI models
ai_reader = GasMeterReader()

# PostgreSQL tables
models.Base.metadata.create_all(bind=database.engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Folder for saved uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Endpoint 1: for ESP32 (wakes up -> takes picture -> sends -> shuts down)
@app.post("/receive-image")
async def receive_image_from_esp32(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    
    # Automatically called by ESP32
    print(f"[{datetime.now()}] ESP32 connection received...")
    
    try:
        # Read image directly from the memory for OpenCV
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            print("Error: Image couldn't be decoded.")
            raise HTTPException(status_code=400, detail="Invalid image")

        # *Save image on disk just for verification
        filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        save_path = os.path.join(UPLOAD_DIR, filename)
        cv2.imwrite(save_path, img)
        print(f"Image saved at: {save_path}")

        # Process AI
        detected_value_str = ai_reader.process_image(img) # process_image returns a string
        
        final_reading = 0.0
        status = "FAILED"

        if detected_value_str:
            try:
                final_reading = float(detected_value_str)
                status = "SUCCESS"
                print(f"✅ AI Detected: {final_reading}")
            except ValueError:
                status = "INVALID_FORMAT"
                print(f"⚠️ AI returned invalid format: {detected_value_str}")
        else:
            status = "NO_DIGITS"
            print("❌ AI hasn't found any digits.")

        # Save data in DB Postgres
        new_reading = models.MeterReading(
            reading_value=final_reading,
            meter_id="esp32_cam_01",
            status=status,
            # recorded_at is automatically in the db
        )
        db.add(new_reading)
        db.commit()
        db.refresh(new_reading)

        # Respond to ESP32 (like a feedback)
        return {"status": "ok", "command": "SLEEP_NOW"}

    except Exception as e:
        print(f"Eroare server: {e}")
        return {"status": "error", "detail": str(e)}

# Endpoint 2 : for Flutter (user wants to see the data)
@app.get("/readings")
async def get_readings(limit: int = 10, db: Session = Depends(database.get_db)):
   # it doesn't wake the ESP32 up
    readings = db.query(models.MeterReading)\
                 .order_by(models.MeterReading.recorded_at.desc())\
                 .limit(limit)\
                 .all()
    
    # Transform data in a simpler format for Flutter
    data = []
    for r in readings:
        data.append({
            "id": r.id,
            "value": r.reading_value,
            "date": r.recorded_at.strftime("%Y-%m-%d %H:%M"),
            "status": r.status
        })
        
    return {"status": "success", "data": data}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
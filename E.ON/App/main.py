import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import cv2
import numpy as np
import os
from datetime import datetime

from . import models, database, analytics 

# Import AI logic
try:
    from .meter_reader import GasMeterReader
except ImportError:
    from meter_reader import GasMeterReader

app = FastAPI()

# Init AI models
print("Initializing AI...")
try:
    ai_reader = GasMeterReader()
    print("AI Loaded.")
except:
    ai_reader = None
    print("AI Failed to load.")

# PostgreSQL tables initialization
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

# Endpoint 1: for ESP32
@app.post("/receive-image")
async def receive_image_from_esp32(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection received...")
    
    try:
        # 1. Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image")

        # 2. Save backup
        filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        save_path = os.path.join(UPLOAD_DIR, filename)
        cv2.imwrite(save_path, img)

        # 3. Process AI
        final_reading = 0.0
        status = "FAILED"

        if ai_reader:
            detected_value_str = ai_reader.process_image(img)
            
            if detected_value_str:
                try:
                    final_reading = float(detected_value_str)
                    status = "SUCCESS"
                    print(f"✅ AI Detected: {final_reading}")
                except ValueError:
                    status = "INVALID_FORMAT"
            else:
                status = "NO_DIGITS"
                print("❌ AI hasn't found digits.")
        else:
            status = "AI_ERROR"

        # 4. Save to DB
        new_reading = models.MeterReading(
            reading_value=final_reading,
            meter_id="esp32_cam_01",
            status=status
        )
        db.add(new_reading)
        db.commit()
        db.refresh(new_reading)

        # 5. RUN ANALYTICS (Anomaly Detection)
        # Luam toate citirile din DB
        all_readings = db.query(models.MeterReading).all()

        # APELAM FUNCTIA DIN MODULUL IMPORTAT 'analytics'
        is_anomaly, message = analytics.detect_anomaly(all_readings)

        # 6. Return Combined Response
        # Trimitem si datele pentru Flutter (anomalie), si comanda pentru ESP32 (Sleep)
        return {
            "status": "success",
            "value": final_reading,
            "is_anomaly": is_anomaly,       # <--- Pentru Flutter
            "alert_message": message,       # <--- Pentru Flutter
            "command": "SLEEP_NOW"          # <--- Pentru ESP32
        }

    except Exception as e:
        print(f"Server Error: {e}")
        return {"status": "error", "detail": str(e)}

# Endpoint 2 : for Flutter history
@app.get("/readings")
async def get_readings(limit: int = 10, db: Session = Depends(database.get_db)):
    readings = db.query(models.MeterReading)\
                 .order_by(models.MeterReading.recorded_at.desc())\
                 .limit(limit)\
                 .all()
    
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
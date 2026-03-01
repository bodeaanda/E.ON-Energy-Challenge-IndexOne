import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import requests # Pentru a trimite comanda către ESP32
import os
import random # Pentru a genera date simulate mai realiste

from sqlalchemy.orm import Session
from . import models, database

app = FastAPI()

# Creăm tabelele în baza de date (dacă e cazul)
models.Base.metadata.create_all(bind=database.engine)

# Permitem Flutter-ului (Web/Mobil) să comunice cu serverul
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adresa IP a ESP32-CAM (o găsești în Serial Monitor-ul din Arduino IDE)
ESP32_IP = "http://192.168.1.XX" 

@app.post("/upload-meter-photo")
async def trigger_and_process(db: Session = Depends(database.get_db)):
    """
    Pasul 1: Aplicația Flutter apelează acest endpoint.
    Pasul 2: Serverul cere ESP32-ului să facă o poză.
    """
    try:
        print("Solicit poză de la ESP32...")
        # Trimitem un semnal către ESP32 (trebuie să ai un endpoint /capture pe ESP)
        # timeout-ul este important pentru că procesarea pozei durează
        response = requests.get(f"{ESP32_IP}/capture", timeout=10)
        
        if response.status_code == 200:
            # Aici vei apela funcția ta de OCR (pe care o vom scrie ulterior)
            # Momentan simulăm o citire (adaugam variatie random pentru teste):
            base_reading = 125.40 
            simulated_reading = base_reading + random.uniform(0.1, 5.0)
            
            # Salvăm în baza de date
            new_reading = models.MeterReading(
                reading_value=simulated_reading,
                meter_id="meter_esp32_01"  # Nume hardcodat momentan
            )
            db.add(new_reading)
            db.commit()
            db.refresh(new_reading)
            
            print(f"Citire salvată în DB: {new_reading.reading_value} (ID: {new_reading.id})")
            return {
                "status": "success",
                "reading": new_reading.reading_value,
                "record_id": new_reading.id,
                "message": "Poza a fost capturată, procesată și salvată în baza de date!"
            }
        else:
            raise HTTPException(status_code=500, detail="ESP32 nu a putut face poza")
            
    except Exception as e:
        print(f"Eroare: {e}")
        # Dacă ESP32 nu e pornit, returnăm totuși ceva să nu crape aplicația
        return {"status": "error", "message": str(e), "reading": 0.0}

# Endpoint separat prin care ESP32 poate trimite poza direct (dacă e configurat așa)
@app.post("/receive-image")
async def receive_image(file: UploadFile = File(...)):
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    return {"info": f"Fișier salvat la {file_location}"}

# --- ENDPOINT NOU PENTRU CITIREA DATELOR DIN DB ---
@app.get("/readings")
async def get_readings(limit: int = 10, db: Session = Depends(database.get_db)):
    """
    Returnează ultimele înregistrări din baza de date pentru a le afișa în Flutter.
    """
    readings = db.query(models.MeterReading).order_by(models.MeterReading.recorded_at.desc()).limit(limit).all()
    return {"status": "success", "data": readings}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
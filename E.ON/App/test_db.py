import sys
import os
# Add the directory containing the 'App' package to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from App import models, database
from datetime import datetime
import random

def test_db():
    print("Testing DB connection...")
    db = database.SessionLocal()
    try:
        # Create a dummy reading
        base_reading = 100.0
        simulated_reading = base_reading + random.uniform(0.1, 5.0)
        
        new_reading = models.MeterReading(
            reading_value=simulated_reading,
            meter_id="test_script_meter"
        )
        db.add(new_reading)
        db.commit()
        db.refresh(new_reading)
        
        print(f"SUCCESS! Added reading {new_reading.reading_value} with ID {new_reading.id}")
        
        # Fetch it back
        records = db.query(models.MeterReading).all()
        print(f"Total records in DB: {len(records)}")
        for r in records:
            print(f"- ID {r.id}: {r.reading_value} taken at {r.recorded_at}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_db()

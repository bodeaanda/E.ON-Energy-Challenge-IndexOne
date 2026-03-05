import statistics

def detect_anomaly(readings: list):
    if len(readings) < 5:
        return False, "Not enough data!"

    sorted_readings = sorted(readings, key=lambda x: x.recorded_at) 
    
    # Calculate consumption
    consumptions = []
    
    for i in range(1, len(sorted_readings)):
        prev = sorted_readings[i-1].reading_value
        curr = sorted_readings[i].reading_value
      
        try:
            diff = float(curr) - float(prev)
            if diff >= 0:
                consumptions.append(diff)
        except:
            continue

    if not consumptions:
        return False, "The consumption cannot be computed. Invalid data!"

    current_consumption = consumptions[-1]
    history = consumptions[:-1]

    if len(history) < 3:
         return False, "Data history is too short."

    # 3. Calcul Statistici
    try:
        mean = statistics.mean(history)          
        stdev = statistics.stdev(history) 
    except:
        return False, "Statistics calculation error."

    # Threshold: Media + 3 * Deviația
    threshold = mean + (3 * stdev)

    # Prag minim de siguranță (să nu dea alertă la 0.001 mc)
    if threshold < 1.0: 
        threshold = 1.0

    print(f"Actual consumption: {current_consumption:.2f} | Limit: {threshold:.2f}")

    if current_consumption > threshold:
        return True, f"ALERT! Abnormal consumption: {current_consumption:.2f} m³"
    
    return False, "Normal consumption."
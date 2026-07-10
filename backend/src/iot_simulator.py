import json
import os
import time
import random
from datetime import datetime

IOT_DATA_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "iot_data.json")
)


def simulate_iot_data():
    print(f"Starting IoT SCADA Simulator. Writing to {IOT_DATA_FILE}")

    equipment_state = {
        "P-101": {"vibration_mms": 2.5, "temp_c": 65.0, "status": "NORMAL"},
        "C-201": {"vibration_mms": 1.2, "temp_c": 45.0, "status": "NORMAL"},
        "E-301": {"vibration_mms": 0.5, "temp_c": 120.0, "status": "NORMAL"},
    }

    # We want P-101 to slowly degrade into a critical vibration state over time
    tick = 0
    history = {eq: [] for eq in equipment_state}
    CRITICAL_VIB_THRESHOLD = 12.0

    while True:
        tick += 1

        # Add random noise
        for eq in equipment_state:
            equipment_state[eq]["temp_c"] += random.uniform(-0.5, 0.5)

            if eq == "P-101":
                # P-101 is degrading
                equipment_state[eq]["vibration_mms"] += random.uniform(-0.1, 0.4)
                if equipment_state[eq]["vibration_mms"] > 8.0:
                    equipment_state[eq]["status"] = "WARNING"
                if equipment_state[eq]["vibration_mms"] > CRITICAL_VIB_THRESHOLD:
                    equipment_state[eq]["status"] = "CRITICAL"
            else:
                equipment_state[eq]["vibration_mms"] += random.uniform(-0.1, 0.1)

            # Clamp values
            if equipment_state[eq]["vibration_mms"] < 0:
                equipment_state[eq]["vibration_mms"] = 0.1

            # Maintain history for prediction
            history[eq].append(equipment_state[eq]["vibration_mms"])
            if len(history[eq]) > 10:
                history[eq].pop(0)

            # Calculate prediction (linear extrapolation)
            if len(history[eq]) >= 5:
                delta = history[eq][-1] - history[eq][0]
                rate_per_sec = delta / len(history[eq])
                if (
                    rate_per_sec > 0.01
                    and equipment_state[eq]["vibration_mms"] < CRITICAL_VIB_THRESHOLD
                ):
                    time_to_crit = (
                        CRITICAL_VIB_THRESHOLD - equipment_state[eq]["vibration_mms"]
                    ) / rate_per_sec
                    equipment_state[eq]["predicted_time_to_critical_sec"] = round(
                        time_to_crit, 1
                    )
                else:
                    equipment_state[eq]["predicted_time_to_critical_sec"] = -1

        payload = {
            "timestamp": datetime.now().isoformat(),
            "equipment": equipment_state,
        }

        # Write to JSON safely
        with open(IOT_DATA_FILE, "w") as f:
            json.dump(payload, f, indent=4)

        time.sleep(1)


if __name__ == "__main__":
    simulate_iot_data()

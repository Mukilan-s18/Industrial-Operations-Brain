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
                if equipment_state[eq]["vibration_mms"] > 12.0:
                    equipment_state[eq]["status"] = "CRITICAL"
            else:
                equipment_state[eq]["vibration_mms"] += random.uniform(-0.1, 0.1)

            # Clamp values
            if equipment_state[eq]["vibration_mms"] < 0:
                equipment_state[eq]["vibration_mms"] = 0.1

        payload = {
            "timestamp": datetime.now().isoformat(),
            "equipment": equipment_state,
        }

        # Write to JSON safely
        temp_file = IOT_DATA_FILE + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(payload, f, indent=4)
        os.replace(temp_file, IOT_DATA_FILE)

        time.sleep(1)


if __name__ == "__main__":
    simulate_iot_data()

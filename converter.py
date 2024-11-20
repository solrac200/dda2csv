import struct
import csv
import os

def parse_binary_to_csv(input_file, output_file):
    # Define constants
    offset = 1494
    regular_entry_size = 31
    extended_entry_size = 36

    # Define headers for the CSV
    csv_headers = [
        "Time", "EngineSpeed", "Pedal", "TractionControl", "VehicleSpeed", "Gear",
        "Altitude", "Longitude", "Latitude", "EngineTemperature", "Distance", "Lap",
        "LeanAngle"
    ]

    # Define unpacking format strings
    regular_entry_format = "<2H B H B 2H 2H B B H B H 2i"
    extended_entry_format = "<2H B H B 2H 2H B B H B B H B H 2i B"

    # Initialize variables
    time = 0.0  # Time starts at 0 seconds
    combined_entries = []

    with open(input_file, "rb") as f:
        # Skip the offset
        f.seek(offset)
        entry_counter = 0

        prev_extended = None  # To hold the last extended entry for interpolation

        while True:
            # Determine the entry type and size
            if entry_counter % 10 == 9:  # Every 10th entry is extended
                entry_size = extended_entry_size
                format_str = extended_entry_format
            else:
                entry_size = regular_entry_size
                format_str = regular_entry_format

            # Read the next block of bytes
            data = f.read(entry_size)
            if not data or len(data) < entry_size:
                break  # End of file

            # Unpack the data
            entry_values = struct.unpack(format_str, data)
            regular = None
            # Parse the data based on type
            if entry_counter % 10 == 9:  # Extended entry
                extended = {
                    "RPM 1": entry_values[0],
                    "RPM 2": entry_values[1],
                    "Throttle": entry_values[2],
                    "Lean": entry_values[3],
                    "DTC": entry_values[4],
                    "RPM 3": entry_values[5],
                    "RPM 4": entry_values[6],
                    "Speed": entry_values[7],
                    "RPM 5": entry_values[8],
                    "Temp": entry_values[9],
                    "Throttle 2": entry_values[10],
                    "Distance": entry_values[11],
                    "Lap": entry_values[12],
                    "Gear": entry_values[13],
                    "Lean 2": entry_values[14],
                    "DTC 2": entry_values[15],
                    "Altitude": entry_values[16],
                    "Longitude": entry_values[17],  # Longitude comes first
                    "Latitude": entry_values[18],   # Latitude comes second
                }
                prev_extended = extended
                regular = extended
            else:  # Regular entry
                regular = {
                    "RPM 1": entry_values[0],
                    "RPM 2": entry_values[1],
                    "Throttle": entry_values[2],
                    "Lean": entry_values[3],
                    "DTC": entry_values[4],
                    "RPM 3": entry_values[5],
                    "RPM 4": entry_values[6],
                    "Speed": entry_values[7],
                    "RPM 5": entry_values[8],
                    "Throttle 2": entry_values[9],
                    "Gear": entry_values[10],
                    "Lean 2": entry_values[11],
                    "DTC 2": entry_values[12],
                    "Altitude": entry_values[13],
                    "Longitude": entry_values[14],  # Longitude comes first
                    "Latitude": entry_values[15],   # Latitude comes second
                }

            # Generate RPM entries with alternating updates for 0.05s fields
            for i, rpm_key in enumerate(["RPM 1", "RPM 2", "RPM 3", "RPM 4", "RPM 5"]):
                rpm_time = time + i * 0.02

                # Alternate fields updated at 0.05s
                is_first_half = i % 2 == 0  # True for 0.00, 0.04, etc., False for 0.02, 0.06, etc.

                # Calculate LeanAngle
                lean_value = regular["Lean"] if is_first_half else regular["Lean 2"]
                lean_angle = round(0.05493 * lean_value - 449.931, 2)

                entry = {
                    "Time": round(rpm_time, 3),
                    "EngineSpeed": regular[rpm_key],
                    "Pedal": round((regular["Throttle"] if is_first_half else regular["Throttle 2"]) / 2, 1),
                    "TractionControl": regular["DTC"] if is_first_half else regular["DTC 2"],
                    "VehicleSpeed": regular["Speed"] / 16,  # Divided by 2^4
                    "Gear": regular["Gear"],  # Updated at 0.1s
                    "Altitude": round(regular["Altitude"] / 10, 1),  # Updated at 0.1s
                    "Longitude": round(regular["Longitude"] / 1_000_000, 6),  # Divide by 1,000,000
                    "Latitude": round(regular["Latitude"] / 1_000_000, 6),  # Divide by 1,000,000
                    "EngineTemperature": (prev_extended["Temp"] - 40) if prev_extended else None,
                    "Distance": prev_extended["Distance"] if prev_extended else None,
                    "Lap": prev_extended["Lap"] if prev_extended else 0,
                    "LeanAngle": lean_angle,
                }
                combined_entries.append(entry)

            time += 0.1  # Increment time by 0.1 seconds per regular entry
            entry_counter += 1

    # Write to CSV
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(combined_entries)

    print(f"CSV file written to {os.path.abspath(output_file)}")

# Usage example:
parse_binary_to_csv("example.dda", "output.csv")

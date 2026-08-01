import csv
import json
import re
from pprint import pprint
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_DIR = BASE_DIR / "csv"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

CSV_DIR.mkdir(parents=True, exist_ok=True)

def load_cases():
    groups = defaultdict(list)

    for output_path in sorted(OUTPUT_DIR.glob("output_*.json")):
        case_id = output_path.stem.removeprefix("output_")
        input_path = INPUT_DIR / f"input_{case_id}.json"

        input_data = load_json(input_path)
        result = load_json(output_path)



    return groups

groups = defaultdict(list)

output_json_paths = sorted(OUTPUT_DIR.glob("output_*.json"))
for output_json_path in output_json_paths:
    case_id = output_json_path.stem.removeprefix("output_")
    input_json_path = INPUT_DIR / f"input_{case_id}.json"

    with input_json_path.open("r", encoding="utf-8") as f:
        input_data = json.load(f)
    
    with output_json_path.open("r", encoding="utf-8") as f:
        result = json.load(f)

    oxide_values = tuple(
        sorted(
            (oxide, float(value))
            for oxide, value in input_data["oxides_mass"].items()
        )
    )
    dNNO = float(input_data["delta_nno"])
    phase_symbols = tuple(input_data["phases"])
    group_key = (dNNO, phase_symbols, oxide_values)

    groups[group_key].append((input_data, result))
    groups[group_key].append((input_data, result))
    pprint(groups, sort_dicts=False)
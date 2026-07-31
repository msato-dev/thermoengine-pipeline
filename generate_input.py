import csv
import json
from pprint import pprint
from pathlib import Path

OXIDE_COLUMNS = (
    "SiO2",
    "TiO2",
    "Al2O3",
    "Fe2O3",
    "Cr2O3",
    "FeO",
    "MnO",
    "MgO",
    "NiO",
    "CoO",
    "CaO",
    "Na2O",
    "K2O",
    "P2O5",
    "H2O",
    "CO2",
)

def read_input(path):
    input_csv_path = Path(path)

    with input_csv_path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        rows = list(r)

    return rows

def output_input(inputdata, path):
    input_json_path = Path(path)

    with input_json_path.open("w", encoding="utf-8") as f:
        json.dump(inputdata, f, ensure_ascii=False, indent=2)

def convert_case(row):
    case_id = f"{int(row['ID']):06d}"
    temperature_K = float(row["T_C"]) + 273.15
    pressure_Pa = float(row["P_MPa"]) * 1e6
    delta_nno = float(row["dNNO"])
    phases = row["phases"].split(";")
    oxides_mass = {}
    for oxide in OXIDE_COLUMNS:
        oxides_mass[oxide] = float(row[oxide])

    case = {
        "case_id": case_id,
        "temperature_K": temperature_K,
        "pressure_Pa": pressure_Pa,
        "delta_nno": delta_nno,
        "phases": phases,
        "oxides_mass": oxides_mass,
    }
    return case
    
input_csv_path = "input.csv"
input_json_dir = Path("input")
input_json_dir.mkdir(parents=True, exist_ok="True")

rows = read_input(input_csv_path)

for row in rows:
    case = convert_case(row)
    #pprint(case, sort_dicts=False)
    input_json_path = input_json_dir / f"input_{case['case_id']}.json"
    output_input(case, input_json_path)
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
    case_id = int(row["ID"])
    T_K = float(row["T_C"]) + 273.15
    P_Pa = float(row["P_MPa"]) * 1e6
    dNNO = float(row["dNNO"])
    phases = row["phases"].split(";")
    oxides_mass = {}
    for oxide in OXIDE_COLUMNS:
        oxides_mass[oxide] = float(row[oxide])

    case = {
        "ID": case_id,
        "T_K": T_K,
        "P_Pa": P_Pa,
        "dNNO": dNNO,
        "phases": phases,
        "oxides_mass": oxides_mass,
    }

    # Normalize oxide compositions 100% with input H2O content.
    def _normalize_oxides_mass(oxides_mass):
        H2O = oxides_mass["H2O"]
        CO2 = oxides_mass["CO2"]
        volatile = H2O + CO2

        non_volatile_total = sum(
            value
            for oxide, value in oxides_mass.items()
            if oxide not in ("H2O", "CO2")
        )

        scale = (100.0 - volatile) / non_volatile_total

        oxides_normalized_mass = {
            oxide: value if oxide in ("H2O", "CO2") else scale * value
            for oxide, value in oxides_mass.items()
        }

        return oxides_normalized_mass
    
    case["oxides_mass"] = _normalize_oxides_mass(case["oxides_mass"])

    return case

def main():
    input_csv_path = "input.csv"
    input_json_dir = Path("input")
    input_json_dir.mkdir(parents=True, exist_ok=True)

    rows = read_input(input_csv_path)

    for row in rows:
        case = convert_case(row)
        #pprint(case, sort_dicts=False)
        input_json_path = input_json_dir / f"input_{int(row['ID']):06d}.json"
        output_input(case, input_json_path)

if __name__ == "__main__":
    main()
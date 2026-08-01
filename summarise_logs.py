import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
LOG_DIR = BASE_DIR / "log"
CSV_DIR = BASE_DIR / "csv"
CSV_PATH = CSV_DIR / "batch_log.csv"

COLUMNS = [
    "ID",
    "input",
    "output",
    "status",
    "timed_out",
    "elapsed_seconds",
    "T_C",
    "P_MPa",
    "delta_nno",
    "SiO2_mass",
    "H2O_mass",
]


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_log(path):
    header = {}
    result = {}
    section = "header"

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line == "--- worker output ---":
                section = "worker"
                continue

            if line == "--- batch result ---":
                section = "result"
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            if section == "header" and key in ("input", "output"):
                header[key] = value
            elif section == "result" and key in (
                "status",
                "timed_out",
                "elapsed_seconds",
            ):
                result[key] = value

    return header | result


def make_row(log_path):
    case_id_text = log_path.stem.removeprefix("log_")
    case_id = int(case_id_text)
    log_data = parse_log(log_path)

    input_name = log_data.get("input", f"input_{case_id_text}.json")
    output_name = log_data.get("output", f"output_{case_id_text}.json")
    input_data = load_json(INPUT_DIR / input_name)
    oxides_mass = input_data["oxides_mass"]

    return {
        "ID": case_id,
        "input": input_name,
        "output": output_name,
        "status": log_data.get("status", ""),
        "timed_out": log_data.get("timed_out", ""),
        "elapsed_seconds": log_data.get("elapsed_seconds", ""),
        "T_C": float(input_data["temperature_K"]) - 273.15,
        "P_MPa": float(input_data["pressure_Pa"]) / 1.0e6,
        "delta_nno": float(input_data["delta_nno"]),
        "SiO2_mass": float(oxides_mass["SiO2"]),
        "H2O_mass": float(oxides_mass["H2O"]),
    }


def main():
    CSV_DIR.mkdir(exist_ok=True)
    rows = [make_row(path) for path in LOG_DIR.glob("log_*.txt")]
    rows.sort(key=lambda row: row["ID"])

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{CSV_PATH.name}: {len(rows)} cases")


if __name__ == "__main__":
    main()
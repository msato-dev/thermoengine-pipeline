import csv
import json
import re
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
CSV_DIR = BASE_DIR / "csv"


PHASE_ALIASES = {
    "System": "system",
    "Liq": "liquid",
    "Liquid": "liquid",
    "Fsp": "fsp",
    "Feldspar": "fsp",
    "Ol": "ol",
    "Olivine": "ol",
    "Cpx": "cpx",
    "Clinopyroxene": "cpx",
    "Opx": "opx",
    "Orthopyroxene": "opx",
    "Hbl": "hbl",
    "Hornblende": "hbl",
    "SplS": "spls",
    "Spinel": "spls",
    "Rhom": "rhom",
    "RhombohedralOxide": "rhom",
    "Ap": "ap",
    "Apatite": "ap",
    "Qz": "qz",
    "Quartz": "qz",
    "Bt": "bt",
    "Biotite": "bt",
    "Grt": "grt",
    "Garnet": "grt",
    "H2O": "h2o",
    "Water": "h2o",
}


PROPERTY_COLUMNS = {
    "Mass": "mass_g",
    "GibbsFreeEnergy": "gibbs_free_energy_J",
    "Enthalpy": "enthalpy_J",
    "Entropy": "entropy_J_per_K",
    "HeatCapacity": "heat_capacity_J_per_K",
    "DcpDt": "dcp_dt_J_per_K2",
    "Volume": "volume_J_per_bar",
    "DvDt": "dv_dt_J_per_bar_K",
    "DvDp": "dv_dp_J_per_bar2",
    "D2vDt2": "d2v_dt2_J_per_bar_K2",
    "D2vDtDp": "d2v_dt_dp_J_per_bar2_K",
    "D2vDp2": "d2v_dp2_J_per_bar3",
    "Density": "density_g_per_cm3",
    "Alpha": "alpha_per_K",
    "Beta": "beta_per_bar",
    "K": "bulk_modulus_GPa",
    "K'": "bulk_modulus_pressure_derivative",
    "Gamma": "gamma",
}


SPECIFIC_PROPERTIES = {
    "GibbsFreeEnergy": "gibbs_free_energy_J_per_kg",
    "Enthalpy": "enthalpy_J_per_kg",
    "Entropy": "entropy_J_per_kg_K",
    "HeatCapacity": "heat_capacity_J_per_kg_K",
    "DcpDt": "dcp_dt_J_per_kg_K2",
}


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sanitize_name(name):
    return re.sub(r"[^0-9A-Za-z]+", "_", str(name)).strip("_")


def phase_prefix(phase_name):
    return PHASE_ALIASES.get(phase_name, sanitize_name(phase_name).lower())


def property_value(section, property_name):
    value = section[property_name]
    return float(value[0])


def add_property(row, prefix, property_name, value, unit, mass_g):
    column_name = PROPERTY_COLUMNS.get(property_name)

    if column_name is None:
        unit_name = sanitize_name(unit) if unit else ""
        column_name = sanitize_name(property_name).lower()
        if unit_name:
            column_name += "_" + unit_name

    row[f"{prefix}_{column_name}"] = value

    if property_name in SPECIFIC_PROPERTIES:
        mass_kg = mass_g / 1000.0
        row[f"{prefix}_{SPECIFIC_PROPERTIES[property_name]}"] = value / mass_kg

    if property_name == "Mass":
        row[f"{prefix}_mass_kg"] = value / 1000.0
    elif property_name == "Volume":
        row[f"{prefix}_volume_m3"] = value * 1.0e-5
    elif property_name == "Density":
        row[f"{prefix}_density_kg_per_m3"] = value * 1000.0


def add_nested_values(row, prefix, values):
    for name, value in values.items():
        column_name = f"{prefix}_{sanitize_name(name)}"

        if isinstance(value, dict):
            add_nested_values(row, column_name, value)
        else:
            row[column_name] = value


def add_section(row, phase_name, section):
    prefix = phase_prefix(phase_name)
    mass_g = property_value(section, "Mass")

    for name, value in section.items():
        if isinstance(value, list) and len(value) == 2:
            add_property(row, prefix, name, float(value[0]), value[1], mass_g)
        elif name == "oxide_mass":
            for oxide, oxide_value in value.items():
                row[f"{prefix}_{oxide}"] = oxide_value
        elif name in ("endmember_mole_fraction", "component_mole_fraction"):
            for component, component_value in value.items():
                row[f"{prefix}_{sanitize_name(component)}"] = component_value
        elif isinstance(value, dict):
            add_nested_values(row, f"{prefix}_{sanitize_name(name)}", value)
        else:
            row[f"{prefix}_{sanitize_name(name)}"] = value


def group_key(input_data):
    oxide_values = tuple(
        sorted(
            (oxide, float(value))
            for oxide, value in input_data["oxides_mass"].items()
        )
    )
    return float(input_data["delta_nno"]), oxide_values


def load_cases():
    groups = defaultdict(list)

    for output_path in sorted(OUTPUT_DIR.glob("output_*.json")):
        case_id = output_path.stem.removeprefix("output_")
        input_path = INPUT_DIR / f"input_{case_id}.json"

        input_data = load_json(input_path)
        result = load_json(output_path)
        groups[group_key(input_data)].append((input_data, result))

    return groups


def make_row(input_data, result):
    row = {
        "temperature_K": float(input_data["temperature_K"]),
        "pressure_Pa": float(input_data["pressure_Pa"]),
        "case_id": input_data["case_id"],
        "delta_nno": float(input_data["delta_nno"]),
    }

    for oxide, value in input_data["oxides_mass"].items():
        row[f"input_{oxide}"] = value

    system = result["System"]
    system_mass_g = property_value(system, "Mass")
    system_volume = property_value(system, "Volume")
    add_section(row, "System", system)

    phase_names = []

    for phase_name, section in result.items():
        if phase_name in ("State", "System"):
            continue

        prefix = phase_prefix(phase_name)
        phase_mass_g = property_value(section, "Mass")
        phase_volume = property_value(section, "Volume")

        row[f"{prefix}_mass_fraction"] = phase_mass_g / system_mass_g
        row[f"{prefix}_volume_fraction"] = phase_volume / system_volume
        add_section(row, phase_name, section)
        phase_names.append(prefix)

    return row, phase_names


def prepare_rows(cases):
    rows = []
    all_phase_names = set()

    for input_data, result in cases:
        row, phase_names = make_row(input_data, result)
        rows.append(row)
        all_phase_names.update(phase_names)

    rows.sort(key=lambda row: (row["temperature_K"], row["pressure_Pa"]))

    for row in rows:
        for prefix in all_phase_names:
            row.setdefault(f"{prefix}_mass_fraction", 0.0)
            row.setdefault(f"{prefix}_volume_fraction", 0.0)
            row.setdefault(f"{prefix}_mass_g", 0.0)
            row.setdefault(f"{prefix}_mass_kg", 0.0)
            row.setdefault(f"{prefix}_volume_J_per_bar", 0.0)
            row.setdefault(f"{prefix}_volume_m3", 0.0)

    return rows


def get_columns(rows):
    first_columns = [
        "temperature_K",
        "pressure_Pa",
        "case_id",
        "delta_nno",
    ]
    columns = list(first_columns)

    for row in rows:
        for column in row:
            if column not in columns:
                columns.append(column)

    return columns


def write_csv(path, rows):
    columns = get_columns(rows)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    groups = load_cases()

    for group_number, group in enumerate(sorted(groups.items()), start=1):
        _, cases = group
        rows = prepare_rows(cases)
        csv_path = CSV_DIR / f"thermoengine_{group_number:04d}.csv"
        write_csv(csv_path, rows)
        print(f"{csv_path.name}: {len(rows)} cases")


if __name__ == "__main__":
    main()

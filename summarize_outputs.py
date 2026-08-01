import csv
import json
from pathlib import Path

class MineralCompositionCalculator:
    COMPOSITION_NAMES = {
        "Fsp": "An",
        "Cpx": "Mg_number",
        "Opx": "Mg_number",
        "Ol": "Fo",
    }

    OXIDE_MOLAR_MASSES = {
        "FeO": 71.844,
        "Fe2O3": 159.688,
        "MgO": 40.304,
        "CaO": 56.077,
        "Na2O": 61.979,
        "K2O": 94.196,
    }

    def __init__(self, oxides_mass):
        self.oxides_mass = oxides_mass

    # Switch calculation phases
    def calculate(self, phase_name):
        if phase_name == "Fsp":
            return self._calculate_anorthite()

        if phase_name in ("Cpx", "Opx"):
            return self._calculate_mg_number()

        if phase_name == "Ol":
            return self._calculate_forsterite()

    def _calculate_anorthite(self):
        # Load oxides mass
        CaO_mass = float(self.oxides_mass.get("CaO", 0.0))
        Na2O_mass = float(self.oxides_mass.get("Na2O", 0.0))
        K2O_mass = float(self.oxides_mass.get("K2O", 0.0))

        # Load oxides molar mass
        CaO_molar_mass = self.OXIDE_MOLAR_MASSES["CaO"]
        Na2O_molar_mass = self.OXIDE_MOLAR_MASSES["Na2O"]
        K2O_molar_mass = self.OXIDE_MOLAR_MASSES["K2O"]

        # Calculate anorthite content
        Ca = CaO_mass / CaO_molar_mass
        Na = 2.0 * Na2O_mass / Na2O_molar_mass
        K = 2.0 * K2O_mass / K2O_molar_mass

        total = Ca + Na + K

        if total == 0.0:
            return None

        An = 100.0 * Ca / total
        return An

    def _calculate_mg_number(self):
        # Load oxides mass
        FeO_mass = float(self.oxides_mass.get("FeO", 0.0))
        Fe2O3_mass = float(self.oxides_mass.get("Fe2O3", 0.0))
        MgO_mass = float(self.oxides_mass.get("MgO", 0.0))

        # Load oxides molar mass
        FeO_molar_mass = self.OXIDE_MOLAR_MASSES["FeO"]
        Fe2O3_molar_mass = self.OXIDE_MOLAR_MASSES["Fe2O3"]
        MgO_molar_mass = self.OXIDE_MOLAR_MASSES["MgO"]

        # Calculate Mg number
        Fe_ferrous = FeO_mass / FeO_molar_mass
        Fe_ferric = 2.0 * Fe2O3_mass / Fe2O3_molar_mass
        Mg = MgO_mass / MgO_molar_mass

        total = Fe_ferrous + Fe_ferric + Mg
        if total == 0:
            return None

        Mg_num = 100 * Mg / total
        return Mg_num

    def _calculate_forsterite(self):
        # Load oxides mass
        FeO_mass = float(self.oxides_mass.get("FeO", 0.0))
        MgO_mass = float(self.oxides_mass.get("MgO", 0.0))

        # Load oxides molar mass
        FeO_molar_mass = self.OXIDE_MOLAR_MASSES["FeO"]
        MgO_molar_mass = self.OXIDE_MOLAR_MASSES["MgO"]

        # Calculate Mg number
        Fe_ferrous = FeO_mass / FeO_molar_mass
        Mg = MgO_mass / MgO_molar_mass

        total = Fe_ferrous + Mg
        if total == 0:
            return None

        Fo = 100 * Mg / total
        return Fo



BASE_DIR = Path(__file__).resolve().parent
CSV_DIR = BASE_DIR / "csv"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

PHASE_ALIASES = {
    "System": "System",
    "Liq": "Liq",
    "Liquid": "Liq",
    "Fsp": "Fsp",
    "Feldspar": "Fsp",
    "Ol": "Ol",
    "Olivine": "Ol",
    "Cpx": "Cpx",
    "Clinopyroxene": "Cpx",
    "Opx": "Opx",
    "Orthopyroxene": "Opx",
    "Hbl": "Hbl",
    "Hornblende": "Hbl",
    "SplS": "SplS",
    "Spinel": "SplS",
    "Rhom": "Rhom",
    "RhombohedralOxide": "Rhom",
    "Ap": "Ap",
    "Apatite": "Ap",
    "Qz": "Qz",
    "Quartz": "Qz",
    "Bt": "Bt",
    "Biotite": "Bt",
    "Grt": "Grt",
    "Garnet": "Grt",
    "H2O": "H2O",
    "Water": "H2O",
}

PROPERTY_COLUMNS = {
    "Mass": "mass_g",
    "Enthalpy": "enthalpy_J",
    "HeatCapacity": "heat_capacity_J_per_K",
    "Volume": "volume_J_per_bar",
    "Density": "density_g_per_cm3",
    "Beta": "beta_per_bar",
}

def prepare_rows(input_dir, output_dir):
    def _load_json(path):
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    
    def _make_row(result):
        def _add_section(row, phase, prefix, section):
            for property_name, column_name in PROPERTY_COLUMNS.items():
                row[f"{prefix}_{column_name}"] = float(section[property_name][0])
            
            if "oxide_mass" in section and phase == "Liq":
                for oxide, value in section["oxide_mass"].items():
                    row[f"{prefix}_{oxide}"] = float(value)
            
            elif (
                "oxide_mass" in section
                and phase in MineralCompositionCalculator.COMPOSITION_NAMES
            ):
                calculator = MineralCompositionCalculator(section["oxide_mass"])
                composition_name = calculator.COMPOSITION_NAMES[phase]
                row[f"{prefix}_{composition_name}"] = calculator.calculate(phase)


        state = result["State"]
        row = {
            "case_id": int(state["case_id"]),
            "temperature_K": float(state["temperature_K"]),
            "pressure_MPa": float(state["pressure_MPa"]),
        }

        # Load system properties
        system = result["System"]
        system_mass_g = float(system["Mass"][0])
        system_volume = float(system["Volume"][0])
        _add_section(row, "System", "System", system)

        phase_names = []

        # Load phase properties
        for phase_name, section in result.items():
            if phase_name in ("State", "System"):
                continue

            name, separator, number = phase_name.partition("_")
            phase = PHASE_ALIASES.get(name, name)
            prefix = f"{phase}_{number}" if separator else phase

            phase_mass_g = float(section["Mass"][0])
            phase_volume = float(section["Volume"][0])

            row[f"{prefix}_mass_fraction"] = phase_mass_g / system_mass_g
            row[f"{prefix}_volume_fraction"] = phase_volume / system_volume
            _add_section(row, phase, prefix, section)
            phase_names.append(prefix)

        return row, phase_names

    rows = []
    all_phase_names = set()

    for output_path in sorted(output_dir.glob("output_*.json")):
        output_data = _load_json(output_path)
        row, phase_names = _make_row(output_data)
        rows.append(row)
        all_phase_names.update(phase_names)
    
    rows.sort(key=lambda row: (row["case_id"], row["temperature_K"], row["pressure_MPa"]))

    for row in rows:
        for prefix in sorted(all_phase_names):
            row.setdefault(f"{prefix}_mass_fraction", 0.0)
            row.setdefault(f"{prefix}_volume_fraction", 0.0)
            row.setdefault(f"{prefix}_mass_g", 0.0)
            row.setdefault(f"{prefix}_volume_J_per_bar", 0.0)

    return rows

def main():
    input_dir = Path("./input")
    output_dir = Path("./output")

    rows = prepare_rows(input_dir, output_dir)

    csv_dir = Path("./csv")
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_path = csv_dir / "output.csv"

    columns = list(["case_id", "temperature_K", "pressure_MPa"])
    for row in rows:
        for column in row:
            if column not in columns:
                columns.append(column)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
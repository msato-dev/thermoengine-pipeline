import json
from pathlib import Path
from pprint import pprint

import numpy as np
from thermoengine import equilibrate, model, phases
from thermoengine.chemistry import OxideWtComp

ELEMENTS = (
    "H",
    "C",
    "O",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "K",
    "Ca",
    "Ti",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
)

PROPERTY_NAMES = (
    "Mass",
    "GibbsFreeEnergy",
    "Enthalpy",
    "Entropy",
    "HeatCapacity",
    "DcpDt",
    "Volume",
    "DvDt",
    "DvDp",
    "D2vDt2",
    "D2vDtDp",
    "D2vDp2",
    "Density",
    "Alpha",
    "Beta",
    "K",
    "K'",
    "Gamma",
    )

def load_input_json(path):
    # Load input file
    with path.open("r", encoding="utf-8") as f:
        input_data = json.load(f)
    return input_data

def run_equilibrium(input_data):
    # Extract input parameters
    temperature_K = input_data["temperature_K"]
    pressure_bar = input_data["pressure_Pa"] / 1e5
    delta_nno = input_data["delta_nno"]
    phase_symbols = input_data["phases"]
    oxides_mass = input_data["oxides_mass"]

    # Convert oxide composition (mass%) to element data
    def _convert_oxide_mass_to_elements(oxides_mass):
        oxides_comp = OxideWtComp(**oxides_mass)
        element_data = oxides_comp.elem_comp.all_data

        bulk_comp = np.array(
            [float(element_data[element]) for element in ELEMENTS],
            dtype=float,
        )
        return bulk_comp

    bulk_comp = _convert_oxide_mass_to_elements(oxides_mass)

    # Set phase model
    def _generate_equilibrator(phase_symbols):
        database = model.Database(database="Berman", liq_mod="v1.2", calib=False)

        phase_models = [
            phases.PurePhase("WaterMelts", "H2O", calib=False)
            if phase_symbol == "H2O"
            else database.get_phase(phase_symbol)
            for phase_symbol in phase_symbols
        ]

        equilibrator = equilibrate.Equilibrate(ELEMENTS, phase_models)
        return equilibrator

    equil = _generate_equilibrator(phase_symbols)

    # Execute equilibrium calculation
    state = equil.execute(
        temperature_K,
        pressure_bar,
        bulk_comp=bulk_comp,
        con_deltaNNO=delta_nno,
        debug=0,
        stats=False
        )
    return state

def generate_result(input_data, state):
    def _get_states(input_data, state):
        states = {
            "case_id": input_data["case_id"],
            "temperature_K": float(state.temperature),
            "pressure_MPa": float(state.pressure) / 10.0
        }
        return states

    def _get_properties(state, phase_name):
        properties = {}
        for prop in PROPERTY_NAMES:
            value, unit = state.properties(phase_name, prop, units=True)
            properties[prop] = [value, unit]
        return properties
    
    def _get_oxides_mass(state, phase_name):
        phase_comps = state.oxide_comp(
            phase_name,
            output="wt%",
            prune_list=False,
        )

        oxides_mass = {
            str(oxide): float(value)
            for oxide, value in phase_comps.items()
        }
        return oxides_mass

    result = {}
    result["State"] = _get_states(input_data, state)
    result["System"] = _get_properties(state, "System")

    def _get_stable_phase_names(state):
        stable_phase_names = [
            phase_name
            for phase_name in state.phase_d
            if state.tot_grams_phase(phase_name) > 0.0
        ]
        return stable_phase_names
    
    stable_phase_names = _get_stable_phase_names(state)
    for phase_name in stable_phase_names:
        result[phase_name] = _get_properties(state, phase_name)
        result[phase_name]["oxide_mass"] = _get_oxides_mass(state, phase_name)
    
    return result

def export_result_json(result, path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def main():
    # Set input and output json path
    input_json_path = Path("input/input_000003.json")
    input_data = load_input_json(input_json_path)
    output_json_dir = Path("output")
    output_json_path = output_json_dir / f"out_{input_data['case_id']}.json"

    # Run equilibrium calculation
    state = run_equilibrium(input_data)
    result = generate_result(input_data, state)
    export_result_json(result, output_json_path)

    # pprint(input_data, sort_dicts=False)
    # state.print_state()
    # pprint(result, sort_dicts=False)

if __name__ == "__main__":
    main()
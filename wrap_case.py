import argparse
import os
from pathlib import Path

import run_thermoengine

def run_case(input_path, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Execute functions within run_thermoengine.py
    input_data = run_thermoengine.load_input_json(input_path)
    state = run_thermoengine.run_equilibrium(input_data)
    result = run_thermoengine.generate_result(input_data, state)

    tmp_output_path = output_path.with_name(
        f".{output_path.name}.{os.getpid()}.tmp"
    )
    tmp_output_path.unlink(missing_ok=True)

    try:
        run_thermoengine.export_result_json(result, tmp_output_path)
        tmp_output_path.replace(output_path)
    finally:
        tmp_output_path.unlink(missing_ok=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", type=Path)
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()
    run_case(
        args.input_path.resolve(),
        args.output_path.resolve()
    )

if __name__ == "__main__":
    main()
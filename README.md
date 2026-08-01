# thermoengine-pipeline
A wrapper for running phase-equilibrium calculations with ThermoEngine.

## Overview
This repository is under development and may contain unexpectd bugs.

## Requirements
This repository has been developed under following enviornments:
- Ubuntu 24.04 LTS on WSL2 (Windows 11 Pro 25H2)
- Docker Desktop
- [ThermoEngine](https://gitlab.com/ENKI-portal/ThermoEngine)


## Usage
- Generate input json files
- Run batch calculations
- Aggregate calculation output json files and log files

```mermaid
flowchart TD
    A["generate_input.py"]
    A -->|generate input .json files| B["run_batch.py"]

    subgraph CASE1["Thermodynamic calculation: one subprocess per case"]
        C["wrap_case.py"]
        -->|call ThermoEngine modules | D["run_thermoengine.py"]
    end

    B -->|launch subprocess| C

    subgraph CASE2["summarise outputs"]
        D -->|output result .json files| E["summarise_outputs.py"]
        D -->|output log files| F["summarise_logs.py"]
    end
```
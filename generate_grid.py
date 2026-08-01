import csv
from pathlib import Path

Ts_C = range(1200, 599, -10)
Ps_MPa = range(50, 601, 50)
H2Os_mass = (0.5, 1.0, 2.0, 3.0, 4.0, 5.0)

def generate_grid():
    rows = []

    for H2O_mass in H2Os_mass:
        for P_MPa in Ps_MPa:
            for T_C in Ts_C:
            
                rows.append(
                    {
                        "T_C": T_C,
                        "P_MPa": P_MPa,
                        "H2O": H2O_mass,
                    }
                )
    return rows

def main():
    rows = generate_grid()

    output_csv_path = Path("input_grid.csv")
    with output_csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=("T_C", "P_MPa", "H2O"))
        w.writeheader()
        w.writerows(rows)

if __name__ == "__main__":
    main()
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "log"
WRAPPER_PATH = BASE_DIR / "wrap_case.py"

TIMEOUT_SECONDS = 600
TERMINATE_GRACE_SECONDS = 5


def stop_process_group(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return

    try:
        process.wait(timeout=TERMINATE_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return

        try:
            process.wait(timeout=TERMINATE_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            pass


def run_case(input_path):
    case_id = input_path.stem.removeprefix("input_")
    output_path = OUTPUT_DIR / f"output_{case_id}.json"
    log_path = LOG_DIR / f"log_{case_id}.txt"
    command = [
        sys.executable,
        "-u",
        str(WRAPPER_PATH),
        str(input_path),
        str(output_path),
    ]

    output_path.unlink(missing_ok=True)
    start_time = time.monotonic()

    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"input={input_path.name}\n")
        log_file.write(f"output={output_path.name}\n")
        log_file.write(f"timeout_seconds={TIMEOUT_SECONDS}\n")
        log_file.write("--- worker output ---\n")
        log_file.flush()

        try:
            process = subprocess.Popen(
                command,
                cwd=BASE_DIR,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except OSError as error:
            status = "error"
            returncode = None
            log_file.write(f"{type(error).__name__}: {error}\n")
        else:
            try:
                returncode = process.wait(timeout=TIMEOUT_SECONDS)
                if returncode == 0 and output_path.exists():
                    status = "success"
                else:
                    status = "error"
            except subprocess.TimeoutExpired:
                status = "timeout"
                stop_process_group(process)
                returncode = process.returncode
                output_path.unlink(missing_ok=True)
            except KeyboardInterrupt:
                stop_process_group(process)
                raise

        elapsed_seconds = time.monotonic() - start_time
        log_file.write("\n--- batch result ---\n")
        log_file.write(f"status={status}\n")
        log_file.write(f"timed_out={str(status == 'timeout').lower()}\n")
        log_file.write(f"returncode={returncode}\n")
        log_file.write(f"elapsed_seconds={elapsed_seconds:.3f}\n")

    return status, elapsed_seconds


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)

    for input_path in sorted(INPUT_DIR.glob("input_*.json")):
        status, elapsed_seconds = run_case(input_path)
        print(f"{input_path.name}: {status} ({elapsed_seconds:.1f} s)")


if __name__ == "__main__":
    main()
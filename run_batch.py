import json
import os
import signal
import subprocess
import sys
import time
import uuid
from concurrent.features import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

TIMEOUT_SECONDS = 600.0
TERMINATE_GRACE_SECONDS = 5.0

# Sequential or parallel runs
MAX_PROCESSES = 1

cases = discover_cases()
import subprocess
import re
from typing import List, Tuple, Optional, Dict

def list_power_plans() -> tuple[List[Tuple[str, str, bool]], str]:
    """
    Retrieve all power plans using powercfg /list and parse GUID, name, and active status.
    Returns (list of (guid, name, is_active), raw_stdout).
    """
    try:
        result = subprocess.run(
            ["powercfg", "/list"],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout
        plans = re.findall(r"Power Scheme GUID:\s*([\w-]+)\s*\(\s*([^)]+)\s*\)(\s*\*)?", output)
        parsed_plans = []
        for guid, name, active_marker in plans:
            is_active = bool(active_marker)
            parsed_plans.append((guid.strip(), name.strip(), is_active))
        return parsed_plans, output
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to list power plans: {e.stderr}")

def get_active_plan() -> tuple[Optional[str], str]:
    """
    Get the GUID of the currently active power plan using powercfg /getactivescheme.
    Returns (GUID or None, raw_stdout).
    """
    try:
        result = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout
        match = re.search(r"Power Scheme GUID:\s*([\w-]+)", output)
        guid = match.group(1).strip() if match else None
        return guid, output
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get active plan: {e.stderr}")

def set_active_plan(guid: str) -> tuple[str, str]:
    """
    Set the active power plan using powercfg /setactive <GUID>.
    Returns (stdout.strip(), stderr if any else '').
    """
    try:
        result = subprocess.run(
            ["powercfg", "/setactive", guid],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to set active plan: {e.stderr}")
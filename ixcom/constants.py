import json
from pathlib import Path

json_files = Path(__file__).resolve().parent / "json-files"

defines_dir = json_files / "defines"

defines_raw = {"defines":[]}
for j in sorted(defines_dir.glob("*.json")):
    with open(j,"r") as f:
        defines_raw["defines"] += json.load(f)["defines"]

defines = {d["name"]:d["int_value"] for d in defines_raw["defines"]}
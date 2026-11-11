import json
import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from scripts.method_a_framework.config import FrameworkConfig
from scripts.method_a_framework.deck_builder import ProductionDeckBuilder

def main():
    cfg_path = "configs/method_a/five_hole_f1716_production.json"
    with open(cfg_path, "r") as f:
        data = json.load(f)

    cfg = FrameworkConfig(data)
    builder = ProductionDeckBuilder(cfg.paths["adapted_phys_inp"], cfg)
    builder.parse_physical_mesh()
    res = builder.build_deck(cfg.paths["production_inp"])
    print("SUCCESS: Production deck generated!")
    for k, v in res.items():
        print("  %s: %s" % (k, v))

if __name__ == "__main__":
    main()

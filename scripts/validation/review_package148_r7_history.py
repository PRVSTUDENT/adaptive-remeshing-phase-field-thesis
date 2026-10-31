"""Recompute all receiver GP transfers from authentic donor without writes."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.state_transfer.build_package146_147_transfer_deck import Package146To147DeckGenerator


def review():
    package = ROOT/'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r7'
    gen = Package146To147DeckGenerator(package, frozen_uel=package/'f42_mixed_uel.for')
    gen.verify_prerequisites()
    gen.load_donor_data()
    gen.initialize_meshes_and_mapper()
    projection = gen.execute_state_projection()
    with (package/'d_lower_bounds.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    checked = 0
    for row in rows:
        for gp in range(1, 5):
            expected = projection['target_gp_h'][int(row['element_id']), gp]
            assert float(row['h0_'+str(gp)]) == float('%.15e' % expected)
            checked += 1
    assert checked == len(projection['gp_map']) == 28224
    result = dict(schema=1, status='PASS', recomputed_history_mappings=checked,
                  source='Authentic Package146 donor to Package147 receiver',
                  operator='HOST_NEAREST_GP', gp_stats=projection['gp_stats'],
                  solver_executed=False)
    (ROOT/'results/validation/package148_r7_history_review.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    review()

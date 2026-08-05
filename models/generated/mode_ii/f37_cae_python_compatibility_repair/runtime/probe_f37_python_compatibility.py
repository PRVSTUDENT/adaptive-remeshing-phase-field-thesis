from __future__ import print_function
import os
import sys
import json
RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
if RUNTIME_DIR not in sys.path:
    sys.path.insert(0, RUNTIME_DIR)
from f37_runtime_compat import resolve_unique_repository_key

def repository(keys):
    return dict((key, object()) for key in keys)

def expect_type_failure(value, logical_name):
    try:
        resolve_unique_repository_key(value, logical_name, 'probe')
    except TypeError:
        return True
    return False

def main():
    audit = {'python_version': sys.version, 'normalization_method': 'str.lower', 'casefold_available': hasattr('', 'casefold'), 'casefold_used': False, 'compatibility_pass': False}
    try:
        audit['exact_case_passed'] = resolve_unique_repository_key(repository(['Part-1']), 'Part-1', 'probe')['resolved_key'] == 'Part-1'
        audit['uppercase_case_passed'] = resolve_unique_repository_key(repository(['PART-1']), 'Part-1', 'probe')['resolved_key'] == 'PART-1'
        audit['mixed_case_passed'] = resolve_unique_repository_key(repository(['pArT-1']), 'Part-1', 'probe')['resolved_key'] == 'pArT-1'
        try: resolve_unique_repository_key(repository(['Other']), 'Part-1', 'probe'); audit['zero_match_failure_passed'] = False
        except RuntimeError: audit['zero_match_failure_passed'] = True
        try: resolve_unique_repository_key(repository(['Part-1','PART-1']), 'Part-1', 'probe'); audit['ambiguous_match_failure_passed'] = False
        except RuntimeError: audit['ambiguous_match_failure_passed'] = True
        audit['non_repository_failure_passed'] = expect_type_failure([], 'Part-1')
        audit['compatibility_pass'] = all(audit[k] for k in ('exact_case_passed','uppercase_case_passed','mixed_case_passed','zero_match_failure_passed','ambiguous_match_failure_passed','non_repository_failure_passed'))
    finally:
        with open(os.environ.get('F37_PYTHON_COMPATIBILITY_AUDIT','EMBEDDED_PYTHON_COMPATIBILITY_AUDIT.json'), 'w') as handle: json.dump(audit, handle, indent=2)
    if not audit['compatibility_pass']: sys.exit(1)
if __name__ == '__main__': main()

from __future__ import print_function

try:
    STRING_TYPES = (basestring,)
except NameError:
    STRING_TYPES = (str,)

def normalize_repository_key(value):
    if not isinstance(value, STRING_TYPES):
        raise TypeError("Repository key must be a string; received {0}".format(type(value).__name__))
    return value.lower()

def resolve_unique_repository_key(repository, logical_name, repository_label):
    if not hasattr(repository, 'keys'):
        raise TypeError("Repository '{0}' does not provide keys()".format(repository_label))
    available_keys = list(repository.keys())
    normalized_name = normalize_repository_key(logical_name)
    matching_keys = [key for key in available_keys if normalize_repository_key(key) == normalized_name]
    if len(matching_keys) != 1:
        raise RuntimeError("Expected exactly one case-insensitive match for '{0}' in {1}; available keys={2}, matches={3}".format(logical_name, repository_label, available_keys, matching_keys))
    return {'requested_logical_name': logical_name, 'repository_label': repository_label, 'available_keys': available_keys, 'matching_keys': matching_keys, 'match_count': len(matching_keys), 'resolved_key': matching_keys[0], 'normalization_method': 'str.lower', 'lookup_contract_passed': True}

#!/usr/bin/env python
"""Write and immediately parse a small status JSON document.

Compatible with Python 2.7 and Python 3. Values use KEY=TYPE:VALUE where TYPE
is int, bool, null, json, or str. This avoids shell-generated JSON entirely.
"""
from __future__ import print_function

import argparse
import json
import os
import sys


def parse_value(raw):
    if ":" not in raw:
        return raw
    kind, value = raw.split(":", 1)
    if kind == "int":
        return int(value)
    if kind == "bool":
        return value.lower() == "true"
    if kind == "null":
        return None
    if kind == "json":
        return json.loads(value)
    if kind == "str":
        return value
    return raw


def write_status(path, assignments):
    data = {}
    for assignment in assignments:
        if "=" not in assignment:
            raise ValueError("status assignment lacks '=': %s" % assignment)
        key, raw = assignment.split("=", 1)
        data[key] = parse_value(raw)
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "w") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")
    with open(path, "r") as stream:
        parsed = json.load(stream)
    if parsed != data:
        raise ValueError("status JSON round-trip mismatch")
    return data


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--set", action="append", default=[])
    args = parser.parse_args(argv)
    write_status(args.output, args.set)
    return 0


if __name__ == "__main__":
    sys.exit(main())

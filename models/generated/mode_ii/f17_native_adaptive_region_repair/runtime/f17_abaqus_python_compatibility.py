from __future__ import print_function
import math

def count_finite_values(values):
    count=0
    for value in values:
        datum=float(value.data)
        if not math.isnan(datum) and not math.isinf(datum):
            count += 1
    return count

def compatibility_self_test():
    class Value(object):
        def __init__(self, data): self.data=data
    values=[Value(1.0),Value(float('nan')),Value(float('inf')),Value(-2.0)]
    return count_finite_values(values)==2

if __name__=='__main__':
    raise SystemExit(0 if compatibility_self_test() else 1)

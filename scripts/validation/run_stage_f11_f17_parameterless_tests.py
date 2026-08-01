from __future__ import print_function
import inspect, runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FILES=[ROOT/('tests/unit/test_stage_f%d%s.py' % (stage, suffix))
       for stage, suffix in ((11,'_qualification'),(12,'_batch'),(13,'_batch'),(14,'_batch'),(15,'_notifications'),(16,'_conditional_batch'),(16,'_r3_queue_replacement'),(17,'_preparation'))]
passed=0
for path in FILES:
    namespace=runpy.run_path(str(path))
    for name in sorted(namespace):
        value=namespace[name]
        if name.startswith('test_') and callable(value) and len(inspect.signature(value).parameters)==0:
            value(); passed += 1
print('%d parameterless Stage F11-F17 tests passed' % passed)

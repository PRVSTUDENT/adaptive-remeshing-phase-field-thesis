import subprocess

def test_exit_propagation():
    script_fail = """#!/bin/bash
false
ABAQUS_RC=$?
exit ${ABAQUS_RC}
"""
    r1 = subprocess.run(["bash", "-c", script_fail])
    print("Failing script returned:", r1.returncode)
    assert r1.returncode != 0, "Failing command must return non-zero!"

    script_pass = """#!/bin/bash
true
ABAQUS_RC=$?
exit ${ABAQUS_RC}
"""
    r2 = subprocess.run(["bash", "-c", script_pass])
    print("Passing script returned:", r2.returncode)
    assert r2.returncode == 0, "Passing command must return 0!"
    print("EXIT PROPAGATION TEST: PASSED")

if __name__ == "__main__":
    test_exit_propagation()

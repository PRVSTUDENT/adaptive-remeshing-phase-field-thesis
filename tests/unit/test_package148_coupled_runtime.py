"""Independent small-mesh and process-contract tests; no Abaqus qualification claim."""
import json
import hashlib
import math
from pathlib import Path
import tempfile
import sys
import subprocess
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    CoupledAbaqusRuntime, PDASReEquilibrationSolver, driving_history,
    shape_gradients, validate_damage, StageC1GateEvaluator,
)
from scripts.state_transfer.build_package146_147_transfer_deck import parse_donor_history_from_evaluation
from scripts.validation.extract_package148_iteration import export

ROOT = Path(__file__).resolve().parents[2]


def square():
    return SimpleNamespace(nodes={1: (0., 0.), 2: (1., 0.),
                                  3: (1., 1.), 4: (0., 1.)},
                           elements={1: [1, 2, 3, 4]})


class CoupledRuntimeTests(unittest.TestCase):
    def test_complete_finite_damage_required(self):
        for values in ({}, {1: .1}, {1: .1, 2: float('nan')},
                       {1: -.1, 2: .1}, {1: .1, 2: 1.01}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                validate_damage(values, {1, 2})

    def test_kkt_signed_dual_and_free_residuals(self):
        solver = PDASReEquilibrationSolver(square(), dict.fromkeys(range(1, 5), .1),
                                           {(1, g): .2 for g in range(1, 5)})
        self.assertFalse(solver.kkt(solver.d0_nodal)['passed'])
        self.assertGreater(solver.kkt(solver.d0_nodal)['dual_error'], 0)
        equilibrium = dict.fromkeys(range(1, 5), .4/(.36+.4))
        self.assertTrue(solver.kkt(equilibrium)['passed'])
        wrong = dict(equilibrium); wrong[1] += .01
        self.assertFalse(solver.kkt(wrong)['passed'])
        solver.h_gp = {(1, g): 0 for g in range(1, 5)}
        self.assertTrue(solver.kkt(solver.d0_nodal)['passed'])

    def test_affine_driving_energy_matches_frozen_uel_and_no_ratchet(self):
        mesh = square()
        u = {n: (.01*x+.003*y, -.002*x+.02*y) for n, (x, y) in mesh.nodes.items()}
        baseline = {(1, g): 0. for g in range(1, 5)}
        high = driving_history(mesh, u, baseline)
        lam = 210*.3/(1.3*.4); mu = 210/2.6
        expected = .5*lam*.03**2+mu*(.01**2+.02**2+2*.0005**2)
        for value in high.values():
            self.assertAlmostEqual(value, expected, places=13)
        low = driving_history(mesh, {n: (0., 0.) for n in mesh.nodes}, baseline)
        self.assertEqual(set(low.values()), {0.})
        with self.assertRaises(ValueError):
            driving_history(mesh, u, {})

    def test_invalid_jacobian_rejected(self):
        with self.assertRaises(ValueError):
            shape_gradients([(0, 0)]*4, 0, 0)

    def test_donor_history_perimeter_to_row_permutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'evaluation.json'
            path.write_text(json.dumps({'packages': {'146': {
                'history_keys': ['PART-1-1:10225:'+str(g) for g in range(1, 5)],
                'history_endpoint': [10., 20., 30., 40.]}}}))
            mapped = parse_donor_history_from_evaluation(path)
            self.assertEqual(mapped, {(1, 1): 10., (1, 2): 20., (1, 3): 40., (1, 4): 30.})

    def test_nonuniform_skew_element_matches_independent_residual_evaluator(self):
        from scripts.validation.evaluate_pdas_phase_residual import PhaseResidualEvaluator
        with tempfile.TemporaryDirectory() as tmp:
            deck, bounds = Path(tmp)/'mesh.inp', Path(tmp)/'bounds.csv'
            deck.write_text('*Node\n1,0,0\n2,2,.2\n3,2.2,1.3\n4,.1,1\n'
                            '*Element, type=U1\n1,1,2,3,4\n')
            bounds.write_text('eid,d1,d2,d3,d4,h1,h2,h3,h4\n1,.1,.1,.1,.1,.1,.2,.7,.4\n')
            independent = PhaseResidualEvaluator(deck, bounds)
            mesh = SimpleNamespace(nodes=independent.nodes, elements=independent.elements)
            solver = PDASReEquilibrationSolver(mesh, dict.fromkeys(range(1, 5), .1),
                                               {(1, g): v for g, v in enumerate([.1, .2, .7, .4], 1)})
            diag, off, rhs = solver.assemble_system()
            for i in range(1, 5):
                self.assertAlmostEqual(rhs[i], independent.F_d[i-1], places=13)
                for j in range(1, 5):
                    value = diag[i] if i == j else off[i, j]
                    self.assertAlmostEqual(value, independent.K_dd[i-1, j-1], places=13)
            damage = {1: .2, 2: .3, 3: .5, 4: .4}
            self.assertTrue(independent.verify_fd_gradient(3, damage)['consistent'])

    def fixture(self, root, broken=None, max_outer=5):
        package = root/'package'; package.mkdir()
        frozen = ROOT/'models/pandey_kumar_mode1/148_c4_package148_state_transfer/f42_mixed_uel.for'
        (package/'f42_mixed_uel.for').write_bytes(frozen.read_bytes())
        runtime = CoupledAbaqusRuntime(package, root/'run', Path(__file__),
                                      1., 2., max_outer=max_outer)
        def load():
            runtime.mesh = square()
            runtime.d0 = dict.fromkeys(range(1, 5), .1)
            runtime.h0 = {(1, g): .2 for g in range(1, 5)}
            runtime.target_u = .001800312544
            runtime.solver = PDASReEquilibrationSolver(runtime.mesh, runtime.d0, runtime.h0)
            runtime.source_hashes = {'fixture': 'synthetic; no scientific acceptance evidence'}
            runtime.template = ('*Heading\n*Node\n1,0,0\n2,1,0\n3,1,1\n4,0,1\n'
                                '*Equation\n2\n3,2,1.,999999,2,-1.\n'
                                '*Boundary\nN_TOP,1,1,0.\n'
                                '*Include, input=initial_conditions_solution.inc\n'
                                '*Step, name=old\n*End Step\n')
        runtime.load = load
        calls = []
        def runner(directory, job, role):
            text = (directory/(job+'.inp')).read_text()
            calls.append((role, text))
            if broken == 'solver':
                raise RuntimeError('synthetic solver failure')
            rows = []
            for n, (x, y) in runtime.mesh.nodes.items():
                if role == 'mechanical':
                    card = next(line for line in text.splitlines() if line.startswith('%d, 3, 3,' % n))
                    damage = float(card.split(',')[-1])
                else:
                    damage = .4/.76
                rows.append([n, 0., runtime.target_u*y, damage])
            if broken == 'missing':
                rows.pop()
            result = dict(schema=1, increment=1, step_time=1., nodes=rows,
                          rp_u2=runtime.target_u, rf2_kN=1., elastic_kNmm=1., fracture_kNmm=1.)
            if broken == 'nonfinite':
                result['nodes'][0][1] = float('inf')
            return result
        runtime.runner = runner
        return runtime, calls

    def test_real_loop_alternates_and_rechecks_mechanical_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, calls = self.fixture(Path(tmp))
            result = runtime.run()
            self.assertEqual([r for r, _ in calls],
                             ['mechanical', 'phase', 'mechanical', 'phase', 'mechanical'])
            self.assertEqual(result['status'], 'EQUILIBRIUM_PASS')
            self.assertTrue(result['physical_gates_passed'])  # Synthetic fixture only.
            self.assertFalse(result['scientific_acceptance'])
            self.assertFalse(result['full_state_preservation_verified'])
            mechanical, phase = calls[0][1], calls[1][1]
            self.assertIn('*Equation', mechanical)
            self.assertNotIn('*Equation', phase)
            self.assertNotIn(', 3, 3,', phase)  # Negative multipliers release all nodes.
            self.assertIn('1, 1, 1,', phase)    # Mechanics is frozen for the phase solve.
            self.assertEqual(runtime.h0, {(1, g): .2 for g in range(1, 5)})
            self.assertTrue((runtime.output/'runtime_report.json').is_file())
            with self.assertRaises(FileExistsError):
                runtime.run()

    def test_solver_and_incomplete_output_stop_without_retry(self):
        for broken in ('solver', 'missing', 'nonfinite'):
            with self.subTest(broken=broken), tempfile.TemporaryDirectory() as tmp:
                runtime, calls = self.fixture(Path(tmp), broken=broken)
                with self.assertRaises((RuntimeError, ValueError)):
                    runtime.run()
                self.assertEqual(len(calls), 1)
                report = json.loads((runtime.output/'runtime_report.json').read_text())
                self.assertEqual(report['status'], 'FAILED')
                self.assertFalse(report['scientific_acceptance'])

    def test_nonconvergence_is_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, _ = self.fixture(Path(tmp), max_outer=2)
            with self.assertRaisesRegex(RuntimeError, 'outer iteration limit'):
                runtime.run()

    def test_physical_gate_failure_is_separate_from_equilibrium(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, _ = self.fixture(Path(tmp))
            runtime.evaluator = StageC1GateEvaluator(10., 2.)
            result = runtime.run()
            self.assertEqual(result['status'], 'PHYSICAL_GATE_FAIL')
            self.assertFalse(result['scientific_acceptance'])

    def test_process_contract_is_serial_bounded_and_no_scheduler(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, _ = self.fixture(Path(tmp))
            runtime.load()
            runtime.deadline = math.inf
            directory = Path(tmp)/'command'; directory.mkdir()
            (directory/'test.sta').write_text('THE ANALYSIS HAS COMPLETED SUCCESSFULLY')
            (directory/'test.odb').write_bytes(b'synthetic ODB identity only')
            (directory/'endpoint.json').write_text(json.dumps(dict(
                odb_sha256=hashlib.sha256((directory/'test.odb').read_bytes()).hexdigest(),
                extractor_sha256=hashlib.sha256(runtime.extractor.read_bytes()).hexdigest())))
            with patch.object(runtime, '_command') as command:
                runtime._run_abaqus(directory, 'test', 'mechanical')
            commands = [c.args[0] for c in command.call_args_list]
            self.assertIn('cpus=1', commands[0])
            self.assertIn('interactive', commands[0])
            self.assertEqual(commands[1][1], 'python')
            self.assertIn('--physical-elements', commands[1])
            self.assertFalse(any('qsub' in s for c in commands for s in c))

    def test_process_timeout_and_nonzero_exit_preserve_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, _ = self.fixture(Path(tmp))
            runtime.deadline = time.monotonic()+.1
            log = Path(tmp)/'timeout.txt'
            with self.assertRaises(subprocess.TimeoutExpired):
                runtime._command([sys.executable, '-c', 'import time; time.sleep(10)'], Path(tmp), log)
            self.assertTrue(log.is_file())
            runtime.deadline = time.monotonic()+10
            with self.assertRaises(subprocess.CalledProcessError):
                runtime._command([sys.executable, '-c', 'raise SystemExit(7)'],
                                 Path(tmp), Path(tmp)/'failed.txt')

    def test_extractor_reads_only_complete_endpoint_and_counts_energy_once(self):
        instance = SimpleNamespace(name='PART-1-1')
        def node(n, data):
            return SimpleNamespace(instance=instance, nodeLabel=n, data=data)
        def energy(g, data):
            return SimpleNamespace(instance=instance, elementLabel=3,
                                   integrationPoint=g, data=data)
        fields = dict(U=SimpleNamespace(values=[node(n, [0., 0., .2]) for n in range(1, 5)]+
                                        [node(999999, [0., .0018])]),
                      RF=SimpleNamespace(values=[node(999999, [0., .1])]),
                      SDV17=SimpleNamespace(values=[energy(g, .5) for g in range(1, 5)]),
                      SDV18=SimpleNamespace(values=[energy(g, 1.) for g in range(1, 5)]))
        frame = SimpleNamespace(incrementNumber=1, frameValue=1., fieldOutputs=fields)
        odb = SimpleNamespace(steps={'C1-1-ReEquil': SimpleNamespace(frames=[frame])},
                              close=lambda: None)
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp)/'test.odb', Path(tmp)/'endpoint.json'
            source.write_bytes(b'synthetic fixture')
            opener = unittest.mock.Mock(return_value=odb)
            with patch.dict(sys.modules, {'odbAccess': SimpleNamespace(openOdb=opener)}):
                export(str(source), str(output), 4, 1)
                self.assertTrue(opener.call_args.kwargs['readOnly'])
                result = json.loads(output.read_text())
                self.assertEqual(result['fracture_kNmm'], .5)
                self.assertEqual(result['elastic_kNmm'], 1.)
                fields['U'].values.pop(0)
                with self.assertRaisesRegex(RuntimeError, 'coverage'):
                    export(str(source), str(Path(tmp)/'bad.json'), 4, 1)
                self.assertFalse((Path(tmp)/'bad.json').exists())


if __name__ == '__main__':
    unittest.main()

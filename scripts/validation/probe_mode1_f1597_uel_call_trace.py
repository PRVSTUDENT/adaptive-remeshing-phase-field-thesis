"""Prepare non-invasive UEL tracing and validate authentic solver evidence.

Preparation never runs Abaqus, submits jobs or claims an authentic call trace.
An instrumented source is NOT an executable-package qualification certificate.
"""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

OPERATION = 'authentic_uel_history_call_trace'
PARENT = 'models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/'
PACKAGE = 'models/pandey_kumar_mode1/73_method_c_history_call_trace/'
PARENT_SHA = 'ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d'
BEGIN = 'C F1597_TRACE_BEGIN'
END = 'C F1597_TRACE_END'
HEADER = ['seq', 'event', 'edge', 'step', 'inc', 'element', 'jtype',
          'lflag1', 'lflag2', 'lflag3', 'time1', 'time2', 'dt',
          'phase', 'residual_inf', 'energy2', 'energy7'] + [f'u{i}' for i in range(1, 9)] + [f'hc{i}' for i in range(1, 5)] + [f'ht{i}' for i in range(1, 5)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strip_instrumentation(data):
    result = []; inside = False
    for line in data.splitlines(keepends=True):
        text = line.decode('ascii').rstrip('\r\n')
        if text == BEGIN:
            if inside: raise ValueError('Nested trace block')
            inside = True
        elif text == END:
            if not inside: raise ValueError('Unmatched trace marker')
            inside = False
        elif not inside:
            result.append(line)
    if inside: raise ValueError('Unclosed trace block')
    return b''.join(result)


def instrument(parent, absolute_trace=False):
    if sha(parent) != PARENT_SHA:
        raise ValueError('Experimental UEL parent must be re-reviewed')
    newline = '\r\n' if b'\r\n' in parent else '\n'
    text = parent.decode('ascii')

    def block(lines):
        if any(len(line) > 72 for line in lines if not line.startswith('C')):
            raise ValueError('Fixed-form trace line exceeds 72 columns')
        return newline.join([BEGIN]+lines+[END, ''])

    def snapshot(event, edge, element, jtype, flags, residual, e2, e7):
        return ['      CALL F1597_TRACE('+','.join(map(str, [event, edge]))+',',
                '     1 KSTEP,KINC,'+element+','+jtype+','+flags+',',
                '     2 TIME,DTIME,SV_PHASE_TRIAL('+element+'),',
                ('     C NDOFEL,U,' if element == 'PHYSIDX' else '     C 0,TIME,'),
                '     3 '+residual+','+e2+','+e7+',',
                '     4 SV_H_COMMITTED('+element+',1),',
                '     5 SV_H_COMMITTED('+element+',2),',
                '     6 SV_H_COMMITTED('+element+',3),',
                '     7 SV_H_COMMITTED('+element+',4),',
                '     8 SV_H_TRIAL('+element+',1),',
                '     9 SV_H_TRIAL('+element+',2),',
                '     A SV_H_TRIAL('+element+',3),',
                '     B SV_H_TRIAL('+element+',4))']

    uel_start = text.index('      SUBROUTINE UEL(')
    umat_start = text.index('      SUBROUTINE UMAT(')
    external, uel, umat = text[:uel_start], text[uel_start:umat_start], text[umat_start:]
    marker = '      IF (JTYPE .EQ. 1 .OR. JTYPE .EQ. 3) THEN'+newline
    if uel.count(marker) != 1: raise ValueError('Ambiguous UEL entry anchor')
    entry = snapshot(1, 0, 'PHYSIDX', 'JTYPE', 'LFLAGS(1),LFLAGS(2),LFLAGS(3)', '0.D0', '0.D0', '0.D0')
    exit_ = snapshot(1, 1, 'PHYSIDX', 'JTYPE', 'LFLAGS(1),LFLAGS(2),LFLAGS(3)', 'MAXVAL(ABS(RHS(1:NDOFEL,1)))', 'ENERGY(2)', 'ENERGY(7)')
    uel = uel.replace(marker, block(entry)+marker, 1)
    pos = uel.rindex('      RETURN'+newline)
    uel = uel[:pos]+block(exit_)+uel[pos:]
    # Pre LOP1/2 and post LOP0/1/2/3. Never read uninitialized LOP0 state.
    marker = '      IF (LOP .EQ. 0) THEN'+newline
    pre = ['      IF (LOP.EQ.1.OR.LOP.EQ.2) THEN', '        DO I=1,336,335']
    pre += snapshot('100+LOP', 0, 'I', '0', '0,0,0', '0.D0', '0.D0', '0.D0')
    pre += ['        ENDDO', '      ENDIF']
    external = external.replace(marker, block(pre)+marker, 1)
    pos = external.rindex('      RETURN'+newline)
    post = ['      IF (LOP.GE.0.AND.LOP.LE.3) THEN', '        DO I=1,336,335']
    # UEXTERNALDB has DTIME and TIME with the same names as UEL.
    post += snapshot('100+LOP', 1, 'I', '0', '0,0,0', '0.D0', '0.D0', '0.D0')
    post += ['        ENDDO', '      ENDIF']
    external = external[:pos]+block(post)+external[pos:]
    helper = [
        '      SUBROUTINE F1597_TRACE(EV,EDGE,KS,KI,EL,JT,F1,F2,F3,',
        '     1 TM,DT,DP,NU,UV,RR,E2,E7,C1,C2,C3,C4,T1,T2,T3,T4)',
        '      IMPLICIT NONE',
        '      INTEGER EV,EDGE,KS,KI,EL,JT,F1,F2,F3,SEQ,NU,J',
        '      DOUBLE PRECISION TM(2),DT,DP,RR,E2,E7,UV(*),UU(8)',
        '      DOUBLE PRECISION C1,C2,C3,C4,T1,T2,T3,T4',
        '      LOGICAL OPENED',
        '      SAVE SEQ,OPENED',
        '      DATA SEQ/0/,OPENED/.FALSE./',
        '      IF (EL.NE.1.AND.EL.NE.336) RETURN',
        '      IF (.NOT.OPENED) THEN',
        "        OPEN(UNIT=109,FILE='f1597_uel_call_trace.csv',",
        "     1       STATUS='NEW',ACTION='WRITE')",
        '        OPENED=.TRUE.',
        '      ENDIF',
        '      IF (SEQ.GE.2048) THEN',
        "        IF (SEQ.EQ.2048) WRITE(109,'(A)') 'TRACE_TRUNCATED'",
        '        SEQ=2049',
        '        RETURN',
        '      ENDIF',
        '      SEQ=SEQ+1',
        '      DO J=1,8',
        '        UU(J)=0.D0',
        '        IF (J.LE.NU) UU(J)=UV(J)',
        '      ENDDO',
        '      WRITE(109,10) SEQ,EV,EDGE,KS,KI,EL,JT,F1,F2,F3,',
        '     1 TM(1),TM(2),DT,DP,RR,E2,E7,UU,',
        '     2 C1,C2,C3,C4,T1,T2,T3,T4',
        " 10   FORMAT(9(I10,','),I10,23(',',ES25.16E3))",
        '      CALL FLUSH(109)',
        '      RETURN',
        '      END',
    ]
    if absolute_trace:
        pos=helper.index('      LOGICAL OPENED')
        helper[pos:pos]=['      CHARACTER*512 TRACE_DIR,TRACE_PATH','      INTEGER LTRACE']
        pos=helper.index("        OPEN(UNIT=109,FILE='f1597_uel_call_trace.csv',")
        helper[pos:pos+1]=['        CALL GETOUTDIR(TRACE_DIR,LTRACE)',
                          '        TRACE_PATH=TRACE_DIR(1:LTRACE)//',
                          "     1       '/f1597_uel_call_trace.csv'",
                          '        OPEN(UNIT=109,FILE=TRIM(TRACE_PATH),']
    generated = (external+uel+umat+block(helper)).encode('ascii')
    if strip_instrumentation(generated) != parent:
        raise ValueError('Instrumentation altered non-diagnostic source bytes')
    return generated


def prepare(workspace):
    task = json.loads((workspace/'project_coordination/ACTIVE_TASK.json').read_text(encoding='utf-8-sig'))
    checkpoint = task['scientific_checkpoint']; basis_path = workspace/checkpoint['artifact']
    basis = json.loads(basis_path.read_text())
    if sha(basis_path.read_bytes()).upper() != checkpoint['sha256'].upper() or basis['operation'] != 'mapped_mechanical_history_call_order_probe' or not basis['verification_passed']:
        raise ValueError('Completed mechanical/history checkpoint required')
    sources = {}
    for path in ('scripts/validation/probe_mode1_f1597_uel_call_trace.py',
                 'tests/unit/test_mode1_f1597_uel_call_trace.py'):
        sources[path] = sha((workspace/path).read_bytes())
    for name in ('f42_experimental_offset_uel.for', 'M1_EXP_COUPLED_TRANSFER_650.inp', 'offset_state_table.csv'):
        path = PARENT+name; actual = sha((workspace/path).read_bytes())
        if basis['sources'][path] != actual: raise ValueError('Scientific basis source changed')
        sources[path] = actual
    folder = workspace/PACKAGE; folder.mkdir(parents=True, exist_ok=True)
    output = folder/'f42_history_trace_uel.for'
    data = instrument((workspace/(PARENT+'f42_experimental_offset_uel.for')).read_bytes())
    if output.exists() and output.read_bytes() != data: raise ValueError('Preserve differing instrumentation candidate')
    if not output.exists(): output.write_bytes(data)
    return dict(schema=1, operation=OPERATION, preparation_status='TECHNICAL_QUALIFICATION_REQUIRED',
        implementation_validated=True, dispatch_ready=False, selected_physical_elements=[1, 336],
        selection_basis='Element 336: first recorded history increase; element 1: reference. Neither is assumed to be a crack-tip label.',
        max_records=2048, trace_columns=HEADER,
        parent_source_sha256=PARENT_SHA, instrumented_source=PACKAGE+output.name,
        instrumented_source_sha256=sha(data), basis_artifact=checkpoint['artifact'], basis_sha256=checkpoint['sha256'],
        blocked_on=['Compile and Abaqus 2023 datacheck of the distinct instrumented source',
                    'Qualified manifest adapter for instrumentation: existing experimental adapter pins the uninstrumented EF92ED58 hash',
                    'Real notification, scheduler and once-only technical preflight before any diagnostic submission',
                    'Actual solver trace, terminal receipts and numerical force/energy parity review'],
        sources=sources, limitation='Byte-exact source restoration proves inserted logging only; it does not prove compiler, solver or numerical parity.')


def analyze_trace(rows):
    """Analyze only explicitly supplied solver records; no simulated trace generation."""
    import math
    if not rows or len(rows) > 2048: raise ValueError('Empty/unbounded trace')
    pending = {}; uel_calls = phase_calls = mechanical_calls = history_writes = accepts = 0
    first = None; max_delta = 0.; last_seq = 0
    for raw in rows:
        if len(raw) != len(HEADER): raise ValueError('Malformed/truncated trace')
        v = [float(x.replace('D', 'E')) for x in raw]
        if not all(math.isfinite(x) for x in v): raise ValueError('Nonfinite trace')
        row = dict(zip(HEADER, v))
        if any(row[k] != int(row[k]) for k in HEADER[:10]): raise ValueError('Noninteger trace context')
        if row['seq'] != last_seq+1 or row['element'] not in (1, 336) or row['edge'] not in (0, 1): raise ValueError('Invalid trace order/context')
        last_seq = int(row['seq']); event = int(row['event']); key = (event, row['element'], row['jtype'])
        if row['step'] < 0 or row['inc'] < 0: raise ValueError('Invalid solver increment context')
        if event == 100 and row['edge'] == 1: continue
        if event == 103 and row['edge'] == 1: continue
        if event not in (1, 101, 102): raise ValueError('Unknown callback')
        if row['edge'] == 0:
            if key in pending: raise ValueError('Unpaired trace entry')
            pending[key] = row; continue
        if key not in pending: raise ValueError('Unpaired trace exit')
        before = pending.pop(key)
        if (before['step'], before['inc']) != (row['step'], row['inc']): raise ValueError('Changed call context')
        committed = [row[f'hc{i}'] for i in range(1, 5)]
        trial = [row[f'ht{i}'] for i in range(1, 5)]
        if event == 1:
            uel_calls += 1; phase_calls += row['jtype'] == 1; mechanical_calls += row['jtype'] == 2
            if row['jtype'] not in (1, 2): raise ValueError('Unexpected element type')
            if max(abs(committed[i-1]-before[f'hc{i}']) for i in range(1, 5)) > 1e-12: raise ValueError('UEL modified committed history')
            delta = max(trial[i-1]-before[f'ht{i}'] for i in range(1, 5))
            if min(trial[i-1]-before[f'ht{i}'] for i in range(1, 5)) < -1e-12: raise ValueError('History decreased within UEL')
            if delta > 1e-10:
                history_writes += 1; max_delta = max(max_delta, delta)
                if first is None: first = dict(sequence=int(row['seq']), element=int(row['element']), step=int(row['step']), increment=int(row['inc']), jtype=int(row['jtype']))
        elif event == 101:
            if max(abs(c-t) for c,t in zip(committed, trial)) > 1e-12: raise ValueError('LOP1 restore mismatch')
        elif event == 102:
            accepts += 1
            if max(abs(committed[i-1]-before[f'ht{i}']) for i in range(1, 5)) > 1e-12: raise ValueError('LOP2 commit mismatch')
    if pending or not (phase_calls and mechanical_calls and accepts): raise ValueError('Incomplete solver lifecycle trace')
    return dict(trace_records=len(rows), uel_calls=uel_calls, phase_calls=int(phase_calls), mechanical_calls=int(mechanical_calls), accepted_element_callbacks=accepts, history_write_calls=history_writes, history_increase_inf_kN_mm2=max_delta), first


def probe(workspace):
    # Acquisition is an external, technically qualified Abaqus experiment. Refuse to
    # reinterpret offline reconstruction or test fixtures as actual solver evidence.
    package='models/pandey_kumar_mode1/74_method_c_history_call_trace_absolute_path/'
    folder = workspace/package/'evidence'
    provenance_path = folder/'provenance.json'
    qualification_path=workspace/package/'QUALIFICATION.json'
    if not provenance_path.is_file() or not qualification_path.is_file(): raise ValueError('TRACE_ACQUISITION_REQUIRED: exact qualified solver evidence is missing')
    qualification=json.loads(qualification_path.read_text())
    if qualification.get('status')!='READY_FOR_TRACE_ANALYSIS' or qualification.get('dispatch_ready') is not True: raise ValueError('Trace technical qualification incomplete')
    sources=dict(qualification['sources'])
    for path,expected in sources.items():
        full=(workspace/path).resolve()
        if not full.is_relative_to(workspace) or not full.is_file() or sha(full.read_bytes())!=expected: raise ValueError('Trace qualification source changed: '+path)
    provenance = json.loads(provenance_path.read_text()); receipt = provenance['pbs_job_id']
    if receipt != qualification['pbs_job_id'] or not re.fullmatch(r'\d+\.mmaster02', receipt): raise ValueError('Invalid actual PBS receipt')
    with (workspace/'project_coordination/HPC_JOB_LEDGER.csv').open(encoding='utf-8-sig') as handle:
        records=[r for r in csv.DictReader(handle) if r.get('Job_ID')==receipt and r.get('Job_Name')=='M1_F1597_HISTORY_TRACE_R2']
    if len(records)!=1 or records[0]['Status']!='COMPLETED' or records[0]['Exit_Status']!='0': raise ValueError('Terminal PBS receipt absent from ledger')
    receipts=json.loads((workspace/'project_coordination/MODE1_BATCH_SUBMISSIONS.json').read_text(encoding='utf-8-sig'))
    if receipts[qualification['manifest_sha256']]['M1_F1597_HISTORY_TRACE_R2']['pbs_job_id']!=receipt: raise ValueError('Governed receipt mismatch')
    if provenance.get('solver') != 'Abaqus/Standard 2023' or type(provenance.get('exit_code')) is not int or provenance['exit_code']!=0: raise ValueError('Unverified solver termination')
    if provenance.get('instrumented_source_sha256') != sha((workspace/package/'f42_history_trace_uel.for').read_bytes()): raise ValueError('Trace source mismatch')
    for name, expected in provenance['evidence_files'].items():
        if Path(name).name != name: raise ValueError('Unsafe evidence filename')
        if sha((folder/name).read_bytes())!=expected: raise ValueError('Evidence hash mismatch')
    from qualify_mode1_f1597_trace import compare_parity
    parity=compare_parity(workspace,folder,package=package)
    recorded=json.loads((folder/'parity.json').read_text())
    if recorded!=parity: raise ValueError('Recorded parity differs from recomputed measurements')
    with (folder/'f1597_uel_call_trace.csv').open() as handle:
        measurements, first = analyze_trace(list(csv.reader(handle)))
    basis=json.loads((workspace/qualification['basis_artifact']).read_text())
    measurements.update(phase_elements=basis['measurements']['phase_elements'],phase_nodes=basis['measurements']['phase_nodes'])
    sources[package+'QUALIFICATION.json']=sha(qualification_path.read_bytes())
    return dict(schema=1, task_id='F1597', operation=OPERATION, verification_passed=True,
        measurements=measurements, first_history_update=first, pbs_job_id=receipt, sources=sources,
        instrumentation_parity=parity,
        finding='Authentic solver lifecycle trace validated; history writes distinguished from accepted LOP2 commits.',
        limitation='Selected elements only; invocation sequence is not a Newton iteration counter. Transfer remains failed and unqualified.',
        next_operation='Review authenticated solver call ordering and parity before choosing a numerical correction.')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args(); root = args.workspace.resolve()
    result = prepare(root) if args.prepare else probe(root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(result, indent=2)+'\n').encode()
    if args.output.exists() and args.output.read_bytes() != data: raise ValueError('Preserve differing operation evidence')
    if not args.output.exists(): args.output.write_bytes(data)
    print(json.dumps(result))

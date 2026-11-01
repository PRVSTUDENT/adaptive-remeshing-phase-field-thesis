import json
import tempfile
import unittest
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from local_bridge_server import State, sha, make_handler, atomic_json
from concurrent.futures import ThreadPoolExecutor


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.state = State(self.root, 'TEST_ONLY_TOKEN_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        self.cid = 'tab_01234567890123456789012345'
        self.ident = 'HND-SUP-0123456789abcdef0123456789abcdef'
        self.prompt = ('[BRIDGE_HANDOFF_ID=' + self.ident + ']\nCHATGPT_SUPERVISOR_V1\nNEXT DECISION: respond only JSON')
        (self.root / 'bridge_request.ready').write_text(self.prompt, encoding='utf-8')
        (self.root / 'bridge.lock').write_text(json.dumps({'bridge_handoff_id': self.ident, 'pid': 123}), encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def body(self, raw, **kw):
        return {'handoff_id': self.ident, 'client_id': self.cid,
                'request_sha256': sha(self.prompt), 'response': raw, **kw}

    def response(self):
        return json.dumps({'correlation_id': self.ident, 'action': 'CONTINUE', 'instruction': 'Read-only check.'})

    def test_actual_http_endpoints_and_token_enforcement(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(self.state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_address[1]}'
        try:
            with self.assertRaises(HTTPError) as denied:
                urlopen(Request(url + '/health'))
            self.assertEqual(denied.exception.code, 403)
            hdr = {'X-Bridge-Token': self.state.token, 'Origin': 'https://chatgpt.com'}
            with urlopen(Request(url + '/health', headers=hdr)) as resp:
                self.assertEqual(json.load(resp)['status'], 'OK')
            with urlopen(Request(url + '/next?client_id=' + self.cid, headers=hdr)) as resp:
                tx = json.load(resp)
            self.assertEqual((tx['status'], tx['handoff_id']), ('READY', self.ident))
            raw_body = json.dumps(self.body(self.response())).encode('utf-8')
            with urlopen(Request(url + '/response', headers=hdr, data=raw_body, method='POST')) as resp:
                result = json.load(resp)
            self.assertEqual(result['status'], 'ACCEPTED')
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_accepted_response_uses_original_powershell_wire_format(self):
        code, req = self.state.next(self.cid)
        self.assertEqual((code, req['status']), (200, 'READY'))
        self.assertEqual(req['prompt'], self.prompt)
        code, ans = self.state.submit(self.body(self.response()))
        self.assertEqual((code, ans['status']), (200, 'ACCEPTED'))
        wire = json.loads((self.root / 'bridge_response.ready').read_text(encoding='utf-8'))
        self.assertEqual(wire['bridge_handoff_id'], self.ident)
        self.assertEqual(wire['response'], self.response())
        self.assertEqual(wire['status'], 'OK')
        code, next_ = self.state.next(self.cid)
        self.assertEqual(next_['status'], 'DELIVERED')

    def test_stale_correlation_is_rejected_without_writing_response(self):
        self.state.next(self.cid)
        bad = json.dumps({'correlation_id':'HND-SUP-old', 'action':'CONTINUE', 'instruction':'bad'})
        code, ans = self.state.submit(self.body(bad))
        self.assertEqual((code, ans['error']), (422, 'SUPERVISOR_STALE_RESPONSE'))
        self.assertFalse((self.root / 'bridge_response.ready').exists())

    def test_other_browser_cannot_claim_or_submit(self):
        self.state.next(self.cid)
        code, reply = self.state.next('tab_abcdefghijabcdefghij')
        self.assertEqual(reply['status'], 'HELD_BY_OTHER_BROWSER')
        code, ans = self.state.submit({'handoff_id': self.ident,
                                       'client_id': 'tab_abcdefghijabcdefghij',
                                       'request_sha256': sha(self.prompt), 'response': self.response()})
        self.assertEqual((code, ans['error']), (409, 'CLIENT_OWNERSHIP_MISMATCH'))

    def test_duplicate_response_rejected_even_after_consumer_removed_ready_file(self):
        self.state.next(self.cid)
        self.assertEqual(self.state.submit(self.body(self.response()))[0], 200)
        (self.root / 'bridge_response.ready').unlink()
        code, ans = self.state.submit(self.body(self.response()))
        self.assertEqual((code, ans['error']), (409, 'RESPONSE_ALREADY_PUBLISHED'))

    def test_changed_prompt_and_lock_rejected(self):
        self.state.next(self.cid)
        (self.root / 'bridge_request.ready').write_text(self.prompt + '\nTAMPERED', encoding='utf-8')
        code, ans = self.state.next(self.cid)
        self.assertEqual((code, ans['error']), (409, 'CLAIM_REQUEST_CHANGED'))
        code, ans = self.state.submit(self.body(self.response()))
        self.assertEqual((code, ans['error']), (409, 'STALE_OR_CHANGED_REQUEST'))

    def test_missing_active_lock_is_idle(self):
        (self.root / 'bridge.lock').unlink()
        code, answer = self.state.next(self.cid)
        self.assertEqual((code, answer['status']), (200, 'IDLE'))

    def test_invalid_supervisor_reply_rejected(self):
        self.state.next(self.cid)
        for response in ('not-json', '{"correlation_id":"'+self.ident+'","action":"APPROVE","instruction":"bad"}'):
            code, answer = self.state.submit(self.body(response))
            self.assertEqual(code, 422)
        self.assertFalse((self.root / 'bridge_response.ready').exists())

    def test_fenced_json_supported(self):
        self.state.next(self.cid)
        code, ans = self.state.submit(self.body('```json\n' + self.response() + '\n```'))
        self.assertEqual((code,ans['status']),(200,'ACCEPTED'))

    def test_immutable_publication_has_only_one_winner(self):
        path = self.root / 'exclusive.json'
        def publish(i):
            try:
                atomic_json(path, {'writer': i})
                return i
            except FileExistsError:
                return None
        with ThreadPoolExecutor(max_workers=16) as pool:
            winners = [i for i in pool.map(publish, range(32)) if i is not None]
        self.assertEqual(len(winners), 1)
        self.assertEqual(json.loads(path.read_text())['writer'], winners[0])

    def test_restart_preserves_claim_against_new_browser_document(self):
        self.state.next(self.cid)
        restarted = State(self.root, self.state.token)
        self.assertEqual(restarted.next('tab_new_document_0123456789')[1]['status'],
                         'HELD_BY_OTHER_BROWSER')

    def test_restart_preserves_consumed_receipt(self):
        self.state.next(self.cid)
        self.state.submit(self.body(self.response()))
        (self.root / 'bridge_response.ready').unlink()
        restarted = State(self.root, self.state.token)
        self.assertEqual(restarted.next(self.cid)[1]['status'], 'DELIVERED')
        self.assertEqual(restarted.submit(self.body(self.response()))[0], 409)

    def test_interrupted_publication_requires_reconciliation(self):
        self.state.next(self.cid)
        atomic_json(self.state.intent_file(self.ident), {'handoff_id': self.ident})
        restarted = State(self.root, self.state.token)
        self.assertEqual(restarted.next(self.cid)[1]['error'], 'UNCERTAIN_RESPONSE_PUBLICATION')
        self.assertEqual(restarted.submit(self.body(self.response()))[0], 409)


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""Check that the offline grader rejects unsafe or incomplete proposed traces."""

import unittest

from eval_cases import export, grade, load_cases


class EvaluationTest(unittest.TestCase):
    def setUp(self):
        self.cases = load_cases()
        self.case = next(c for c in self.cases if c['id'] == 'new-zh')
        self.result = {'id': 'new-zh', 'action': 'rename',
                       'title': '🐛 修复 | 270101 | 登录回调失败', 'verified': True,
                       'trace': ['read', 'write', 'readback'], 'reason': 'Confirmed first turn; Shanghai date and matching readback.'}

    def test_export_hides_expectations_and_routes_actual_hook(self):
        inputs = export(self.cases)['cases']
        self.assertTrue(all(set(case) == {'id', 'input'} for case in inputs))
        by_id = {case['id']: case['input'] for case in inputs}
        self.assertIsNone(by_id['subagent']['trusted_hook'])
        self.assertIn('source=resume', by_id['resume']['trusted_hook'])
        self.assertNotIn('set_thread_title', by_id['claude-new']['trusted_hook'])

    def test_rejects_missing_reads_repeated_writes_wrong_dates_and_false_verification(self):
        self.assertEqual(grade([self.case], [self.result])['passed'], 1)
        for change in ({'trace': ['write', 'readback']}, {'trace': ['read', 'write']},
                       {'trace': ['read', 'write', 'readback', 'write', 'readback']},
                       {'title': '🐛 修复 | 261231 | 登录回调失败'}, {'verified': 'true'}):
            with self.subTest(change=change):
                self.assertEqual(grade([self.case], [{**self.result, **change}])['passed'], 0)
        protected = next(c for c in self.cases if c['id'] == 'user-title')
        self.assertEqual(grade([protected], [{**self.result, 'id': protected['id']}])['passed'], 0)
        failed = next(c for c in self.cases if c['id'] == 'failed-readback')
        self.assertEqual(grade([failed], [{**self.result, 'id': failed['id']}])['passed'], 0)
        conflict = next(c for c in self.cases if c['id'] == 'external-before-write')
        self.assertEqual(grade([conflict], [{**self.result, 'id': conflict['id'],
                         'action': 'conflict', 'verified': False, 'trace': ['read']}])['passed'], 0)

    def test_missing_duplicate_and_unknown_results_cannot_pass(self):
        self.assertEqual(grade([self.case], [])['passed'], 0)
        for rows in ([self.result, self.result], [{**self.result, 'id': 'unknown'}]):
            with self.assertRaises(ValueError):
                grade([self.case], rows)

    def test_missing_date_can_preserve_but_cannot_invent_a_draft_date(self):
        case = next(c for c in self.cases if c['id'] == 'missing-date')
        result = {**self.result, 'id': case['id'], 'action': 'preserve',
                  'title': case['input']['current_title'], 'verified': False, 'trace': ['read']}
        self.assertEqual(grade([case], [result])['passed'], 1)
        draft = {**result, 'action': 'candidate', 'title': '🐛 修复 | 270101 | 登录回调失败'}
        self.assertEqual(grade([case], [draft])['passed'], 0)


if __name__ == '__main__':
    unittest.main()

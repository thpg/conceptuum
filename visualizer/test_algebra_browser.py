"""Read-only Q40 browser checks. Start the Go server and Python worker first."""
import json
import os
import unittest
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright, expect


BASE = os.environ.get('CONCEPTUUM_TEST_URL', 'http://127.0.0.1:7100').rstrip('/')


class AlgebraBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        options = {'headless': True}
        if os.environ.get('CONCEPTUUM_BROWSER_CHANNEL'):
            options['channel'] = os.environ['CONCEPTUUM_BROWSER_CHANNEL']
        cls.browser = cls.playwright.chromium.launch(**options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1440, 'height': 1000})
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def open(self, expression=None, **kwargs):
        params = dict(lang='en', **kwargs)
        if expression is not None:
            params['expr'] = expression
        self.page.goto(BASE + '/algebra?' + urlencode(params))
        self.ready()

    def ready(self):
        expect(self.page.locator('#algebra-results')).to_have_attribute('aria-busy', 'false', timeout=25000)

    def submit(self, expression, within=''):
        self.page.locator('#expression').fill(expression)
        self.page.locator('#algebra-within').fill(within)
        self.page.locator('#algebra-run').click()
        self.ready()

    def result(self):
        return json.loads(self.page.locator('#algebra-json').text_content())

    def test_intersection_evidence_and_download(self):
        self.open()
        self.assertEqual(self.result()['result']['ids'], [25447])
        self.page.get_by_role('button', name='Explain glass food storage jar', exact=True).click()
        self.ready()
        expect(self.page.locator('#algebra-explanation')).to_contain_text('Edge #37656')
        expect(self.page.locator('#algebra-explanation')).to_contain_text('Edge #37734')
        with self.page.expect_download() as download_info:
            self.page.locator('#algebra-download').click()
        with open(download_info.value.path(), encoding='utf-8') as stream:
            data = json.load(stream)
        self.assertEqual(data['result']['ids'], [25447])
        self.assertEqual(data['result']['source']['data_revision'], 'Q40')
        self.assertEqual(data['result']['explanation']['concept']['id'], 25447)
        self.assertEqual(data['schema'], 'conceptuum.algebra.example.v1')

    def test_every_demo_and_negative_exception(self):
        self.open()
        for name, kind in [('material', 'set'), ('exception', 'set'), ('parents', 'set'),
                           ('counterexample', 'boolean'), ('unknown', 'set'),
                           ('subset', 'boolean'), ('complement', 'set'), ('count', 'integer')]:
            self.page.locator('#algebra-demo').select_option(name)
            self.ready()
            data = self.result()['result']
            self.assertEqual(data['kind'], kind)
            self.assertEqual(self.page.locator('#algebra-error').is_visible(), False)
            if name == 'material':
                self.assertEqual(data['count'], 4)
            if name == 'exception':
                self.assertEqual(data['ids'], [1354])
                self.page.locator('.explain-button').click()
                self.ready()
                expect(self.page.locator('#algebra-explanation')).to_contain_text('explicit negative')
                expect(self.page.locator('#algebra-explanation')).to_contain_text('overridden')
            if name == 'parents':
                self.assertEqual(data['ids'], [25439, 25446])
            if name == 'subset':
                self.assertIs(data['value'], True)
            if name == 'counterexample':
                self.assertIs(data['value'], False)
            if name == 'unknown':
                self.assertEqual(data['ids'], [1354])
            if name == 'count':
                self.assertEqual(data['value'], 1)

    def test_homonyms_in_expression_and_domain(self):
        self.open('en:"glass"')
        expect(self.page.locator('#algebra-candidates button')).to_have_count(2)
        self.page.locator('#algebra-candidates button').filter(has_text='#90 ·').click()
        self.ready()
        expect(self.page.locator('#expression')).to_have_value('#90')
        self.submit('U', 'en:"glass"')
        expect(self.page.locator('#algebra-error-message')).to_contain_text('Within domain:')
        self.page.locator('#algebra-candidates button').filter(has_text='#90 ·').click()
        self.ready()
        expect(self.page.locator('#expression')).to_have_value('U')
        expect(self.page.locator('#algebra-within')).to_have_value('#90')

    def test_paging_complete_export_and_share_reload(self):
        self.open('U', within='#16')
        first = self.result()['result']
        self.assertGreater(first['count'], 25)
        self.assertEqual(len(first['ids']), first['count'])
        self.page.locator('#algebra-next').click()
        self.ready()
        second = self.result()['result']
        self.assertEqual(second['offset'], 25)
        self.assertEqual(second['ids'], first['ids'])
        self.assertNotEqual(second['items'], first['items'])
        self.page.reload()
        self.ready()
        expect(self.page.locator('#algebra-within')).to_have_value('#16')
        self.assertEqual(self.result()['result']['ids'], first['ids'])

    def test_search_insert_and_mobile_layout(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.open()
        self.page.locator('#algebra-clear').click()
        self.page.locator('#algebra-search').fill('glass jar')
        expect(self.page.locator('.lookup-result').first).to_be_visible()
        self.page.locator('.lookup-result').filter(has_text='#25439 ·').click()
        expect(self.page.locator('#expression')).to_have_value('#25439')
        self.page.locator('#algebra-run').click()
        self.ready()
        self.assertIn(25447, self.result()['result']['ids'])
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        self.page.locator('#expression').fill('#25439 &')
        expect(self.page.locator('#algebra-download')).to_be_disabled()
        self.page.locator('#algebra-run').click()
        self.ready()
        expect(self.page.locator('#algebra-error')).to_be_visible()
        expect(self.page.locator('#result-content')).to_be_hidden()

    def test_late_response_does_not_restore_stale_export(self):
        self.open()
        self.page.evaluate('''() => {
            const original = window.fetch;
            window.fetch = async (...args) => {
                if (args[0] !== '/api/algebra') return original(...args);
                const response = await original(...args);
                await new Promise(resolve => setTimeout(resolve, 800));
                return response;
            };
        }''')
        self.page.locator('#expression').fill('#25439')
        self.page.locator('#algebra-run').click()
        self.page.locator('#expression').fill('#25446')
        self.page.wait_for_timeout(1100)
        expect(self.page.locator('#result-content')).to_be_hidden()
        expect(self.page.locator('#algebra-download')).to_be_disabled()
        expect(self.page.locator('#collection-add')).to_be_disabled()
        expect(self.page.locator('#algebra-status')).to_contain_text('Expression changed')

    def test_counterexample_inspection_and_shared_evidence(self):
        self.open('#25439 <= #25446')
        expect(self.page.locator('.counterexample-label')).to_have_text('Counterexamples')
        self.page.locator('.counterexamples .diagnostic-sample').click()
        self.ready()
        data = self.result()['result']
        self.assertIs(data['value'], False)
        self.assertEqual(data['explanation']['concept']['id'], 25439)
        self.assertEqual([branch['member'] for branch in data['explanation']['operands']], [True, False])
        self.assertIn('explain=25439', self.page.url)
        self.page.reload()
        self.ready()
        expect(self.page.locator('#algebra-explanation')).to_be_visible()
        expect(self.page.locator('#algebra-explanation')).to_contain_text('Expression result: false')
        self.submit('#25439 < #25439')
        expect(self.page.locator('.diagnostic-note')).to_contain_text('equal')
        expect(self.page.locator('.counterexample-label')).to_have_count(0)

    def test_arbitrary_nonmember_and_count_inspection(self):
        self.open('has(action, #209)')
        self.page.locator('#inspect-id').fill('#1354')
        self.page.get_by_role('button', name='Inspect', exact=True).click()
        self.ready()
        expect(self.page.locator('#algebra-explanation')).to_contain_text('Not included in this result.')
        self.assertEqual(self.result()['result']['explanation']['fact']['state'], 'negative')
        self.submit('count(#24488 & #24489)')
        self.page.locator('.diagnostic-sample').click()
        self.ready()
        proof = self.result()['result']['explanation']
        self.assertEqual(proof['value'], 1)
        self.assertTrue(proof['operands'][0]['member'])
        self.assertEqual(proof['concept']['id'], 24492)

    def test_collection_jsonl_restore_replay_and_remove(self):
        self.open()
        question = 'Which records belong to both?\n"Quoted" <script>window.bad = true</script>'
        self.page.locator('#example-question').fill(question)
        self.page.locator('#collection-add').click()
        expect(self.page.locator('#collection-count')).to_have_text('1')
        self.page.locator('#collection-add').click()
        expect(self.page.locator('#collection-count')).to_have_text('1')
        expect(self.page.locator('#collection-status')).to_contain_text('already')
        self.submit('#25439 <= #25446')
        self.page.locator('#example-question').fill('Are all stored glass jars food storage jars?')
        self.page.locator('#collection-add').click()
        expect(self.page.locator('#collection-count')).to_have_text('2')
        self.page.reload()
        self.ready()
        expect(self.page.locator('#collection-count')).to_have_text('2')
        with self.page.expect_download() as download_info:
            self.page.locator('#collection-download').click()
        with open(download_info.value.path(), encoding='utf-8') as stream:
            lines = stream.readlines()
        self.assertEqual(len(lines), 2)
        saved = [json.loads(line) for line in lines]
        self.assertEqual(saved[0]['question'], question)
        self.assertEqual(saved[0]['result']['ids'], [25447])
        self.assertIs(saved[1]['result']['value'], False)
        self.assertEqual(saved[1]['result']['diagnostics']['regions'][0]['count'], 1)
        self.assertEqual(saved[0]['result']['source']['data_revision'], 'Q40')
        self.assertIsNone(self.page.evaluate('window.bad'))
        self.page.locator('.collection-replay').first.click()
        self.ready()
        expect(self.page.locator('#expression')).to_have_value('#25439 & #25446')
        expect(self.page.locator('#example-question')).to_have_value(question)
        expect(self.page.locator('#collection-count')).to_have_text('2')
        self.page.get_by_role('button', name='Remove example 1', exact=True).click()
        expect(self.page.locator('#collection-count')).to_have_text('1')
        self.page.reload()
        self.ready()
        expect(self.page.locator('#collection-count')).to_have_text('1')

    def test_collection_without_storage_and_mobile_diagnostics(self):
        self.page.add_init_script("Storage.prototype.getItem = function() { throw new Error('blocked'); };")
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.open('#25439 <= #25446')
        self.page.locator('#collection-add').click()
        expect(self.page.locator('#collection-count')).to_have_text('1')
        expect(self.page.locator('#collection-storage')).to_contain_text('page session')
        with self.page.expect_download():
            self.page.locator('#collection-download').click()
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        self.page.reload()
        self.ready()
        expect(self.page.locator('#collection-count')).to_have_text('0')

    def test_question_stays_local_and_stale_result_cannot_be_saved(self):
        requests = []
        self.page.on('request', lambda request: requests.append(request.post_data) if request.url.endswith('/api/algebra') else None)
        self.open()
        question = 'A private draft question with a unique marker 735829'
        self.page.locator('#example-question').fill(question)
        self.page.locator('#expression').fill('count(#24488 & #24489)')
        expect(self.page.locator('#collection-add')).to_be_disabled()
        self.page.locator('#algebra-run').click()
        self.ready()
        self.page.locator('#collection-add').click()
        expect(self.page.locator('#collection-count')).to_have_text('1')
        self.assertTrue(requests)
        self.assertTrue(all(question not in request for request in requests))


if __name__ == '__main__':
    unittest.main(verbosity=2)

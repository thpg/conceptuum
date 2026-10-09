"""Read-only Q39 browser checks. Start the Go server and Python worker first."""
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
        self.assertEqual(data['result']['source']['data_revision'], 'Q39')
        self.assertEqual(data['result']['explanation']['concept']['id'], 25447)
        self.assertEqual(data['schema'], 'conceptuum.algebra.example.v1')

    def test_every_demo_and_negative_exception(self):
        self.open()
        for name, kind in [('material', 'set'), ('exception', 'set'), ('parents', 'set'),
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
        expect(self.page.locator('#algebra-status')).to_contain_text('Expression changed')


if __name__ == '__main__':
    unittest.main(verbosity=2)

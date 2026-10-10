"""Read-only QA generator browser checks against a running Q40 site."""
import json
import os
import unittest

from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('CONCEPTUUM_TEST_URL', 'http://127.0.0.1:7100').rstrip('/')


class TrainingBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        options = dict(headless=True)
        if os.environ.get('CONCEPTUUM_BROWSER_CHANNEL'):
            options['channel'] = os.environ['CONCEPTUUM_BROWSER_CHANNEL']
        cls.browser = cls.playwright.chromium.launch(**options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport=dict(width=1440, height=1000))
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def ready(self):
        expect(self.page.locator('#qa-results')).to_have_attribute('aria-busy', 'false', timeout=30000)

    def open(self, query=''):
        self.page.goto(BASE + '/training' + query)
        self.ready()

    def download(self, selector, jsonl=True):
        with self.page.expect_download() as event:
            self.page.locator(selector).click()
        with open(event.value.path(), encoding='utf-8') as stream:
            return [json.loads(line) for line in stream] if jsonl else json.load(stream)

    def test_default_batch_evidence_selection_and_both_exports(self):
        self.open()
        expect(self.page.locator('.qa-example')).to_have_count(20)
        full = self.download('#qa-annotated')
        self.assertEqual(len(full), 20)
        self.assertTrue(all(r['quality']['answer_recomputed_from_input'] for r in full))
        self.assertTrue(all(r['source']['data_revision'] == 'Q40' for r in full))
        self.page.locator('.qa-example input').first.uncheck()
        selected = self.download('#qa-annotated')
        self.assertEqual(selected, full[1:])
        self.assertEqual(self.download('#qa-chat'), [dict(messages=r['messages']) for r in selected])
        report = self.download('#qa-report-download', jsonl=False)
        self.assertEqual(report['exported'], 19)
        self.assertEqual(report['excluded_ids'], [full[0]['id']])
        self.page.locator('.qa-example summary').first.click()
        expect(self.page.locator('.qa-example pre').first).to_contain_text('Facts:')

    def test_algebra_link_replays_the_exported_expression(self):
        self.open()
        records = self.download('#qa-annotated')
        index = next(i for i,r in enumerate(records) if r['algebra'])
        card = self.page.locator('.qa-example').nth(index)
        card.locator('summary').click()
        with self.context.expect_page() as event:
            card.locator('a').click()
        algebra = event.value
        expect(algebra.locator('#algebra-results')).to_have_attribute('aria-busy','false',timeout=25000)
        expect(algebra.locator('#expression')).to_have_value(records[index]['algebra']['expression'])
        expect(algebra.locator('#algebra-error')).to_be_hidden()

    def test_russian_content_and_preset_with_explicit_negative(self):
        self.open('?lang=ru')
        expect(self.page.locator('.qa-example').first).to_have_attribute('lang','ru')
        self.assertTrue(any('поняти' in text for text in self.page.locator('.qa-question').all_text_contents()))
        self.page.locator('#qa-preset').select_option('flight')
        self.page.locator('#qa-run').click()
        self.ready()
        records = self.download('#qa-annotated')
        self.assertTrue(any(r['task']=='property' and r['expected']['value']=='negative' for r in records))

    def test_empty_context_reports_shortfall_and_disables_training_export(self):
        self.open()
        self.page.locator('#qa-context').select_option('2')
        self.page.locator('#qa-run').click()
        self.ready()
        expect(self.page.locator('#qa-status')).to_contain_text('Only 0 of 20')
        expect(self.page.locator('#qa-chat')).to_be_disabled()
        self.assertFalse(self.download('#qa-report-download', jsonl=False)['complete'])

    def test_network_error_is_visible_and_stale_export_is_disabled(self):
        self.open()
        self.page.route('**/api/qa/generate', lambda route: route.fulfill(status=503, content_type='application/json', body='{"error":{"message":"Temporarily unavailable"}}'))
        self.page.locator('#qa-run').click()
        self.ready()
        expect(self.page.locator('#qa-error')).to_have_text('Temporarily unavailable')
        expect(self.page.locator('#qa-chat')).to_be_disabled()
        expect(self.page.locator('#qa-run')).to_be_enabled()

    def test_rendered_questions_are_text_and_mobile_has_no_overflow(self):
        self.open()
        records = self.download('#qa-annotated')
        record = records[0]
        record['question'] = '<img src=x onerror="window.qaInjected=true">'
        payload = dict(schema='conceptuum.qa.batch.v1', records=[record], report=dict(requested=1, generated=1, complete=True, source=record['source'], tasks={record['task']:1}, property_states={}))
        self.page.route('**/api/qa/generate', lambda route: route.fulfill(content_type='application/json', body=json.dumps(payload)))
        self.page.locator('#qa-run').click()
        self.ready()
        expect(self.page.locator('.qa-question')).to_have_text(record['question'])
        self.assertFalse(self.page.evaluate('Boolean(window.qaInjected)'))
        self.page.set_viewport_size(dict(width=375,height=850))
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        expect(self.page.locator('#qa-run')).to_be_visible()


if __name__ == '__main__':
    unittest.main()

"""Wiring integrity tests.

Ensures the form HTML, JS fetch call, and backend route all stay in sync.
These tests parse files directly - no server needed, no credentials needed.
If any of these fail after a merge, the contact form is broken.
"""
import os
import re
import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..')
FRONTEND = os.path.join(ROOT, 'frontend')
BACKEND = os.path.join(ROOT, 'backend')


def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


class TestFormFieldSync:
    """Ensure contact.html form fields match what app.py expects."""

    def test_contact_form_has_quoteForm_id(self):
        html = read_file(os.path.join(FRONTEND, 'contact.html'))
        assert 'id="quoteForm"' in html, "contact.html must have a form with id='quoteForm'"

    def test_contact_form_has_formSuccess_id(self):
        html = read_file(os.path.join(FRONTEND, 'contact.html'))
        assert 'id="formSuccess"' in html, "contact.html must have a div with id='formSuccess'"

    def test_contact_form_has_required_name_fields(self):
        """Form must have inputs with name= matching what app.py reads from request.form."""
        html = read_file(os.path.join(FRONTEND, 'contact.html'))
        required_names = ['name', 'email', 'message']
        for field_name in required_names:
            assert f'name="{field_name}"' in html, \
                f"contact.html missing form field with name='{field_name}'"

    def test_contact_form_has_optional_fields(self):
        html = read_file(os.path.join(FRONTEND, 'contact.html'))
        optional_names = ['phone', 'grade']
        for field_name in optional_names:
            assert f'name="{field_name}"' in html, \
                f"contact.html missing form field with name='{field_name}'"

    def test_backend_reads_matching_fields(self):
        """app.py must read the same field names the form sends."""
        py = read_file(os.path.join(BACKEND, 'app.py'))
        expected_fields = ['name', 'email', 'phone', 'grade', 'message']
        for field_name in expected_fields:
            assert f"'{field_name}'" in py or f'"{field_name}"' in py, \
                f"app.py doesn't read form field '{field_name}'"


class TestJSBackendWiring:
    """Ensure main.js submits to the backend, not localStorage or console.log."""

    def _get_js(self):
        # Handle both main.js and app.js naming
        for name in ['main.js', 'app.js']:
            path = os.path.join(FRONTEND, 'js', name)
            if os.path.exists(path):
                return read_file(path)
        pytest.fail("No main.js or app.js found in frontend/js/")

    def test_js_fetches_submit_endpoint(self):
        js = self._get_js()
        assert "fetch('/submit'" in js or 'fetch("/submit"' in js, \
            "main.js must contain fetch('/submit') to hit the backend. " \
            "If this fails, the form is submitting to localStorage or nowhere."

    def test_js_sends_post_method(self):
        js = self._get_js()
        assert "'POST'" in js or '"POST"' in js, \
            "main.js must send a POST request"

    def test_js_uses_formdata(self):
        js = self._get_js()
        assert 'FormData' in js, \
            "main.js must use FormData to send form fields"

    def test_js_does_not_use_localstorage_for_submissions(self):
        js = self._get_js()
        assert 'localStorage' not in js, \
            "main.js must NOT use localStorage for form submissions. " \
            "This means the backend wiring was replaced with a demo stub."

    def test_js_references_quoteForm(self):
        js = self._get_js()
        assert 'quoteForm' in js, \
            "main.js must reference the quoteForm element"

    def test_js_references_formSuccess(self):
        js = self._get_js()
        assert 'formSuccess' in js, \
            "main.js must reference the formSuccess element"


class TestBackendRouteExists:
    """Ensure the /submit route exists in app.py."""

    def test_submit_route_defined(self):
        py = read_file(os.path.join(BACKEND, 'app.py'))
        assert "'/submit'" in py or '"/submit"' in py, \
            "app.py must define a /submit route"

    def test_submit_route_accepts_post(self):
        py = read_file(os.path.join(BACKEND, 'app.py'))
        assert "'POST'" in py or '"POST"' in py, \
            "The /submit route must accept POST requests"

    def test_resend_integration_exists(self):
        py = read_file(os.path.join(BACKEND, 'app.py'))
        assert 'resend' in py.lower(), \
            "app.py must use Resend for email delivery"

    def test_database_integration_exists(self):
        py = read_file(os.path.join(BACKEND, 'app.py'))
        assert 'Lead' in py and 'db_session' in py, \
            "app.py must save leads to the database"


class TestNoDeadLinks:
    """Ensure HTML pages don't link to deleted pages."""

    def _get_all_html_files(self):
        files = []
        for f in os.listdir(FRONTEND):
            if f.endswith('.html'):
                files.append(f)
        return files

    def test_no_links_to_why_us(self):
        """why-us.html was deleted in Torsten's redesign."""
        for html_file in self._get_all_html_files():
            content = read_file(os.path.join(FRONTEND, html_file))
            assert 'why-us.html' not in content, \
                f"{html_file} links to why-us.html which no longer exists"

    def test_all_internal_links_have_targets(self):
        """Every .html link should point to a file that exists."""
        existing_files = set(self._get_all_html_files())
        for html_file in self._get_all_html_files():
            content = read_file(os.path.join(FRONTEND, html_file))
            links = re.findall(r'href="([^"#]+\.html)"', content)
            for link in links:
                assert link in existing_files, \
                    f"{html_file} links to '{link}' which doesn't exist in frontend/"

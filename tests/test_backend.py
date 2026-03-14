"""Backend route tests for the /submit endpoint.

Tests form validation, DB writes, and email dispatch (mocked).
No real credentials needed - uses SQLite in-memory and mocks Resend.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Set required env vars before importing app
os.environ.setdefault('DATABASE_URL', 'sqlite:///test.db')
os.environ.setdefault('RESEND_API_KEY', 'test_key')


@pytest.fixture
def client():
    """Create a test client with an in-memory SQLite DB."""
    # Patch resend before importing app
    with patch.dict(os.environ, {'DATABASE_URL': 'sqlite://', 'RESEND_API_KEY': 'test_key'}):
        # Re-import app fresh each time
        import importlib
        import backend.app as app_module
        importlib.reload(app_module)

        app_module.app.config['TESTING'] = True

        # Create tables in the in-memory DB
        if app_module.db_session:
            from sqlalchemy import inspect
            inspector = inspect(app_module.engine)
            if not inspector.has_table('leads'):
                app_module.Base.metadata.create_all(app_module.engine)

        with app_module.app.test_client() as client:
            yield client, app_module


class TestSubmitRoute:
    """Tests for POST /submit."""

    def _post(self, client, data, ajax=True):
        headers = {'Accept': 'application/json'} if ajax else {}
        return client.post('/submit', data=data, headers=headers)

    def test_valid_submission(self, client):
        client, app_module = client
        with patch('resend.Emails.send') as mock_send:
            mock_send.return_value = {'id': 'test'}
            resp = self._post(client, {
                'name': 'Test Parent',
                'email': 'test@example.com',
                'phone': '(780) 555-1234',
                'grade': '10',
                'message': 'My child needs help with math.'
            })
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['success'] is True
            mock_send.assert_called_once()

    def test_missing_name(self, client):
        client, _ = client
        resp = self._post(client, {
            'name': '',
            'email': 'test@example.com',
            'message': 'Hello'
        })
        assert resp.status_code == 400

    def test_missing_email(self, client):
        client, _ = client
        resp = self._post(client, {
            'name': 'Test',
            'email': '',
            'message': 'Hello'
        })
        assert resp.status_code == 400

    def test_invalid_email(self, client):
        client, _ = client
        resp = self._post(client, {
            'name': 'Test',
            'email': 'not-an-email',
            'message': 'Hello'
        })
        assert resp.status_code == 400

    def test_missing_message(self, client):
        client, _ = client
        resp = self._post(client, {
            'name': 'Test',
            'email': 'test@example.com',
            'message': ''
        })
        assert resp.status_code == 400

    def test_invalid_phone(self, client):
        client, _ = client
        resp = self._post(client, {
            'name': 'Test',
            'email': 'test@example.com',
            'phone': '123',
            'message': 'Hello'
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'phone' in data['error'].lower() or 'digit' in data['error'].lower()

    def test_valid_submission_saves_to_db(self, client):
        client, app_module = client
        with patch('resend.Emails.send') as mock_send:
            mock_send.return_value = {'id': 'test'}
            self._post(client, {
                'name': 'DB Test',
                'email': 'db@example.com',
                'phone': '7805551234',
                'grade': '11',
                'message': 'Testing DB write'
            })
            if app_module.db_session:
                lead = app_module.db_session.query(app_module.Lead).filter_by(
                    email='db@example.com'
                ).first()
                assert lead is not None
                assert lead.full_name == 'DB Test'
                assert lead.grade == '11'

    def test_resend_called_with_correct_fields(self, client):
        client, _ = client
        with patch('resend.Emails.send') as mock_send:
            mock_send.return_value = {'id': 'test'}
            self._post(client, {
                'name': 'Email Test',
                'email': 'email@example.com',
                'phone': '',
                'grade': '9',
                'message': 'Check email fields'
            })
            call_args = mock_send.call_args[0][0]
            assert 'Email Test' in call_args['subject']
            assert 'Email Test' in call_args['html']
            assert 'email@example.com' in call_args['html']
            assert call_args['reply_to'] == 'email@example.com'

    def test_optional_phone_accepted(self, client):
        """Phone is optional - empty phone should not cause an error."""
        client, _ = client
        with patch('resend.Emails.send') as mock_send:
            mock_send.return_value = {'id': 'test'}
            resp = self._post(client, {
                'name': 'No Phone',
                'email': 'nophone@example.com',
                'phone': '',
                'message': 'No phone provided'
            })
            assert resp.status_code == 200

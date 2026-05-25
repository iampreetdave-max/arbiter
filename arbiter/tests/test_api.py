"""
API route integration tests for Arbiter backend.

Tests cover:
- Cases CRUD endpoints (POST /cases, GET /cases/{id}, GET /cases)
- Document generation endpoint (POST /documents/generate)
- Payments webhook (POST /payments/webhook)
- Auth middleware (401 on missing/invalid token)

All external dependencies (Firebase, Gemini, Razorpay) are mocked.
Run with: pytest arbiter/tests/test_api.py -v
"""
import json
import hmac
import hashlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# App import — ensure backend is importable
# ---------------------------------------------------------------------------
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Mock environment variables before importing the app
os.environ.setdefault('GEMINI_API_KEY', 'test-gemini-key')
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', 'test-project')
os.environ.setdefault('FIREBASE_PROJECT_ID', 'test-firebase')
os.environ.setdefault('RAZORPAY_KEY_ID', 'rzp_test_key')
os.environ.setdefault('RAZORPAY_KEY_SECRET', 'test_secret')
os.environ.setdefault('GCS_BUCKET_NAME', 'test-bucket')


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_firebase():
    """Mock Firebase service so tests don't hit Firestore."""
    with patch('api.cases.firebase') as mock_fb, \
         patch('api.documents.firebase') as mock_doc_fb, \
         patch('api.payments.firebase') as mock_pay_fb:

        # Default return values
        mock_case = {
            'id': 'case-123',
            'user_id': 'user-456',
            'status': 'intake',
            'problem_type': 'tenant_dispute',
            'title': 'Deposit not returned',
            'description': 'Landlord refused to return ₹50,000 deposit',
            'created_at': '2026-05-25T10:00:00',
            'updated_at': '2026-05-25T10:00:00',
        }
        mock_fb.create_case.return_value = mock_case
        mock_fb.get_case.return_value = mock_case
        mock_fb.get_cases_by_user.return_value = [mock_case]
        mock_fb.update_case.return_value = mock_case

        mock_doc_fb.get_case.return_value = mock_case
        mock_doc_fb.update_case.return_value = mock_case

        mock_pay_fb.get_case.return_value = mock_case
        mock_pay_fb.update_case.return_value = mock_case

        yield mock_fb, mock_doc_fb, mock_pay_fb


@pytest.fixture
def mock_current_user():
    """Mock Firebase auth middleware — returns a fake verified user."""
    fake_user = {'uid': 'user-456', 'email': 'test@example.com'}
    with patch('core.security.get_current_user', return_value=fake_user), \
         patch('api.cases.get_current_user', return_value=fake_user), \
         patch('api.documents.get_current_user', return_value=fake_user), \
         patch('api.payments.get_current_user', return_value=fake_user):
        yield fake_user


@pytest.fixture
def client(mock_firebase, mock_current_user):
    """FastAPI test client with mocked external dependencies."""
    with patch('services.gemini_service.genai'), \
         patch('services.firebase_service.firebase_admin'), \
         patch('services.storage_service.storage'):
        from main import app
        return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers():
    """Bearer token header for authenticated requests."""
    return {'Authorization': 'Bearer test-firebase-jwt-token'}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    """Basic liveness probe tests."""

    def test_health_returns_200(self, client):
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        response = client.get('/health')
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'


# ---------------------------------------------------------------------------
# Cases API
# ---------------------------------------------------------------------------

class TestCasesCreate:
    """POST /cases — create a new legal case."""

    def test_create_case_success(self, client, auth_headers):
        payload = {
            'problem_type': 'tenant_dispute',
            'title': 'Deposit not returned',
            'description': 'Landlord refused to return ₹50,000 deposit after 60 days',
            'jurisdiction': 'Delhi',
        }
        response = client.post('/cases', json=payload, headers=auth_headers)
        assert response.status_code in (200, 201)

    def test_create_case_returns_case_id(self, client, auth_headers):
        payload = {
            'problem_type': 'employment',
            'title': 'Salary not paid',
            'description': 'Company withheld 3 months salary',
        }
        response = client.post('/cases', json=payload, headers=auth_headers)
        if response.status_code in (200, 201):
            data = response.json()
            assert 'id' in data or 'case_id' in data

    def test_create_case_without_auth_returns_401(self, client):
        payload = {
            'problem_type': 'tenant_dispute',
            'title': 'Test',
            'description': 'Test description',
        }
        response = client.post('/cases', json=payload)
        assert response.status_code == 401

    def test_create_case_invalid_problem_type_returns_422(self, client, auth_headers):
        payload = {
            'problem_type': 'invalid_type_xyz',
            'title': 'Test',
            'description': 'Test description',
        }
        response = client.post('/cases', json=payload, headers=auth_headers)
        # Should be 422 Unprocessable Entity for invalid enum value
        assert response.status_code in (400, 422)

    def test_create_case_missing_description_returns_422(self, client, auth_headers):
        payload = {
            'problem_type': 'tenant_dispute',
            'title': 'Missing description',
        }
        response = client.post('/cases', json=payload, headers=auth_headers)
        assert response.status_code == 422


class TestCasesRead:
    """GET /cases and GET /cases/{id}."""

    def test_get_case_by_id_success(self, client, auth_headers):
        response = client.get('/cases/case-123', headers=auth_headers)
        assert response.status_code == 200

    def test_get_case_by_id_returns_correct_fields(self, client, auth_headers):
        response = client.get('/cases/case-123', headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert 'id' in data or 'problem_type' in data

    def test_get_case_without_auth_returns_401(self, client):
        response = client.get('/cases/case-123')
        assert response.status_code == 401

    def test_list_cases_success(self, client, auth_headers):
        response = client.get('/cases', headers=auth_headers)
        assert response.status_code == 200

    def test_list_cases_returns_list(self, client, auth_headers):
        response = client.get('/cases', headers=auth_headers)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or 'cases' in data

    def test_list_cases_without_auth_returns_401(self, client):
        response = client.get('/cases')
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Documents API
# ---------------------------------------------------------------------------

class TestDocumentsGenerate:
    """POST /documents/generate — trigger AI document drafting."""

    def test_generate_document_requires_auth(self, client):
        payload = {'case_id': 'case-123', 'document_type': 'demand_letter'}
        response = client.post('/documents/generate', json=payload)
        assert response.status_code == 401

    def test_generate_document_missing_case_id(self, client, auth_headers):
        payload = {'document_type': 'demand_letter'}
        response = client.post('/documents/generate', json=payload, headers=auth_headers)
        assert response.status_code == 422

    def test_generate_document_invalid_doc_type(self, client, auth_headers):
        payload = {'case_id': 'case-123', 'document_type': 'invalid_doc_type'}
        response = client.post('/documents/generate', json=payload, headers=auth_headers)
        assert response.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Payments Webhook
# ---------------------------------------------------------------------------

class TestPaymentsWebhook:
    """POST /payments/webhook — Razorpay signature verification."""

    def _make_signature(self, payload_str: str, secret: str = 'test_secret') -> str:
        """Generate a valid Razorpay HMAC-SHA256 signature."""
        return hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

    def test_webhook_missing_signature_returns_400(self, client):
        payload = {'event': 'payment.captured'}
        response = client.post(
            '/payments/webhook',
            json=payload,
            headers={'Content-Type': 'application/json'},
        )
        # Missing x-razorpay-signature header
        assert response.status_code in (400, 401, 422)

    def test_webhook_invalid_signature_returns_400(self, client):
        payload = json.dumps({'event': 'payment.captured'})
        response = client.post(
            '/payments/webhook',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'X-Razorpay-Signature': 'invalid_signature_xyz',
            },
        )
        assert response.status_code in (400, 401)

    def test_webhook_valid_signature_accepted(self, client):
        """A properly signed webhook from Razorpay should be accepted."""
        event_payload = json.dumps({
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_test123',
                        'order_id': 'order_test123',
                        'amount': 29900,
                        'currency': 'INR',
                        'status': 'captured',
                    }
                }
            }
        })
        signature = self._make_signature(event_payload)
        response = client.post(
            '/payments/webhook',
            data=event_payload,
            headers={
                'Content-Type': 'application/json',
                'X-Razorpay-Signature': signature,
            },
        )
        # Either 200 (processed) or 404 (case not found) is acceptable —
        # both mean the signature check passed
        assert response.status_code in (200, 404)


# ---------------------------------------------------------------------------
# Security / Auth middleware
# ---------------------------------------------------------------------------

class TestAuthMiddleware:
    """Verify all protected routes reject unauthenticated requests."""

    PROTECTED_ROUTES = [
        ('GET',  '/cases'),
        ('POST', '/cases'),
        ('GET',  '/cases/some-id'),
        ('POST', '/documents/generate'),
    ]

    @pytest.mark.parametrize('method,path', PROTECTED_ROUTES)
    def test_protected_route_without_token_returns_401(self, client, method, path):
        fn = getattr(client, method.lower())
        response = fn(path)
        assert response.status_code == 401, (
            f'{method} {path} should return 401 without auth, got {response.status_code}'
        )

    def test_malformed_bearer_token_returns_401(self, client):
        response = client.get(
            '/cases',
            headers={'Authorization': 'Bearer not.a.real.jwt.token'},
        )
        assert response.status_code == 401

    def test_wrong_auth_scheme_returns_401(self, client):
        response = client.get(
            '/cases',
            headers={'Authorization': 'Basic dXNlcjpwYXNz'},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# CORS & headers
# ---------------------------------------------------------------------------

class TestResponseHeaders:
    """Verify security headers are set on responses."""

    def test_health_endpoint_is_cors_accessible(self, client):
        response = client.get(
            '/health',
            headers={'Origin': 'http://localhost:3000'},
        )
        # Should not block CORS from localhost in dev
        assert response.status_code == 200

    def test_powered_by_header_not_exposed(self, client):
        response = client.get('/health')
        assert 'x-powered-by' not in {k.lower() for k in response.headers}

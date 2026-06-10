"""Validate contractor-related API endpoints using TestClient and seeded data.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
try:
    import email_validator  # type: ignore
except Exception:
    # Minimal stub for environments missing the optional email-validator package
    import types

    email_validator = types.SimpleNamespace()
    class EmailNotValidError(Exception):
        pass
    def validate_email(x):
        return {"email": x}
    email_validator.validate_email = validate_email
    email_validator.EmailNotValidError = EmailNotValidError
    import sys as _sys
    _sys.modules['email_validator'] = email_validator

import importlib.metadata as _importlib_metadata

# If the optional `email-validator` distribution is not installed in this
# environment, pydantic may call importlib.metadata.version('email-validator')
# which raises PackageNotFoundError. For this local validation script only
# we shim that call to return a plausible version to avoid import-time
# failures when loading the FastAPI app.
_orig_version = _importlib_metadata.version
def _version_shim(name: str, *a, **k):
    if name == 'email-validator':
        return '2.0.0'
    return _orig_version(name)
_importlib_metadata.version = _version_shim

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.core.auth import create_token_pair
from sqlalchemy import create_engine, text


def get_admin_token():
    url = settings.database_url.replace('+asyncpg', '+psycopg2')
    eng = create_engine(url)
    with eng.connect() as conn:
        row = conn.execute(text("select id,email,role from users where email='admin@asip.ai' limit 1")).first()
        if not row:
            raise SystemExit('admin user not found in DB; run seeds first')
        user_id, email, role = row
        tp = create_token_pair(str(user_id), email, role)
        return tp.access_token


def main():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    with TestClient(app) as client:
        # GET /contractors
        r = client.get('/contractors', headers=headers)
        print('GET /contractors ->', r.status_code, 'count=', len(r.json()) if r.status_code==200 else r.text)

        # GET /contractors/rankings
        r2 = client.get('/contractors/rankings?incident_type=water_leak&k=3', headers=headers)
        print('GET /contractors/rankings ->', r2.status_code)
        if r2.status_code==200:
            import json
            print(json.dumps(r2.json(), indent=2)[:1000])

        # POST /contractors (create new contractor)
        payload = {
            "name": "Test Contractor",
            "specializations": ["water"],
            "rating": 4.0,
            "avg_response_time_hrs": 5.0,
            "contact_info": {"phone": "", "email": "test@example.com"}
        }
        r3 = client.post('/contractors', json=payload, headers=headers)
        print('POST /contractors ->', r3.status_code)
        created = None
        if r3.status_code==201:
            created = r3.json()
            print('created id=', created.get('id'))

        # PUT /contractors/{id}
        if created:
            cid = created.get('id')
            payload2 = payload.copy()
            payload2['rating'] = 4.5
            r4 = client.put(f'/contractors/{cid}', json=payload2, headers=headers)
            print('PUT /contractors/{id} ->', r4.status_code)


if __name__ == '__main__':
    main()

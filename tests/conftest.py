import base64
import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.security.encryption import decrypt_credentials, encrypt_credentials
from app.security.sql_validator import validate_sql_v1

TEST_KEK = base64.b64encode(b"0" * 32).decode("ascii")


@pytest.fixture
def chinook_catalog() -> dict:
    return {
        "tables": [
            {
                "name": "customer",
                "columns": [
                    {"name": "customer_id", "type": "integer", "nullable": "NO"},
                    {"name": "country", "type": "text", "nullable": "YES"},
                    {"name": "support_rep_id", "type": "integer", "nullable": "YES"},
                ],
                "foreign_keys": [
                    {
                        "column": "support_rep_id",
                        "ref_table": "employee",
                        "ref_column": "employee_id",
                    }
                ],
            },
            {
                "name": "employee",
                "columns": [{"name": "employee_id", "type": "integer", "nullable": "NO"}],
                "foreign_keys": [],
            },
            {
                "name": "invoice",
                "columns": [
                    {"name": "invoice_id", "type": "integer", "nullable": "NO"},
                    {"name": "customer_id", "type": "integer", "nullable": "NO"},
                ],
                "foreign_keys": [
                    {
                        "column": "customer_id",
                        "ref_table": "customer",
                        "ref_column": "customer_id",
                    }
                ],
            },
            {
                "name": "artist",
                "columns": [{"name": "artist_id", "type": "integer", "nullable": "NO"}],
                "foreign_keys": [],
            },
            {
                "name": "album",
                "columns": [
                    {"name": "album_id", "type": "integer", "nullable": "NO"},
                    {"name": "artist_id", "type": "integer", "nullable": "NO"},
                ],
                "foreign_keys": [
                    {"column": "artist_id", "ref_table": "artist", "ref_column": "artist_id"}
                ],
            },
        ]
    }


@pytest.fixture
def kek_env(monkeypatch):
    monkeypatch.setenv("KEK_SECRET", TEST_KEK)
    monkeypatch.setenv(
        "METADATA_DATABASE_URL",
        os.getenv(
            "METADATA_DATABASE_URL",
            "postgresql+asyncpg://querypilot:querypilot@localhost:5435/querypilot_meta",
        ),
    )
    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def client(kek_env):
    from app.db.session import engine

    await engine.dispose()
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await engine.dispose()


def test_encryption_roundtrip():
    blob = encrypt_credentials("secret-pass", TEST_KEK)
    assert decrypt_credentials(blob, TEST_KEK) == "secret-pass"


def test_encryption_wrong_kek_fails():
    blob = encrypt_credentials("secret-pass", TEST_KEK)
    wrong = base64.b64encode(b"1" * 32).decode("ascii")
    with pytest.raises(Exception):
        decrypt_credentials(blob, wrong)


def test_sql_validator_rejects_drop():
    result = validate_sql_v1("DROP TABLE users")
    assert not result.valid


def test_sql_validator_injects_limit():
    result = validate_sql_v1("SELECT 1")
    assert result.valid
    assert "LIMIT" in (result.sanitized_sql or "").upper()

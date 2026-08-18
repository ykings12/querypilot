def test_settings_load_from_env(kek_env, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("SQL_MODEL", "llama-test")
    from app.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    assert settings.groq_api_key == "test-key"
    assert settings.sql_model == "llama-test"


def test_settings_defaults(kek_env):
    from app.config import get_settings

    settings = get_settings()
    assert settings.default_row_limit == 1000

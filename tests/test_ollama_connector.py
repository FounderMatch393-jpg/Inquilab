import types

from ollama_connector import OllamaConnector


def test_default_model_uses_tagged_ollama_name(monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_SMALL_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_WARMUP_MODEL", raising=False)
    connector = OllamaConnector()
    assert connector.model == "llama3.2:latest"
    assert connector.large_model == "llama3.2:latest"
    assert connector.small_model == "tinyllama:latest"
    assert connector.warmup_model == "tinyllama:latest"


def test_saved_config_is_used_for_connection_defaults(monkeypatch):
    for name in ("OLLAMA_HOST", "OLLAMA_PORT", "OLLAMA_SMALL_MODEL", "OLLAMA_WARMUP_MODEL", "OLLAMA_LARGE_MODEL", "OLLAMA_MODEL"):
        monkeypatch.delenv(name, raising=False)

    connector = OllamaConnector()

    assert connector.host == "localhost"
    assert connector.port == 11434
    assert connector.small_model == "tinyllama:latest"
    assert connector.large_model == "llama3.2:latest"


def test_explicit_small_and_large_models_are_configured(monkeypatch):
    connector = OllamaConnector(small_model="phi3:mini", large_model="qwen2.5:14b")

    assert connector.small_model == "phi3:mini"
    assert connector.large_model == "qwen2.5:14b"
    assert connector.warmup_model == "phi3:mini"
    assert connector.model == "qwen2.5:14b"


def test_chat_uses_large_working_model(monkeypatch):
    connector = OllamaConnector(large_model="qwen2.5:14b")
    monkeypatch.setattr(connector, "verify_connection", lambda: True)
    requests = {}

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"message": {"content": "done"}}

    def fake_post(url, **kwargs):
        requests["payload"] = kwargs["json"]
        return FakeResponse()

    monkeypatch.setattr("requests.post", fake_post)

    assert connector.chat([{"role": "user", "content": "work"}]) == "done"
    assert requests["payload"]["model"] == "qwen2.5:14b"


def test_chat_collects_streamed_chunks(monkeypatch):
    connector = OllamaConnector()
    monkeypatch.setattr(connector, "verify_connection", lambda: True)
    requests = {}

    class FakeResponse:
        status_code = 200

        @staticmethod
        def iter_lines(decode_unicode=True):
            return [
                '{"message":{"content":"hel"}}',
                '{"message":{"content":"lo"}}',
            ]

    def fake_post(url, **kwargs):
        requests["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr("requests.post", fake_post)

    assert connector.chat([{"role": "user", "content": "work"}]) == "hello"
    assert requests["kwargs"]["json"]["stream"] is True
    assert requests["kwargs"]["stream"] is True


def test_get_available_models_keeps_full_name(monkeypatch):
    connector = OllamaConnector()

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"models": [{"name": "llama3.2:latest"}, {"name": "mistral:7b"}]}

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: FakeResponse())
    assert connector.get_available_models() == ["llama3.2:latest", "mistral:7b"]


def test_warm_up_uses_small_model(monkeypatch):
    connector = OllamaConnector(model="llama3.2:latest", warmup_model="tinyllama")

    monkeypatch.setattr(connector, "get_available_models", lambda: ["tinyllama", "llama3.2:latest"])
    requests = {}

    class FakeResponse:
        status_code = 200

    def fake_post(url, **kwargs):
        requests["url"] = url
        requests["payload"] = kwargs["json"]
        requests["timeout"] = kwargs["timeout"]
        return FakeResponse()

    monkeypatch.setattr("requests.post", fake_post)

    assert connector.warm_up() is True
    assert requests["payload"]["model"] == "tinyllama"
    assert requests["payload"]["options"] == {"num_predict": 1}
    assert requests["timeout"] == 60


def test_warm_up_skips_missing_model(monkeypatch):
    connector = OllamaConnector(warmup_model="tinyllama")
    monkeypatch.setattr(connector, "get_available_models", lambda: ["llama3.2:latest"])
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError()))

    assert connector.warm_up() is True

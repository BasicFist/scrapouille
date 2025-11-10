"""
Unit tests for Model Fallback Chain
Tests automatic failover across multiple LLM models
"""
import pytest
from scraper.fallback import ModelConfig, ModelFallbackExecutor, DEFAULT_FALLBACK_CHAIN


class MockScraperSuccess:
    """Mock scraper that always succeeds"""
    def __init__(self, prompt, source, config):
        self.prompt = prompt
        self.source = source
        self.config = config

    def run(self):
        return {"data": "success", "model": self.config["llm"]["model"]}


class MockScraperFail:
    """Mock scraper that always fails"""
    def __init__(self, prompt, source, config):
        self.prompt = prompt
        self.source = source
        self.config = config

    def run(self):
        raise ValueError("Model unavailable")


class MockScraperEmpty:
    """Mock scraper that returns empty results"""
    def __init__(self, prompt, source, config):
        self.prompt = prompt
        self.source = source
        self.config = config

    def run(self):
        return {}


def test_model_config_to_graph_config():
    """Test ModelConfig converts correctly to graph config"""
    config = ModelConfig(name="qwen2.5-coder:7b")
    graph_config = config.to_graph_config()

    assert graph_config["llm"]["model"] == "ollama/qwen2.5-coder:7b"
    assert graph_config["llm"]["temperature"] == 0
    assert graph_config["llm"]["format"] == "json"
    assert graph_config["embeddings"]["model"] == "ollama/nomic-embed-text"


def test_default_fallback_chain():
    """Test default fallback chain is properly configured"""
    assert len(DEFAULT_FALLBACK_CHAIN) == 3
    assert DEFAULT_FALLBACK_CHAIN[0].name == "qwen2.5-coder:7b"
    assert DEFAULT_FALLBACK_CHAIN[1].name == "llama3.1"
    assert DEFAULT_FALLBACK_CHAIN[2].name == "deepseek-coder-v2"


def test_fallback_executor_success_first_attempt():
    """Test executor succeeds on first attempt"""
    executor = ModelFallbackExecutor()

    result, model_used, attempts = executor.execute_with_fallback(
        MockScraperSuccess,
        "test prompt",
        "http://test.com"
    )

    assert result["data"] == "success"
    assert attempts == 1
    assert model_used == "qwen2.5-coder:7b"


def test_fallback_executor_uses_fallback():
    """Test executor falls back to second model when first fails"""
    # Create custom chain where first model fails
    chain = [
        ModelConfig(name="failing-model"),
        ModelConfig(name="working-model"),
    ]
    executor = ModelFallbackExecutor(chain)

    # Mock: first fails, second succeeds
    call_count = [0]

    class MockScraperConditional:
        def __init__(self, prompt, source, config):
            self.prompt = prompt
            self.source = source
            self.config = config

        def run(self):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("First model failed")
            return {"data": "success from fallback"}

    result, model_used, attempts = executor.execute_with_fallback(
        MockScraperConditional,
        "test prompt",
        "http://test.com"
    )

    assert result["data"] == "success from fallback"
    assert attempts == 2
    assert model_used == "working-model"


def test_fallback_executor_all_models_fail():
    """Test executor raises RuntimeError when all models fail"""
    executor = ModelFallbackExecutor()

    with pytest.raises(RuntimeError) as exc_info:
        executor.execute_with_fallback(
            MockScraperFail,
            "test prompt",
            "http://test.com"
        )

    assert "All 3 models failed" in str(exc_info.value)


def test_fallback_executor_empty_result_triggers_fallback():
    """Test executor treats empty results as failure"""
    chain = [
        ModelConfig(name="empty-model"),
        ModelConfig(name="working-model"),
    ]
    executor = ModelFallbackExecutor(chain)

    call_count = [0]

    class MockScraperConditional:
        def __init__(self, prompt, source, config):
            self.prompt = prompt
            self.source = source
            self.config = config

        def run(self):
            call_count[0] += 1
            if call_count[0] == 1:
                return {}  # Empty result
            return {"data": "success"}

    result, model_used, attempts = executor.execute_with_fallback(
        MockScraperConditional,
        "test prompt",
        "http://test.com"
    )

    assert attempts == 2
    assert result["data"] == "success"


def test_fallback_executor_config_overrides():
    """Test config overrides are properly merged"""
    executor = ModelFallbackExecutor()

    result, model_used, attempts = executor.execute_with_fallback(
        MockScraperSuccess,
        "test prompt",
        "http://test.com",
        extraction_mode=False,  # Override
        custom_param="test"
    )

    assert result is not None
    assert attempts == 1


def test_fallback_executor_get_available_models():
    """Test getting list of available models"""
    executor = ModelFallbackExecutor()
    models = executor.get_available_models()

    assert len(models) == 3
    assert "qwen2.5-coder:7b" in models
    assert "llama3.1" in models
    assert "deepseek-coder-v2" in models


def test_fallback_executor_tracks_last_successful_model():
    """Test executor tracks last successful model"""
    executor = ModelFallbackExecutor()

    assert executor.last_successful_model is None

    executor.execute_with_fallback(
        MockScraperSuccess,
        "test prompt",
        "http://test.com"
    )

    assert executor.last_successful_model == "qwen2.5-coder:7b"

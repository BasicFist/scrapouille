"""
Model fallback orchestrator
Provides automatic failover across multiple LLM models
"""
from typing import Callable, Any, Optional, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a single model in the fallback chain"""
    name: str
    provider: str = "ollama"
    base_url: str = "http://localhost:11434"
    temperature: float = 0
    format: str = "json"

    def to_graph_config(self) -> dict:
        """Convert to scrapegraphai config format"""
        return {
            "llm": {
                "model": f"{self.provider}/{self.name}",
                "temperature": self.temperature,
                "format": self.format,
                "base_url": self.base_url,
            },
            "embeddings": {
                "model": "ollama/nomic-embed-text",
                "base_url": self.base_url,
            },
            "verbose": True,
        }


# Default fallback chain (ordered by speed/availability)
DEFAULT_FALLBACK_CHAIN = [
    ModelConfig(name="qwen2.5-coder:7b"),     # Primary (fastest, high quality)
    ModelConfig(name="llama3.1"),             # Fallback 1 (very fast)
    ModelConfig(name="deepseek-coder-v2"),   # Fallback 2 (slower, highest quality)
]


class ModelFallbackExecutor:
    """
    Executes scraping with automatic model fallback

    Example:
        executor = ModelFallbackExecutor(fallback_chain)
        result = executor.execute_with_fallback(scraper_func, url, prompt)
    """

    def __init__(self, fallback_chain: Optional[List[ModelConfig]] = None):
        self.fallback_chain = fallback_chain or DEFAULT_FALLBACK_CHAIN
        self.last_successful_model: Optional[str] = None

    def execute_with_fallback(
        self,
        scraper_class: type,
        prompt: str,
        source: str,
        **config_overrides
    ) -> Tuple[Any, str, int]:
        """
        Execute scraping with automatic fallback

        Args:
            scraper_class: SmartScraperGraph or similar
            prompt: Extraction prompt
            source: URL to scrape
            **config_overrides: Additional config (e.g., extraction_mode)

        Returns:
            Tuple of (result, model_used, attempt_count)

        Raises:
            RuntimeError: If all models in chain fail
        """
        last_exception = None

        for attempt, model_config in enumerate(self.fallback_chain, start=1):
            try:
                logger.info(f"Attempt {attempt}: Trying model {model_config.name}")

                # Build config
                graph_config = model_config.to_graph_config()
                graph_config.update(config_overrides)

                # Create scraper instance
                scraper = scraper_class(
                    prompt=prompt,
                    source=source,
                    config=graph_config
                )

                # Execute
                result = scraper.run()

                # Validate result
                if not result or result == {}:
                    raise ValueError("Empty result from scraper")

                # Success!
                self.last_successful_model = model_config.name
                logger.info(f"✓ Success with {model_config.name} on attempt {attempt}")

                return result, model_config.name, attempt

            except Exception as e:
                last_exception = e
                logger.warning(f"✗ Model {model_config.name} failed: {e}")

                # Continue to next model in chain
                continue

        # All models failed
        raise RuntimeError(
            f"All {len(self.fallback_chain)} models failed. "
            f"Last error: {last_exception}"
        )

    def get_available_models(self) -> list[str]:
        """Get list of model names in fallback chain"""
        return [m.name for m in self.fallback_chain]

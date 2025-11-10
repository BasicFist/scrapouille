"""
Simple integration test for batch processing
Tests basic functionality without complex mocking
"""

from scraper.batch import BatchConfig, BatchResult

def test_batch_config():
    """Test BatchConfig initialization"""
    config = BatchConfig(
        max_concurrent=10,
        timeout_per_url=60.0,
        continue_on_error=True
    )
    assert config.max_concurrent == 10
    assert config.timeout_per_url == 60.0
    assert config.continue_on_error is True
    print("✅ BatchConfig works")


def test_batch_result():
    """Test BatchResult creation"""
    result = BatchResult(
        url="http://test.com",
        index=0,
        success=True,
        data={"title": "Test"},
        execution_time=1.5,
        model_used="qwen",
        cached=False
    )
    assert result.url == "http://test.com"
    assert result.success is True
    assert result.data == {"title": "Test"}
    print("✅ BatchResult works")


if __name__ == "__main__":
    test_batch_config()
    test_batch_result()
    print("\n🎉 Basic integration tests passed!")

import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_kafka_producer():
    """Globally mocks the KafkaProducer so tests don't attempt to connect to Kafka."""
    with patch('shared_lib.kafka.producer.KafkaEventProducer') as mock_producer_class:
        mock_instance = MagicMock()
        mock_producer_class.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_celery_task():
    """Provides a utility to mock celery tasks cleanly."""
    def _mock_task(task_path):
        patcher = patch(task_path)
        mock = patcher.start()
        return mock, patcher
    return _mock_task

@pytest.fixture(autouse=True)
def mock_redis_cache():
    """Globally mock django cache to prevent Redis connection errors."""
    with patch('django.core.cache.cache.set') as mock_set, \
         patch('django.core.cache.cache.get') as mock_get, \
         patch('django.core.cache.cache.delete') as mock_delete:
        yield {
            'set': mock_set,
            'get': mock_get,
            'delete': mock_delete
        }

import logging
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

logger = logging.getLogger(__name__)

def is_temporary_failure(exception):
    """
    Returns True if the exception represents a temporary network/server error:
    - ConnectionError, Timeout
    - HTTPError with status code 429, 500, 502, 503, 504
    """
    if isinstance(exception, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return True
    if isinstance(exception, requests.exceptions.HTTPError):
        if exception.response is not None:
            status_code = exception.response.status_code
            if status_code in [429, 500, 502, 503, 504]:
                return True
    return False

def make_resilient_request(url, method='GET', service_name='Unknown', max_attempts=2, timeout=2, **kwargs):
    """
    Executes an HTTP request with retry logic and exponential backoff.
    
    Args:
        url: Request URL
        method: HTTP method (GET, POST, etc.)
        service_name: Name of target service for structured logging
        max_attempts: Number of total attempts before raising (default 2)
        timeout: Timeout per request in seconds (default 2)
    """
    def log_before_retry(retry_state):
        attempt_num = retry_state.attempt_number
        if attempt_num > 1:
            logger.warning(
                "Retrying %s. Attempt %d/%d",
                service_name, attempt_num, max_attempts
            )

    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception(is_temporary_failure),
        before=log_before_retry,
        reraise=True
    )
    def _execute():
        # Force the configured timeout
        kwargs['timeout'] = timeout
        resp = requests.request(method, url, **kwargs)
        # Raise HTTPError for retryable status codes so tenacity can retry
        if resp.status_code in [429, 500, 502, 503, 504]:
            resp.raise_for_status()
        return resp

    return _execute()

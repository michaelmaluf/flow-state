import json

from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QTimer
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


class BaseNetworkClient(QObject):
    response_received = pyqtSignal(str, dict)  # operation_type, response_data
    request_error = pyqtSignal(str, str)  # operation_type, error_message

    def __init__(self, base_url, timeout=10000, max_retries=3, retry_delay=2000):
        super().__init__()
        self.base_url = base_url.rstrip('/')  # Remove trailing slash
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.manager = QNetworkAccessManager(self)
        self.manager.setTransferTimeout(timeout)

    def get(self, endpoint, operation_type=None):
        return self._make_request('GET', endpoint, operation_type=operation_type)

    def post(self, endpoint, payload=None, operation_type=None):
        return self._make_request('POST', endpoint, payload=payload, operation_type=operation_type)

    def put(self, endpoint, payload=None, operation_type=None):
        return self._make_request('PUT', endpoint, payload=payload, operation_type=operation_type)

    def delete(self, endpoint, operation_type=None):
        return self._make_request('DELETE', endpoint, operation_type=operation_type)

    def _make_request(self, method, endpoint, payload=None, operation_type=None, attempt=1):
        """
        Generic method to make HTTP requests

        Args:
            method: HTTP method ('GET', 'POST', 'PUT', 'DELETE')
            endpoint: API endpoint (will be appended to base_url)
            payload: Dictionary to be JSON-encoded as request body
            operation_type: String identifier for this operation (for signals)

        Returns:
            QNetworkReply object
        """
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        url = QUrl(f"{self.base_url}{endpoint}")

        # Create request
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

        # Prepare payload
        if payload is not None:
            data = json.dumps(payload).encode('utf-8')
        else:
            data = b''

        # Make the request based on method
        if method.upper() == 'GET':
            reply = self.manager.get(request)
        elif method.upper() == 'POST':
            reply = self.manager.post(request, data)
        elif method.upper() == 'PUT':
            reply = self.manager.put(request, data)
        elif method.upper() == 'DELETE':
            reply = self.manager.deleteResource(request)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        retry_info = {
            'method': method,
            'endpoint': endpoint,
            'payload': payload,
            'operation_type': operation_type,
            'attempt': attempt
        }

        # Connect response handler
        operation_id = operation_type or endpoint
        reply.finished.connect(lambda: self._handle_response(reply, operation_id, retry_info))

        return reply

    def _handle_response(self, reply, operation_type, retry_info):
        """
        Generic response handler

        Subclasses can override this method to customize response handling
        """
        try:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                # Successful response
                data = reply.readAll().data()
                if data:
                    try:
                        response = json.loads(data.decode('utf-8'))
                    except json.JSONDecodeError:
                        # Handle non-JSON responses
                        response = {'raw_response': data.decode('utf-8')}
                else:
                    response = {}

                # Call the success handler
                self._handle_success(operation_type, response)
            else:
                if self._should_retry(reply, retry_info['attempt']):
                    self._schedule_retry(retry_info)
                else:
                    error_msg = reply.errorString()
                    status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)

                    error_data = reply.readAll().data()
                    if error_data:
                        try:
                            error_details = json.loads(error_data.decode('utf-8'))
                            error_msg += f" - {error_details}"
                        except json.JSONDecodeError:
                            pass

                    self._handle_error(operation_type, error_msg, status_code)

        except Exception as e:
            self._handle_error(operation_type, f"Response processing error: {str(e)}", None)
        finally:
            reply.deleteLater()

    def _handle_success(self, operation_type, response):
        raise NotImplementedError("Method must be overridden")

    def _handle_error(self, operation_type, error_msg, status_code):
        raise NotImplementedError("Method must be overridden")

    def _should_retry(self, reply, attempt):
        """Determine if request should be retried"""
        # Don't retry if we've exceeded max attempts
        if attempt >= self.max_retries - 1:
            return False

        error = reply.error()

        # Retry on network/connection errors
        retryable_errors = [
            QNetworkReply.NetworkError.ConnectionRefusedError,
            QNetworkReply.NetworkError.RemoteHostClosedError,
            QNetworkReply.NetworkError.HostNotFoundError,
            QNetworkReply.NetworkError.TimeoutError,
            QNetworkReply.NetworkError.OperationCanceledError,
            QNetworkReply.NetworkError.TemporaryNetworkFailureError,
            QNetworkReply.NetworkError.NetworkSessionFailedError,
            QNetworkReply.NetworkError.BackgroundRequestNotAllowedError,
        ]

        if error in retryable_errors:
            return True

        # Check HTTP status codes
        status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status_code:
            # Retry on server errors, no retry on client errors
            if 500 <= status_code < 600:
                return True

        return False

    def _schedule_retry(self, retry_info):
        """Schedule a retry attempt after delay"""
        retry_info['attempt'] += 1

        # Use QTimer to schedule retry after delay
        QTimer.singleShot(
            self.retry_delay,
            lambda: self._make_request(
                retry_info['method'],
                retry_info['endpoint'],
                retry_info['payload'],
                retry_info['operation_type'],
                retry_info['attempt']
            )
        )

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("app.middleware.logging")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log details about incoming HTTP requests and response times."""
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
        except Exception:
            # Errors will be handled by the global error handler, but we still want to log failure
            process_time_ms = (time.time() - start_time) * 1000
            logger.error(
                "Request failed: %s %s - Duration: %sms",
                request.method, request.url.path, round(process_time_ms, 2)
            )
            raise

        process_time_ms = (time.time() - start_time) * 1000
        
        # Log response status code and execution time
        logger.info(
            "%s %s - Status: %s - Process Time: %sms",
            request.method,
            request.url.path,
            response.status_code,
            round(process_time_ms, 2)
        )
        
        return response

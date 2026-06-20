# backend/exceptions.py (Loguru only)
import sys
from pprint import pprint
from loguru import logger
from rest_framework.views import exception_handler

# Configure loguru
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Get context information
        view = context.get("view")
        request = context.get("request")

        # Prepare log data
        log_data = {
            "view": view.__class__.__name__ if view else "Unknown",
            "method": request.method if request else "Unknown",
            "path": request.path if request else "Unknown",
            "user": str(request.user)
            if request and hasattr(request, "user")
            else "Anonymous",
            "status_code": response.status_code,
            "exception_type": type(exc).__name__,
            "response_data": response.data,
            "request_data": request.data
            if request and hasattr(request, "data")
            else {},
            "request_files": {
                key: {"name": file.name, "size": file.size, "type": file.content_type}
                for key, file in (
                    request.FILES.items()
                    if request and hasattr(request, "FILES")
                    else {}
                )
            },
        }

        # Log the error
        pprint(log_data)

    return response

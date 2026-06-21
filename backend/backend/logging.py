import os
from django.utils import timezone
from loguru import logger
from django.conf import settings


def get_vendor_logger(vendor_id: str):
    """
    Returns a plain-text contextual logger instance isolated by vendor_id.
    Guards against handler duplication to ensure clean, singular log traces.
    """
    current_date_str = timezone.now().strftime("%Y-%m-%d")

    log_dir = os.path.join(settings.MEDIA_ROOT, "compliance_vault", "logs", vendor_id)
    os.makedirs(log_dir, exist_ok=True)
    vendor_daily_log_file = os.path.join(log_dir, f"{current_date_str}.log")

    # CRITICAL FIX: Loop through registered handlers to see if this log file is already active
    handler_already_exists = False
    for handler_id, handler_instance in logger._core.handlers.items():
        # Check if the handler target is a file string matching our path
        if hasattr(handler_instance, "_sink") and hasattr(
            handler_instance._sink, "_file"
        ):
            if os.path.abspath(handler_instance._sink._file.name) == os.path.abspath(
                vendor_daily_log_file
            ):
                handler_already_exists = True
                break
        # Fallback raw string matching for standard sinks
        elif getattr(handler_instance, "_name", None) == vendor_daily_log_file:
            handler_already_exists = True
            break

    # Only attach a new plain-text pipe if it hasn't been configured yet
    if not handler_already_exists:
        logger.add(
            vendor_daily_log_file,
            format="[{time:HH:mm:ss}] | {level: <7} | {name}:{function}:{line} - {message}",
            filter=lambda record: record["extra"].get("vendor_id") == vendor_id,
            level="DEBUG",
            enqueue=True,
            serialize=False,
        )

    return logger.bind(vendor_id=vendor_id)

# filepath: backend/logging.py
import os
from django.utils import timezone
from loguru import logger
from django.conf import settings

# Register a custom AI level between DEBUG (10) and INFO (20)
AI_LEVEL_NO = 15
AI_LEVEL_NAME = "AI"

try:
    logger.level(AI_LEVEL_NAME, no=AI_LEVEL_NO, color="<cyan>", icon="🤖")
except TypeError:
    pass  # already registered on reloads


# Create a derived field that combines module function and line
patched_logger = logger.patch(
    lambda record: record["extra"].update(
        source=f"{record['name']}:{record['function']}:{record['line']}"
    )
)


def get_vendor_logger(vendor_id: str):
    current_date_str = timezone.now().strftime("%d-%m-%Y")
    log_dir = os.path.join(settings.MEDIA_ROOT, vendor_id, "logs")
    os.makedirs(log_dir, exist_ok=True)
    vendor_log_file = os.path.join(log_dir, f"{current_date_str}.log")
    vendor_json_log_file = os.path.join(log_dir, f"{current_date_str}.jsonl")   # NEW

    handler_already_exists = any(
        (
            hasattr(h, "_sink")
            and hasattr(h._sink, "_file")
            and os.path.abspath(h._sink._file.name) == os.path.abspath(vendor_log_file)
        )
        or getattr(h, "_name", None) == vendor_log_file
        for h in patched_logger._core.handlers.values()
    )

    if not handler_already_exists:
        patched_logger.add(
            vendor_log_file,
            format=("[{time:HH:mm:ss}] | {level:<7} | {extra[source]:<60} | {message}"),
            filter=lambda record: record["extra"].get("vendor_id") == vendor_id,
            level="DEBUG",
            enqueue=True,
            serialize=False,
        )

        # NEW: second sink, pure JSON lines, same filter/level
        patched_logger.add(
            vendor_json_log_file,
            filter=lambda record: record["extra"].get("vendor_id") == vendor_id,
            level="DEBUG",
            enqueue=True,
            serialize=True,   # <-- loguru emits one JSON object per line
        )

    bound = patched_logger.bind(vendor_id=vendor_id)

    def ai(message: str, **kwargs):
        bound.log(AI_LEVEL_NAME, message, **kwargs)

    bound.ai = ai
    bound.log_file = vendor_log_file
    bound.json_log_file = vendor_json_log_file   # NEW: expose path for tasks.py to save on the Vendor model
    return bound
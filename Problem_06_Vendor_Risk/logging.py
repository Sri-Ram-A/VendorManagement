# backend/logging.py
import os
import logging
import json
from datetime import datetime
from django.conf import settings

class JSONVendorFormatter(logging.Formatter):
    """Formats log records into flat, single-line JSON structures."""
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": f"{record.module}:{record.funcName}:{record.lineno}",
        }
        
        # If the user passed string formatting context, load it as event metadata
        if isinstance(record.msg, dict):
            log_data.update(record.msg)
        else:
            log_data["event"] = str(record.msg)
            
        # Capture any extra properties passed via logger.info(..., extra={})
        if hasattr(record, "extra_ctx"):
            log_data.update(record.extra_ctx)
            
        return json.dumps(log_data)

class StructuredVendorLogger:
    """Wrapper to safely route JSON structural traces to vendor media directories."""
    def __init__(self, vendor_id: str):
        self.vendor_id = vendor_id
        
        # Build matching directory target inside Django Media paths
        log_dir = os.path.join(settings.MEDIA_ROOT, vendor_id, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Output log file matching execution path
        self.log_file = os.path.join(log_dir, f"{datetime.now().strftime('%d-%m-%Y')}.log")
        
        # Core standard logger engine setup
        self.logger = logging.getLogger(f"vendor_{vendor_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers to prevent duplicate append states
        if not self.logger.handlers:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(JSONVendorFormatter())
            self.logger.addHandler(file_handler)

    def log_event(self, level: str, event_name: str, **kwargs):
        """Helper to enforce key-value payloads."""
        msg_payload = {"event": event_name}
        msg_payload.update(kwargs)
        
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(msg_payload)

    def info(self, event_name: str, **kwargs): self.log_event("INFO", event_name, **kwargs)
    def debug(self, event_name: str, **kwargs): self.log_event("DEBUG", event_name, **kwargs)
    def warning(self, event_name: str, **kwargs): self.log_event("WARNING", event_name, **kwargs)
    def error(self, event_name: str, **kwargs): self.log_event("ERROR", event_name, **kwargs)
    def critical(self, event_name: str, **kwargs): self.log_event("CRITICAL", event_name, **kwargs)

def get_vendor_logger(vendor_id: str) -> StructuredVendorLogger:
    return StructuredVendorLogger(vendor_id)
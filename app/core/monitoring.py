import time
import logging
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from pythonjsonlogger import jsonlogger

class JSONLogFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(JSONLogFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime())
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

def setup_logging():
    logger = logging.getLogger()
    logHandler = logging.StreamHandler()
    formatter = JSONLogFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)

class PerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log slow requests
        if process_time > 1.0:
            logging.getLogger("performance").warning(
                f"Slow Request: {request.method} {request.url.path} took {process_time:.4f}s"
            )
            
        response.headers["X-Process-Time"] = str(process_time)
        return response

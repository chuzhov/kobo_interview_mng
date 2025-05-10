# utils/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler

_logger = None

def setup_logger(service_name: str) -> logging.Logger:
    global _logger
    if _logger is None:
        # Create log directory if it doesn't exist
        if not os.path.exists('log'):
            os.makedirs('log')
        
        # Create a custom logger with a fixed name
        _logger = logging.getLogger(service_name)
        _logger.setLevel(logging.INFO)
        
        # Create handlers
        log_file_path = os.path.join('log', f'{service_name}.log')
        handler = RotatingFileHandler(
            log_file_path,
            maxBytes=1024*1024,  # 1MB
            backupCount=1,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter('%(asctime)s,%(levelname)s,%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        _logger.addHandler(handler)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        _logger.addHandler(console_handler)
    
    return _logger

logger = setup_logger(service_name="interview_durations")
__all__ = ['logger']
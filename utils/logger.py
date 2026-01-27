"""
Centralized logging utility for the VUS Life project.

This module provides a unified logging interface that can be used across
all scripts in the project. It supports individual log files per function
and automatic timestamp-based naming.

Usage:
    from backend.utils.logger import setup_logging
    
    # Individual function logging
    logger = setup_logging(function_name="my_function")
    logger.info("This goes to logs/my_function_YYYYMMDD_HHMMSS.log")
    
    # General logging
    logger = setup_logging()
    logger.info("This goes to logs/general.log")
    
    # Custom log file
    logger = setup_logging(log_file="/path/to/custom.log")
    logger.info("This goes to the specified file")
"""

import os
import logging


def setup_logging(log_file: str = None, logs_dir: str = 'logs', function_name: str = None):
    """
    Set up logging configuration with optional individual log file.
    
    Args:
        log_file: Optional path to individual log file
        function_name: Optional function name for log file naming
        
    Returns:
        Logger instance
    """
    # Generate log file name if not provided

    if function_name:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(logs_dir, f"{function_name}_{timestamp}.log")
    else:
        log_file = os.path.join(logs_dir, "general.log")

    # Ensure the directory for the log file exists
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(function_name or __name__)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to prevent duplicates
    logger.handlers.clear()
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter - simplified format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger to avoid duplicates
    logger.propagate = False
    
    logger.info(f"Logging initialized for {function_name or 'general'} - Log file: {log_file}")
    
    return logger
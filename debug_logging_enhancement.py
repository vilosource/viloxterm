#!/usr/bin/env python3
"""
Enhancement to add dedicated debug file logging.
"""

import logging.config

from logging_config import get_log_file_path


def add_debug_file_handler():
    """Add a dedicated debug file handler that captures all DEBUG logs."""

    log_file_path = get_log_file_path()
    if not log_file_path:
        print("File logging disabled, skipping debug handler")
        return

    # Ensure log directory exists
    log_file_path.mkdir(parents=True, exist_ok=True)
    debug_log_file = log_file_path / "debug.log"

    # Create debug file handler
    debug_handler = logging.handlers.RotatingFileHandler(
        filename=str(debug_log_file),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding="utf-8",
    )
    debug_handler.setLevel(logging.DEBUG)

    # Set detailed formatter for debug logs
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    debug_handler.setFormatter(formatter)

    # Add to root logger to catch all debug logs
    root_logger = logging.getLogger()
    root_logger.addHandler(debug_handler)

    print(f"Debug file handler added: {debug_log_file}")


if __name__ == "__main__":
    # Example usage
    import logging_config

    logging_config.setup_logging()
    add_debug_file_handler()

    # Test logging
    logger = logging.getLogger(__name__)
    logger.debug("This debug message should go to debug.log")
    logger.info("This info message goes to both files")

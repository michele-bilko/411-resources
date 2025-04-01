import logging
import sys

from flask import current_app, has_request_context


def configure_logger(logger):
    """
    Configure logger with necessary handlers and formatters.

    Sets up a logger to output logs to stderr with timestamps and
    adds Flask app handlers if context is a request

    Args:
        logger: logger instance to configure
    
    """
    logger.setLevel(logging.DEBUG)

    # Create a console handler that logs to stderr
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)

    # Create a formatter with a timestamp
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add the formatter to the handler
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    # We also need to add the handler to the Flask logger
    if has_request_context():
        app_logger = current_app.logger
        for handler in app_logger.handlers:
            logger.addHandler(handler)
import argparse
import logging
import os

def setup_logging():
    parser = argparse.ArgumentParser(description="Demonstration of Python logging")
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level"
    )
    parser.add_argument("--debug", action="store_const", const="DEBUG", dest="log_level")
    parser.add_argument("--quiet", action="store_const", const="ERROR", dest="log_level")
    parser.add_argument("--verbose", action="store_const", const="INFO", dest="log_level")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format='%(levelname)s: %(message)s')
    return logging.getLogger(__name__)

def main():
    logger = setup_logging()

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Show all logger levels
    logger.info("Current logger levels:")
    for name in logging.root.manager.loggerDict:
        logger.info(f"{name}: {logging.getLogger(name).level}")

if __name__ == "__main__":
    main()

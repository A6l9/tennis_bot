import sys


def get_logger(logger):
    logger.remove()
    logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", backtrace=False)
    return logger

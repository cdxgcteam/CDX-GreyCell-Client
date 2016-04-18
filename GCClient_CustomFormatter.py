import logging
import time

# Create UTC Formatter for console logging purposes:
class UTCFormatter(logging.Formatter):
    converter = time.gmtime


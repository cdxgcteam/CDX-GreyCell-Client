from fluent import handler
import logging
import time

# Create UTC Formatter for console logging purposes:
class UTCFormatter(logging.Formatter):
    converter = time.gmtime

# # Create UTC Formatter for Fluent logging purposes:
class UTCFluentFormatter(handler.FluentRecordFormatter):
    converter = time.gmtime
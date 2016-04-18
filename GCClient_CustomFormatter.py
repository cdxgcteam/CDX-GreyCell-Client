<<<<<<< HEAD
=======
from fluent import handler
>>>>>>> origin/master
import logging
import time

# Create UTC Formatter for console logging purposes:
class UTCFormatter(logging.Formatter):
    converter = time.gmtime

<<<<<<< HEAD
=======
# # Create UTC Formatter for Fluent logging purposes:
class UTCFluentFormatter(handler.FluentRecordFormatter):
    converter = time.gmtime
>>>>>>> origin/master

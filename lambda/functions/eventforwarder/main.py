from anlogger import Logger
_logger = Logger("eventforwarder", 'INFO')
logger = _logger.get()

from anlogger import Logger
logger_obj = Logger(name="eventforwarder", default_loglevel="INFO", fmt=None, syslog=None)
logger = logger_obj.get()

from .forwarder import Forwarder

fwdr = Forwarder(logger)

def lambda_handler(event, context):
  return fwdr.handle(event)

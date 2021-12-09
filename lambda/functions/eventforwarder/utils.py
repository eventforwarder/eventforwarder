import os
from anawsutils.sns import SNS

sns = SNS()
sns_arn =  os.environ["SNS_ADMIN"] if "SNS_ADMIN" in os.environ else None


def send_admin_sns(logger, subject, message):
  if sns_arn is None:
    logger.error("Environment variable SNS_ADMIN is not set")
    
  else:
    response = sns.send_sns(sns_arn, subject, message)
    return response


def handle_exception(logger, e, where=None, text=None, reraise=False):
  import traceback
  s = 'Exception "{}"{}:\n{}\n{}'.format(
    e, 
    f" at {where}" if where is not None else "", 
    '-'*60, 
    traceback.format_exc()
  )
  if text is not None:
    s += '\n\n' + text

  logger.error(s)

  try:
    send_admin_sns(logger, "Eventforwarder exception", s)
  except Exception as e:
    logger.error("Exception while sending admin message: "+str(e))

  if reraise is True:
    raise e
  
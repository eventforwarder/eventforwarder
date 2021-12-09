from botocore.exceptions import ClientError

from jinja2 import Template as JinjaTemplate


class Template(object):

  def __init__(self, ssmclient=None, path=None, text=None):
    if ssmclient is not None and path is not None:
      self.text = self._get_template(ssmclient, path)
    else:
      self.text = text

    if self.text is None:
      raise InvalidTemplateException(self.text)

    self._template = JinjaTemplate(
      self.text,
      variable_start_string = "{=",
      variable_end_string = "=}"
    )


  @property
  def template(self):
    return self._template


  @staticmethod
  def _get_template(ssm_client, path):
    try:
      v = ssm_client.get_parameter(Name=path)
      return v['Parameter']['Value']
    except ClientError as e:
      if e.response['Error']['Code'] == 'ParameterNotFound':
        raise TemplateNotFound()
      else:
        raise RetrieveTemplateException(e)
    

class InvalidTemplateException(Exception):
  pass


class RetrieveTemplateException(Exception):
  pass


class TemplateNotFound(Exception):
  pass
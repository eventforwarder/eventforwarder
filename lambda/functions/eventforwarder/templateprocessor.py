import json
from .template import Template

class TemplateProcessor(object):

  @classmethod
  def process(cls, template, data=None):
    # You can use a standard Jinja2 Template object or our builtin Template-object
    _template = template.template if isinstance(template, Template) else template

    try:
      datastr = json.dumps(data, indent=4)
    except:
      datastr = data

    return _template.render(data = data, datastr = datastr)
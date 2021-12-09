import json

from .dictutils import Dictutils


class Transformer(object):

  @classmethod
  def transform(cls, instructions, data):
    _instructions = instructions if isinstance(instructions, list) else [ instructions ]
    for instruction in _instructions:
      data = cls._transform(instruction, data)
    return data


  @classmethod
  def _transform(cls, instruction, data):
    a = instruction.split(':')
    op_name = a[0].lower()
    if op_name in cls.FUNC_MAP.keys():
      path = a[1]
      input_params = a[2] if len(a) > 2 else None
      fixed_params = cls.FUNC_MAP[op_name][1]
      f = cls.FUNC_MAP[op_name][0]
      _f = lambda x: f(x, input_params, fixed_params)
      return Dictutils.set_path(data, path, _f)
    else:
      return data


  @staticmethod
  def from_json(data, input_params, fixed_params):
    try:
      v = json.loads(data)
    except json.decoder.JSONDecodeError as e:
      v = "JSON error ({}): {}".format(e.msg, data)
    return v



  FUNC_MAP = {
    "json": (from_json.__func__, None)
  }
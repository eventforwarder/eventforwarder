from .dictutils import Dictutils, PathNotFound

from enum import Enum

class LogicOper(Enum):
  AND = 0,
  OR  = 1


class RuleSet(object):
  def __init__(self, items, logic_operator):
    self.items = items if isinstance(items, list) else [ items ]
    self.logic_operator = logic_operator


  def _check_results(self, data):
    results = []
    for item in self.items:
      try:
        v = Dictutils.get_path(data, item.path)
      except PathNotFound:
        v = None
    for item in self.items:      
      results.append(item.compare(v))
    return results
    

  def check(self, data):
    """
    Check if resultset's rules matches the request when evaluated against input.
    If it does, return True, else False.
    """
    results = self._check_results(data)
    if self.logic_operator == LogicOper.AND:
      return not (False in results or True not in results)
    elif self.logic_operator == LogicOper.OR:
      return (False not in results or True in results)
    else:
      raise NotImplementedError()




###############################################################################
    

class ANDRuleSet(RuleSet):
  def __init__(self, items):
    super().__init__(items, LogicOper.AND)


class ORRuleSet(RuleSet):
  def __init__(self, items):
    super().__init__(items, LogicOper.OR)


###############################################################################

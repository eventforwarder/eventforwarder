import re

from enum import Enum

class CompOper(Enum):
  EQ = 0,
  NE = 1,
  LT = 2,
  LE = 3,
  GT = 4,
  GE = 5,
  REGEX = 6


class RuleItem(object):
  def __init__(self, path, compoperator, value):
    if not isinstance(compoperator, CompOper):
      self.operator = CompOper[compoperator]
    else:
      self.operator = compoperator

    self.path  = path
    self.value = value

    
  def compare(self, comp_value):
    if ((self.operator == CompOper.EQ and self.value == comp_value) or
        (self.operator == CompOper.NE and self.value != comp_value) or
        (self.operator == CompOper.LT and self.value <  comp_value) or
        (self.operator == CompOper.LE and self.value <= comp_value) or
        (self.operator == CompOper.GT and self.value >  comp_value) or
        (self.operator == CompOper.GE and self.value >= comp_value)):
      return True
    elif self.operator == CompOper.REGEX:
      return re.search(self.value, comp_value) is not None
    else:
      return False



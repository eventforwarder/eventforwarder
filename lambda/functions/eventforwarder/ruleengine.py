from .rulecollection import RuleCollection
from .ruleset import ANDRuleSet, ORRuleSet
from .ruleitem import RuleItem
from .transform import Transformer

class RuleEngine(object):

  def __init__(self, rules_dict):
    self.rulecollections = []
    self._generate(rules_dict)


  def _generate(self, rules_dict):
    i = 0
    for rule in rules_dict:
      i += 1
      res = { **rule }
      del res["rulesets"]
      name = "autogen{}".format(i)
      ruleset_list = []
      for k, v in rule["rulesets"].items():
        if k.lower() == 'or':
          rsc = ORRuleSet
        elif k.lower() == 'and':
          rsc = ANDRuleSet
        else:
          continue

        ruleitem_list = []
        for ritem in v:
          ruleitem_list.append(RuleItem(*ritem))

        ruleset_list.append(rsc(ruleitem_list))
      
      self.rulecollections.append(RuleCollection(name, ruleset_list, res))

  
  def evaluate(self, input_data):

    for rc in self.rulecollections:
      r = rc.check(input_data)
      if r is None:
        continue

      result = {
        **r, 
        "body": input_data 
      }

      if "transform" in r:
        result["body"] = Transformer.transform(r["transform"], input_data)  

      return result
    
    return None

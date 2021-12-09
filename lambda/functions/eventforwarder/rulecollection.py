class RuleCollection(object):
  def __init__(self, name, ruleset_list, result_on_match):
    self.name = name
    self.ruleset_list = ruleset_list
    self.result_on_match = result_on_match
  
  def check(self, data):
    results = []
    for ruleset in self.ruleset_list:
      results.append(ruleset.check(data))
      
    if True in results and False not in results:
      return self.result_on_match
    else:
      return None

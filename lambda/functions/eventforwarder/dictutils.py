

class Dictutils(object):

  @classmethod
  def get_path(cls, d, path):
    if not isinstance(path, list):
      p = cls.to_path(path)
    else:
      p = path
    _d = d
    for x in range(0, len(p)):
      if p[x] not in _d:
        raise PathNotFound(path, p[x])
      _d = _d[p[x]]
      
    return _d


  @classmethod
  def set_path(cls, d, path, func):
    p = cls.to_path(path)
    cls.get_path(d, p)
    return cls.traverse_modify(d, p, func)
    


  @classmethod
  def traverse(cls, obj, path=None, callback=None):
      """
      Traverse an arbitrary Python object structure (limited to JSON data
      types), calling a callback function for every element in the structure,
      and inserting the return value of the callback as the new value.
      """
      if path is None:
          path = []

      if isinstance(obj, dict):
          value = {k: cls.traverse(v, path + [k], callback)
                  for k, v in obj.items()}
      elif isinstance(obj, list):
          value = [cls.traverse(elem, path + [[]], callback)
                  for elem in obj]
      else:
          value = obj

      if callback is None:
          return value
      else:
          return callback(path, value)


  @classmethod
  def traverse_modify(cls, obj, target_path, action):
      """
      Traverses an arbitrary object structure and where the path matches,
      performs the given action on the value, replacing the node with the
      action's return value.
      """
      target_path = cls.to_path(target_path)

      def transformer(path, value):
          if path == target_path:
              return action(value)
          else:
              return value

      return cls.traverse(obj, callback=transformer)


  @staticmethod
  def to_path(path):
      """
      Helper function, converting path strings into path lists.
          >>> to_path('foo')
          ['foo']
          >>> to_path('foo.bar')
          ['foo', 'bar']
          >>> to_path('foo.bar[]')
          ['foo', 'bar', []]
      """
      if isinstance(path, list):
          return path  # already in list format

      def _iter_path(path):
          for parts in path.split('[]'):
              for part in parts.strip('.').split('.'):
                  yield part
              yield []

      return list(_iter_path(path))[:-1]


class PathNotFound(Exception):
  def __init__(self, path, element):
    self.path = path
    self.element = element

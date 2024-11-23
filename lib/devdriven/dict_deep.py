def hash_deep(obj):
  def mix(a, b):
    a = a - 1
    if a < 0:
      a = - a
    b = b - 1
    if b < 0:
      b = - b
    return a ^ b

  def hash_deep_seq(obj):
    val = hash(len(obj))
    for item in obj:
      val = mix(hash_deep(item), val)
    return val

  if f := obj.__hash__:
    return f()
  h = hash(obj.__class__.__name__)
  if isinstance(obj, (list, tuple)):
    return mix(h, hash_deep_seq(obj))
  if isinstance(obj, (dict)):
    return mix(h, hash_deep_seq(obj))
  return -1


hash_deep(123)
hash_deep(123.45)
hash_deep(True)
hash_deep(False)
hash_deep([])
hash_deep('a')
hash_deep(['a'])
hash_deep((1))
hash_deep({})
hash_deep({"a": 1})

def dict_deep():
  d = {}

  def d_get(k):
    h = hash_deep(k)
    if bucket := d.get(h):
      for item in bucket:
        if item[0] == k:
          return item[1]
    return None

  def d_set(k, v):
    h = hash_deep(k)
    if not (bucket := d.get(h)):
      d[h] = bucket = []
    for e in bucket:
      if e[0] == k:
        e[1] = v
        return None
    bucket.append([k, v])
    return None

  def g(k, *v):
    if v:
      d_set(k, v[0])
      return None
    return d_get(k)
  return g

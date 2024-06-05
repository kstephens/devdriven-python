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
    h = len(obj).__hash__()
    for e in obj:
      h = mix(hash_deep(e), h)
    return h
  if f := obj.__hash__:
    return f()
  h = obj.__class__.__name__.__hash__()
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
      for e in bucket:
        if e[0] == k:
          return e[1]
    return None

  def d_set(k, v):
    h = hash_deep(k)
    if not (bucket := d.get(h)):
      d[h] = bucket = []
    for e in bucket:
      if e[0] == k:
        e[1] = v
        return
    bucket.append([k, v])

  def g(k, *v):
    if v:
      d_set(k, v[0])
    else:
      return d_get(k)
  return g


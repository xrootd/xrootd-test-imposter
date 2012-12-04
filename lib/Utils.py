def flatten(*args):
  for x in args:
    if hasattr(x, '__iter__'):
      for y in flatten(*x):
        yield y
    else:
      yield x
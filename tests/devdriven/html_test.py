from devdriven.html import Table
# from icecream import ic

def test_table():
  title = 'TITLE'
  columns = ['a', 'b', 'c']
  rows = [
    {'a': 11, 'b': 12, 'c': 13},
    {'a': 21, 'b': '<b>22</b>', 'c': 23},
    {'a': 31, 'b': '32', 'c': '<b>33</b>'},
  ]
  opts = {
    'raw_columns': ['b'],
    'sorting': True,
    'filtering': True,
  }
  sut = Table(title=title, columns=columns, rows=rows, opts=opts)
  sut.render()
  print(sut.output.getvalue())

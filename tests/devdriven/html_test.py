from devdriven.html import Table

def test_table():
  columns = ['a', 'b', 'c', 'd']
  rows = [
    [11, "jack", 13, 123],
    ["boo", '<span style="font-size: 150%;"><b><i>RAW</i></b></span>', "soup", 987],
    ["foo", 'farm', '<b>not-raw</b>', 567],
    [None, '0', '', -1],
  ]
  rows = [dict(zip(columns, row)) for row in rows]
  options = {
    'title': 'TITLE',
    'columns': {
      'a': {'align': 'center'},
      'b': {'raw': True},
      'c': {'align': 'right'},
      'd': {'numeric': True},
    },
    'styled': True,
    'sorting': True,
    'filtering': True,
    'filtering_tooltip': True,
    'row_index': True,
    'none': '',
  }
  sut = Table(columns=columns,
              rows=rows,
              options=options)
  sut.render()
  result = sut.output.getvalue()
  with open("tmp/html_test.html", "w", encoding='UTF-8') as html:
    html.write(result)
  print(len(result))
  assert len(result) > 8192

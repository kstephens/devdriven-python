from devdriven.html import Table
# from icecream import ic

def test_table():
  title = 'TITLE'
  columns = ['a', 'b', 'c']
  rows = [
    {'a': 11,    'b': "jack", 'c': 13},
    {'a': "boo", 'b': '<span style="font-size: 150%;"><b><i>RAW</i></b></span>', 'c': "soup"},
    {'a': "foo", 'b': 'farm', 'c': '<b>not-raw</b>'},
  ]
  options = {
    'column_options': {
      'b': {'raw': True},
    },
    'styled': True,
    'sorting': True,
    'filtering': True,
    'filtering_tooltip': True,
  }
  sut = Table(title=title,
              columns=columns,
              rows=rows,
              options=options)
  sut.render()
  result = sut.output.getvalue()
  with open("tmp/html_test.html", "w", encoding='UTF-8') as html:
    html.write(result)
  print(len(result))
  assert len(result) > 8192

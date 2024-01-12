from io import StringIO
from typing import Any, Optional, Iterable
from dataclasses import dataclass, field
import html
from mako.template import Template  # type: ignore
from mako.runtime import Context  # type: ignore
# from icecream import ic

@dataclass
class Table:
  output: Any = None
  title: Optional[str] = None
  columns: list = field(default_factory=list)
  rows: Iterable[Any] = field(default_factory=list)
  opts: dict = field(default_factory=dict)
  table_head: bool = True

  def render(self):
    if not self.output:
      self.output = StringIO()
    template = Template(text=TABLE, strict_undefined=True)
    data = vars(self) | {
      'this': self,
      'h': self.h,
      'resource': self.resource,
      'opt': self.opt,
      'cell': self.cell,
      'width': len(self.columns),
      'height': len(self.rows),
      'right': 'class="cx-right"',
      'javascript': self.javascript,
    }
    context = Context(self.output, **data)
    template.render_context(context)
    # ic(result)
    return self

  def h(self, x: Any) -> str:
    return html.escape(str(x))

  def opt(self, name, default: Any = None) -> Any:
    return self.opts.get(name, default)

  def resource(self, name, default='') -> str:
    if not name:
      return str(default)
    if data := self.opts.get(name, False):
      if data.startswith('@'):
        return f'TODO:RESOURCE-FROM-FILE({data[1:]})'
      return str(data)
    return f'TODO:resource({name!r})'

  def javascript(self, content):
    return f'<script>{content}</script>'

  def is_raw_column(self, col):
    return col in self.opts.get('raw_columns', [])

  def cell(self, row, col):
    data = row.get(col, '')
    if not self.is_raw_column(col):
      return self.h(data)
    return str(data)

  def init_sort(self):
    return self.javascript("new Tablesort(document.getElementById('cx-table'));")

  def init_search(self):
    return self.javascript("var cx_filter = cx_make_filter('cx-table');")


HEAD = '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8"/>
    % if title:
    <title>${h(title)}</title>
    % endif
    % if opt('styled'):
    ${resource('cx.css')}
    % endif
    ${resource('head.html')}
    ${opt('head', '')}
  </head>
  <body>
  <!--
    ${repr(this.opts)}
  -->
  ${resource(opt('body_head'))}
'''

FOOT = '''${resource(opt('body_foot'))}
  </body>
${opt('foot', '')}
${resource('foot.html')}
</html>
'''

TABLE = HEAD + '''<table>
%if table_head:
  <thead>
    <tr>
    <th></th>
% for col in columns:
    <th>${h(col)}</th>
% endfor
    </tr>
  </thead>
%endif
  <tbody>
<% row_idx = 0 %>
% for row in rows:
  <% row_idx += 1 %>
    <tr title="${f'{row_idx} / {height}'}">
      <td ${right}>${row_idx}</td>
  % for col in columns:
      <td>${cell(row, col)}</td>
  % endfor
    </tr>
% endfor
  </tbody>
</table>
% if opt('filtering'):
  ${javascript(resource("vendor/zepto.js"))}
  ${javascript(resource("parser_combinator.js"))}
  ${javascript(resource("filter.js"))}
%endif
% if opt('sorting'):
  ${javascript(resource("vendor/tablesort.js"))}
  ${this.init_sort()}
%endif
% if opt('filtering'):
  ${this.init_search()}
%endif
''' + FOOT

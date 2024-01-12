from io import StringIO
from pathlib import Path
from typing import Any, Optional, Self, List
from dataclasses import dataclass, field
import html
from devdriven.resource import Resources
from mako.template import Template  # type: ignore
from mako.runtime import Context  # type: ignore

@dataclass
class Table:
  output: Any = None
  title: Optional[str] = None
  columns: list = field(default_factory=list)
  rows: List[Any] = field(default_factory=list)
  opts: dict = field(default_factory=dict)
  table_head: bool = True
  resources: Optional[Any] = None
  data: Optional[dict] = None

  def render(self) -> Self:
    if not self.output:
      self.output = StringIO()
    if not self.resources:
      path = Path(__file__).parent.joinpath('resources/html')
      self.resources = Resources(search_paths=[str(path)])
    template = Template(text=TABLE, strict_undefined=True)
    self.data = vars(self) | {
      'this': self,
      'h': self.h,
      'opt': self.opt,
      'width': len(self.columns),
      'height': len(self.rows),
      'right': 'class="cx-right"',
      'left': 'class="cx-left"',
    }
    context = Context(self.output, **self.data)
    template.render_context(context)
    return self

  def h(self, x: Any) -> str:
    return html.escape(str(x))

  def opt(self, name, default: Any = None) -> Any:
    return self.opts.get(name, default)

  def resource_(self, names: List[str], default=None) -> Any:
    if not names:
      return str(default)
    assert self.resources
    data = self.resources.read(names, None)
    if data is None:
      if default is None:
        raise Exception(f'resource: cannot locate {names!r}')
      return default
    return data

  def resource_opt(self, name: str, default=None) -> str:
    if data := self.opts.get(name, False):
      if data.startswith('@'):
        return self.resource(name[:1])
      return str(data)
    if default is None:
      raise Exception(f'resource: cannot locate {name!r}')
    return str(default)

  def resource(self, name: str, default=None) -> str:
    return self.resource_([name], default)

  def resource_min(self, name: str, default=None) -> str:
    path = Path(name)
    parent = path.parent
    suffix = path.suffix
    base = path.name[:-len(suffix)]
    name_min = parent.joinpath(f'{base}.min{suffix}')
    return self.resource_([name, str(name_min)], default)

  def javascript(self, content: str) -> str:
    return f'<script>{content}</script>'

  def style(self, content: str) -> str:
    return f'<style>{content}</style>'

  def is_raw_column(self, col: str) -> bool:
    return col in self.opts.get('raw_columns', [])

  def cell(self, row, col: str) -> str:
    data = row.get(col, '')
    if not self.is_raw_column(col):
      return self.h(data)
    return str(data)

  def init_sort(self) -> str:
    return self.javascript("new Tablesort(document.getElementById('cx-table'));")

  def init_search(self) -> str:
    return self.javascript("var cx_filter = cx_make_filter('cx-table');")


HEAD = '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8"/>
    % if title:
    <title>${h(title)}</title>
    % endif
    % if opt('styled'):
    ${this.style(this.resource_min('cx.css'))}
    % endif
    % if opt('stylesheet'):
    ${this.style(this.resource_min(opt('stylesheet')))}
    % endif
    ${this.resource('head.html')}
    ${this.resource_opt('head', '')}
  </head>
  <body>
  <!--
    ${repr(this.opts)}
  -->
  ${this.resource_opt('body_head', '')}
'''

FOOT = '''${this.resource_opt('body_foot', '')}
  </body>
${this.resource_opt('foot', '')}
${this.resource('foot.html')}
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
      <td>${this.cell(row, col)}</td>
  % endfor
    </tr>
% endfor
  </tbody>
</table>
% if opt('filtering'):
  ${this.javascript(this.resource_min("vendor/zepto.js"))}
  ${this.javascript(this.resource_min("parser_combinator.js"))}
  ${this.javascript(this.resource_min("filter.js"))}
%endif
% if opt('sorting'):
  ${this.javascript(this.resource("vendor/tablesort.js"))}
  ${this.init_sort()}
%endif
% if opt('filtering'):
  ${this.init_search()}
%endif
''' + FOOT

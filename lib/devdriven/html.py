from typing import Any, Optional, Self, List, Tuple
from io import StringIO
from pathlib import Path
import re
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
  options: dict = field(default_factory=dict)
  table_head: bool = True
  resources: Optional[Any] = None
  data: Optional[dict] = None

  def render(self) -> Self:
    if not self.output:
      self.output = StringIO()
    if not self.resources:
      path = Path(__file__).parent.joinpath('resources/html')
      self.resources = Resources(search_paths=[str(path)])
    self.data = vars(self) | {
      'this': self,
      'h': self.h,
      'opt': self.opt,
      'width': len(self.columns),
      'colspan': len(self.columns) + 1,
      'height': len(self.rows),
      'unicode': UNICODE,
    }
    self.render_template(self.template_text())
    return self

  def template_text(self) -> str:
    templates = [TABLE_HEAD]
    if self.opt('thead', True):
      templates += [THEAD_HEAD]
      if self.opt('filtering'):
        templates += [THEAD_FILTERING]
      templates += [THEAD_COLUMNS, THEAD_FOOT]
    templates += [TBODY, TABLE_FOOT]
    if not self.opt('table_only'):
      templates = [HTML_HEAD, *templates, HTML_FOOT]
    return self.join_templates(templates)

  def render_template(self, text) -> Self:
    template, context = self.template_context(text)
    template.render_context(context)
    return self

  def template_context(self, text) -> Tuple[Template, Context]:
    return (
      Template(text=text, strict_undefined=True),
      Context(self.output, **self.data)
    )

  def join_templates(self, templates):
    def strip_leading(text):
      return re.sub(r'^\s*\n+', '', text, count=1)
    return ''.join(map(strip_leading, templates))

  ######################################
  # Helpers:

  def h(self, x: Any) -> str:
    return html.escape(str(x))

  def opt(self, name, default: Any = None) -> Any:
    return self.options.get(name, default)

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
    if data := self.options.get(name, False):
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
    return self.resource_([str(name_min), name], default)

  def javascript(self, content: str) -> str:
    if content:
      return f'<script>\n{content}\n</script>\n'
    return ''

  def style(self, content: str) -> str:
    if content:
      return f'<style>\n{content}\n</style>\n'
    return ''

  def col_opts(self, col: str) -> dict:
    return self.options.get('column_options', EMPTY_DICT).get(col, EMPTY_DICT)

  def col_opt(self, col: str, opt: str, default=None) -> Any:
    return self.col_opts(col).get(opt, default)

  def cell(self, row, col: str, _row_idx: int) -> str:
    data = row.get(col, '')
    if not self.col_opt(col, 'raw', False):
      return self.h(data)
    return str(data)

  def init_sort(self) -> str:
    return self.javascript("new Tablesort(document.getElementById('cx-table'));")

  def init_filtering(self) -> str:
    return self.javascript("var cx_filter = cx_make_filter('cx-table');")


#########################################

EMPTY_DICT = {}

UNICODE = {
  # Left-Pointing Magnifying Glass : U+1F50D
  'search': "🔍",
}

#########################################

HTML_HEAD = '''
<!DOCTYPE html>
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
    ${this.resource('html-head-foot.html')}
    ${this.resource_opt('head', '')}
  </head>
  <body>
  <!--
    ${repr(this.options)}
  -->
  ${this.resource('body-head.html', '')}
  ${this.resource_opt('body_head', '')}
  <div class="cx-content">
  % if title:
    <div class="cx-title">${title}</div>
  % endif
'''

HTML_FOOT = '''
    </div>
    ${this.resource_opt('body_foot', '')}
    ${this.resource('body-foot.html')}
  </body>
${this.resource_opt('html_foot', '')}
${this.resource('html-foot.html')}
</html>
'''

#########################################

TABLE_HEAD = '''
<table id="cx-table" class="cx-table">
  ${this.resource_opt('table_head', '')}
'''
TABLE_FOOT = '''
  ${this.resource_opt('table_foot', '')}
</table>
% if opt('filtering'):
  ${this.javascript(this.resource_min("vendor/zepto-1.2.0/zepto.js"))}
  ${this.javascript(this.resource_min("parser_combinator.js"))}
  ${this.javascript(this.resource_min("filter.js"))}
%endif
% if opt('sorting'):
  ${this.javascript(this.resource_min("vendor/tablesort-5.3.0/src/tablesort.js"))}
  ${this.javascript(this.resource_min("vendor/tablesort-5.3.0/src/sorts/tablesort.number.js"))}
  ${this.javascript(this.resource_min("vendor/tablesort-5.3.0/src/sorts/tablesort.date.js"))}
  ${this.javascript(this.resource_min("vendor/tablesort-5.3.0/src/sorts/tablesort.dotsep.js"))}
  ${this.javascript(this.resource_min("vendor/tablesort-5.3.0/src/sorts/tablesort.filesize.js"))}
  ${this.init_sort()}
%endif
% if opt('filtering'):
  ${this.init_filtering()}
%endif
'''

#########################################

THEAD_HEAD = '''
  <thead class="cx-thead">
'''

THEAD_FOOT = '''
  </thead>
'''

#########################################

THEAD_COLUMNS = '''
<%
  row_title = "row #"
  if opt('sorting'):
    row_title += ' -- click to sort'
%>
    <tr class="cx-columms">
      <th title="${row_title}" data-sort-method="number">#</th>
<% col_idx = 0 %>
% for col in columns:
<%
  col_idx += 1
  col_title = f'name: {col}; index: {col_idx}; type: {this.col_opt("type", "UNKNOWN")}'
  col_sort = ''
  if opt('sorting'):
    if this.col_opt('numeric', False):
      col_sort = 'number'
    if col_sort:
      col_sort = f'data-sort-method="{col_sort}"'
%>
      <th
        class="cx-column"
% if opt('sorting'):
        ${col_sort}
%endif
%if opt('filtering'):
        data-column-index="${col_idx}"
        data-filter-name="${col}"
        data-filter-name-full="${col}"
%endif
      title="${col_title}"
      >${h(col)}</th>
% endfor
    </tr>
'''

THEAD_FILTERING = '''
    <tr class="cx-filter-row">
      <th class="cx-filter-th" colspan="${colspan}">
        <span class="cx-filter-input-span">
          <input
            type="text"
            id="cx-filter-input"
            class="cx-filter-input"
            onkeyup="cx_filter.filter_rows(event)"
            placeholder="${unicode['search']} Filter..." />
          %if opt('filtering_tooltip'):
          <span class="cx-tooltip">
            <span class="cx-tooltip-body">?</span>
            <span class="cx-tooltip-text"></span>
          </span>
          %endif
          <!-- Clear filter button: -->
          <button class="cx-filter-input-clear" onclick="cx_filter.clear_filter()">X</button>
          <span class="cx-filter-row-count-span">
            <span class="cx-filter-matched-row-count">${height}</span>
            &nbsp;/&nbsp;
            <span class="cx-filter-row-count">${height}</span>
          </span>
        </span>
      </th>
    </tr>
'''

#########################################

TBODY = '''
  <tbody class="cx-tbody">
<% row_idx = 0 %>
% for row in rows:
  <%
    row_idx += 1
    row_tooltip = f'{row_idx} / {height}'
  %>
    <tr title="${row_tooltip}">
      <td class="cx-right">${row_idx}</td>
  % for col in columns:
      <td title="${row_tooltip} - ${col}">${this.cell(row, col, row_idx)}</td>
  % endfor
    </tr>
% endfor
  </tbody>
'''

#########################################


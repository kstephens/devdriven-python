from typing import Any, Optional, Self, List, Tuple, Dict
from io import StringIO
from pathlib import Path
import re
from dataclasses import dataclass, field
import html
import cmath
from devdriven.resource import Resources
from mako.template import Template  # type: ignore
from mako.runtime import Context  # type: ignore
# from icecream import ic

res_html = Resources([]).add_file_dir(__file__, 'resources/html')
res_table = Resources([]).add_file_dir(__file__, 'resources/html/table')
res_vendor = Resources([]).add_file_dir(__file__, 'resources/vendor')
res_js = Resources([]).add_file_dir(__file__, 'resources/js')
res_css = Resources([]).add_file_dir(__file__, 'resources/css')

@dataclass
class Table:
  columns: list = field(default_factory=list)
  rows: List[Any] = field(default_factory=list)
  options: dict = field(default_factory=dict)
  output: Any = None
  data: dict = field(default_factory=dict)
  _col_opts: dict = field(default_factory=dict)
  enable_min: bool = field(default=True)

  def render(self) -> Self:
    self.enable_min = False
    if not self.output:
      self.output = StringIO()
    self.prepare_options()
    self.data = vars(self) | {
      'this': self,
      'h': self.h,
      'opt': self.opt,
      'col_opt': self.col_opt,
      'width': len(self.columns),
      'colspan': len(self.columns) + 1 if self.opt('row_index') else len(self.columns),
      'height': len(self.rows),
      'unicode': UNICODE,
      'allow_attributes': self.opt('styled') or self.opt('filtering') or self.opt('sorting'),
      'attr': self.attr,
      'attrs': self.attrs,
      'class_': self.class_,
      'table': res_table,
      'vendor': res_vendor,
      'js': res_js,
      'css': res_css,
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
    templates += [TABLE_INIT]
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
    def strip_it(text):
      return re.sub(r'^\s*\n+|\s*\n+$', '', text, count=1)
    return ''.join(map(strip_it, templates))

  ######################################
  # Options:

  def prepare_options(self):
    self.options = {} | self.options
    if self.opt('simple'):
      self.options['styled'] = False
      self.options['sorting'] = False
      self.options['filtering'] = False
    if self.opt('sorting') or self.opt('filtering'):
      self.options['styled'] = True
    # Merge and amend column options:
    opt_cols = self.options.get('columns', {})
    # ic(opt_cols)
    self._col_opts = {col: {} | opt_cols.get(col, {}) for col in self.columns}
    # ic(self._col_opts)
    for col, opts in self._col_opts.items():
      opts['none'] = self.opt('none', opts.get('none', None))
      opts['td_class'] = self.col_class(col)
    # ic(self._col_opts)

  def col_class(self, col):
    cls = []
    align = None
    if self.col_opt(col, 'numeric'):
      align = 'right'
    if align := (self.col_opt(col, 'align') or align):
      cls.append(f'cx-{align}')
    cls.append(self.col_opt(col, 'class', ''))
    cls = ' '.join([x for x in cls if x])
    if cls:
      return cls
    return None

  ######################################
  # Helpers:

  def h(self, x: Any) -> str:
    return html.escape(str(x))

  def opt(self, name, default: Any = None) -> Any:
    return self.options.get(name, default)

  def col_opt(self, col: str, opt: str, default=None) -> Any:
    return self._col_opts[col].get(opt, default)

  def attrs(self, d):
    return ' '.join([self.attr(name, val) for name, val in d.items()]).strip()

  def attr(self, name, val):
    if name and val is not None and self.data['allow_attributes']:
      return f'{name}="{val}"'
    return ''

  def class_(self, val):
    return self.attr('class', val)

  ######################################
  # Content:

  def cell(self, row, col: str, _row_idx: int) -> str:
    data = row.get(col, '')
    replace = None
    if data is None:
      replace = self.col_opt(col, 'none_as', self.opt('none_as'))
    elif isinstance(data, float) and cmath.isnan(data):
      replace = self.col_opt(col, 'nan_as', self.opt('nan_as'))
    elif self.col_opt(col, 'render_links', self.opt('render_links')):
      if link := html_link(data):
        replace = link
    if replace is not None:
      return replace
    if self.col_opt(col, 'raw', False):
      data = self.h(data)
    data = str(data)
    return data

  def resource_(self, res: Resources, names: List[str], default=None) -> Any:
    if not names:
      return str(default)
    data = res.read(names, None)
    if data is None:
      if default is None:
        raise Exception(f'resource: cannot locate {names!r}')
      return default
    return data

  def resource_opt(self, res: Resources, name: str, default=None) -> str:
    if data := self.options.get(name, False):
      if isinstance(data, str) and data.startswith('@'):
        return self.resource(res, name[:1])
      return str(data)
    if default is None:
      raise Exception(f'resource: cannot locate {name!r}')
    return str(default)

  def resource(self, res: Resources, name: str, default=None) -> str:
    return self.resource_(res, [name], default)

  def resource_min(self, res: Resources, name: str, default=None) -> str:
    if not self.enable_min:
      return self.resource_(res, [name], default)
    path = Path(name)
    parent = path.parent
    suffix = path.suffix
    base = path.name[:-len(suffix)]
    name_min = parent.joinpath(f'{base}.min{suffix}')
    return self.resource_(res, [str(name_min), name], default)

  def javascript(self, content: str) -> str:
    if content:
      return f'<script>\n{content}\n</script>\n'
    return ''

  def style(self, content: str) -> str:
    if content:
      return f'<style>\n{content}\n</style>\n'
    return ''

def html_link(url: str, attrs=None) -> Optional[str]:
  attrs = attrs or 'target="_new" rel="noopener noreferrer"'
  url = str(url).strip()
  if re.match(r'^(https?|ftps?)://', url):
    return f'<a href="{url}" {attrs}>{html.escape(url)}</a>'
  return None


#########################################

EMPTY_DICT: Dict[Any, Any] = {}

UNICODE = {
  # Left-Pointing Magnifying Glass : U+1F50D
  'search': "🔍",
}

#########################################

HTML_HEAD = '''
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
% if opt('title'):
<title>${h(opt('title'))}</title>
% endif
% if opt('styled'):
${this.style(this.resource_min(css, 'cx.css'))}
% endif
% if opt('stylesheet'):
${this.style(this.resource_min(css, opt('stylesheet')))}
% endif
${this.resource(table, 'html-head-footer.html')}
${this.resource_opt(table, 'html_head_footer', '')}
</head>
<body>
${this.resource(table, 'body-header.html', '')}
${this.resource_opt(table, 'body_header', '')}
<div ${class_("cx-content")}>
% if opt('title'):
<div ${class_("cx-title")}>${opt('title')}</div>
% endif
'''

HTML_FOOT = '''
</div>
<div ${class_("cx-footer")}>
${this.resource_opt(table, 'body_footer', '')}
${this.resource(table, 'body-footer.html')}
%if opt('attribution'):
<div class="cx-attribution">Generated by <a href="https://github.com/kstephens/psv">PSV</a></div>
%endif
${this.resource(table, 'html-footer.html')}
${this.resource_opt(table, 'html_footer', '')}
</div>
</body>
</html>
'''

#########################################

TABLE_HEAD = '''
<table ${attrs({"id": "cx-table", "class":"cx-table"})}>
${this.resource_opt(table, 'table_head', '')}
'''
TABLE_FOOT = '''
${this.resource_opt(table, 'table_foot', '')}
</table>
'''

TABLE_INIT = '''
% if opt('filtering'):
${this.javascript(this.resource_min(vendor, "zepto-1.2.0/zepto.js"))}
${this.javascript(this.resource_min(js, "parser_combinator.js"))}
${this.javascript(this.resource_min(js, "filter.js"))}
%endif
% if opt('sorting'):
${this.javascript(this.resource_min(vendor, "tablesort-5.3.0/src/tablesort.js"))}
${this.javascript(this.resource_min(vendor, "tablesort-5.3.0/src/sorts/tablesort.number.js"))}
${this.javascript(this.resource_min(vendor, "tablesort-5.3.0/src/sorts/tablesort.date.js"))}
${this.javascript(this.resource_min(vendor, "tablesort-5.3.0/src/sorts/tablesort.dotsep.js"))}
${this.javascript(this.resource_min(vendor, "tablesort-5.3.0/src/sorts/tablesort.filesize.js"))}
%endif

% if opt('sorting') or opt('filtering'):
<script>
  var cx_filter;
$(document).ready(function() {
  console.log( "psv : document ready!" );
% if opt('sorting'):
  new Tablesort(document.getElementById('cx-table'));
%endif
% if opt('filtering'):
  cx_filter = cx_make_filter('cx-table');
%endif
});
</script>
%endif

'''

#########################################

THEAD_HEAD = '''
% if opt('header'):
<thead ${attrs({'class': "cx-thead"})}>
'''

THEAD_FOOT = '''
</thead>
%endif
'''

#########################################

THEAD_COLUMNS = '''
<%
  col_idx = 0;
  row_title = "row #";
  if opt('sorting'):
    row_title += ' -- click to sort'
%>
<tr ${class_("cx-columms")}>
%if opt('row_index'):
<th ${attrs({'class': 'cx-right', 'title': row_title, "data-sort-method": "number"})}>#</th>
%endif
% for col in columns:
<%
  col_idx += 1
  col_attrs = {
    "class": "cx-column",
    "title": f'name: {col}; index: {col_idx}; type: {this.col_opt(col, "type", "UNKNOWN")}',
  }
  col_sort = None
  if opt('sorting'):
    if this.col_opt(col, 'numeric'):
      col_attrs['data-sort-method'] = 'number'
  if opt('filtering'):
    col_attrs.update({
      "data-column-index": col_idx,
      "data-filter-name": col,
      "data-filter-name-full": col,
    })
%>
<th ${attrs(col_attrs)}>${h(col)}</th>
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
        name="cx-filter-input"
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
<tbody ${class_("cx-tbody")}>
<% row_idx = 0 %>
% for row in rows:
  <% row_idx += 1; row_tooltip = f'{row_idx} / {height}' %>
<tr ${attr("title", row_tooltip)}>
%if opt('row_index'):
<td ${class_("cx-right")}>${row_idx}</td>
%endif
% for col in columns:
<% col_tooltip = f'{row_tooltip} - {col}' %>
<td ${attrs({"class": col_opt(col, 'td_class'), "title": col_tooltip})}>${this.cell(row, col, row_idx)}</td>
  % endfor
</tr>
% endfor
</tbody>
'''

#########################################

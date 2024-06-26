/*!
 * Row filtering.
 * Copyright 2021-2024 Kurt Stephens
 * git@kurtstephens.com
 */
var cx_make_filter =
  function(table_id_) {
    var debug = false;
    var debug_init = false || debug;
    var debug_cols = false || debug;
    var debug_row = false;
    var debug_row_data = false || debug;
    var debug_event = false;
    var debug_history = false;
    var debug_match = false || debug;
    var debug_match_expr = true || debug;
    var debug_parse = false || debug;

    var query_param = 'q';

    var table_id = table_id_;

    var dom_window, dom_table, dom_rows, dom_cols, dom_ths,
        dom_filter_input, dom_matched_row_count;

    var col_name_to_idx = new Map();
    var col_idx_to_name = new Map();
    var col_to_data_idx = new Map();
    var col_idxs = [];

    function to_col_idx(x) {
      return col_name_to_idx.get(x) || col_name_to_idx.get(col_idx_to_name.get(x));
    }

    function to_data_idx(x) {
      return col_to_data_idx.get(x) || col_to_data_idx.get(col_idx_to_name.get(x));
    }

    //////////////////////////////////////////////////
    // Grammar

    function escapeRegExp(str) {
      return str.replaceAll(/[.*+?^$|{}()\[\]]/g, '\\$&');
    }

    var name_word_rx = /^:([^\s:]+)/i;
    var name_quote_rx = /^:"([^"]+)"/i;
    var quote_rx = /^"((\\["\\]|[^"])*)"/;
    var rx_rx = /^\/((\\[/\\]|[^/])*)\//;
    var word_rx = /^([^:"\/\s]+)/;

    function make_parser() {
      var pc = parser_combininator;
      function pc_trace(p) {
        return debug_parse ? pc.trace(p) : p;
      }

      function with_type(t, p) {
        return pc.describe(
          'with_type', arguments,
          pc.when(p,
                  function (str, _inp) {
                    return {type: t,
                            str: str};
                  }));
      }

      var name_word  = pc.pred(pc.trim(pc.rx(name_word_rx)), to_col_idx);
      var name_quote = pc.pred(pc.trim(pc.rx(name_quote_rx)), to_col_idx);
      var name       = pc.or_(name_quote, name_word);
      name = pc_trace(name);

      var pat_quote  = pc.trim(pc.rx(quote_rx));

      rx_maybe       = pc_trace(pc.regexp_maybe);
      var pat_rx     = pc.pred(pc.trim(pc.rx(rx_rx)), rx_maybe);
      pat_rx = pc_trace(pat_rx);

      var pat_word   = pc.trim(pc.rx(word_rx));
      pat_word = pc_trace(pat_word);

      var pat_datum  = pc.or_(with_type('quote', pat_quote),
                              with_type('rx',    pat_rx),
                              with_type('word',  pat_word));

      // pat_datum = trace_parse(pat_datum);

      var pat_not = pc.seq(pc.trim(pc.rx(/^(NOT)\b/)), pat_datum);
      pat_not = pc.when(pat_not, function (parsed, _inp) {
        return Object.assign(parsed[1], {negate: true});
      });

      var pat = pc.or_(pat_not, pat_datum)

      var col_pat  = pc.with_keys(['name', 'pat'],
                                  pc.seq(name, pat));

      col_pat = pc_trace(col_pat);
      col_pat = pc.when(col_pat,
                        function (pat, _inp) {
                          return Object.assign({name: pat.name}, pat.pat);
                        });

      var bare_pat  =
          pc.when(pat,
                  function (pat, _inp) {
                    return Object.assign({name: null}, pat);
                  });

      var p = pc.all(pc.one_or_more(pc.or_(col_pat, bare_pat)));
      // trap exceptions in parser:
      return pc.safe(p);
    }
    var parser = make_parser();

    //////////////////////////////////////////////////
    // Help

    function escapeHtml(unsafe) {
      return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }
    function make_html(lines) {
      return lines.map(s => escapeHtml(s.trimEnd())).join(" \n");
    }
    help_examples = make_html([
      '  Examples:                                               ',
      '                                                          ',
      'foo        - Any column contains "foo"                    ',
      'foo bar    - Any column contains "foo" followed by "bar"  ',
      '/^foo/     - Any column starts with "foo"                 ',
      ':a bar     - Column "a" contains "bar"                    ',
      ':a "bar"   - Column "a" is "bar"                          ',
      '',
    ]);

    help_syntax = make_html([
      '  Syntax:                                   ',
      '                                            ',
      '<filter>      = <match> *                   ',
      '<match>       = <all> | <column>            ',
      '<all>         = <pattern>                   ',
      '<column>      = <name> <pattern>            ',
      '<pattern>     = <word> | <rx> | <quote>     ',
      '<name>        = <name-quote> | <name-word>  ',
      '<name-quote>  = ' + name_quote_rx + '       ',
      '<name-word>   = ' + name_word_rx + '        ',
      '<word>        = ' + word_rx + '             ',
      '<rx>          = ' + rx_rx + '               ',
      '<quote>       = ' + quote_rx + '            ',
      ''
    ]);

    //////////////////////////////////////////////////
    // Filter Predicate

    function parse_filter_fn_(filter_str) {
      var pc = parser_combininator;
      var result = parser(filter_str);
      if ( ! result ) return false;
      var pats_all = result[0];
      if ( pats_all.length == 0 ) return false;

      var is_bare_pat = pat => pat.col === null;
      var bare_pats   = pats_all.filter(is_bare_pat);
      var pats        = pats_all.filter(pat => ! is_bare_pat(pat))

      // Build a single RX for bare patterns:
      if ( bare_pats.length > 0 ) {
        var str    = bare_pats.map(pat => pat.str).join(' ');
        var rx_str = bare_pats.map(pat => pat.str).join('.+')
        var desc   = 'THEN(' + bare_pats.map(pat => pc.description(pat)).join(',') + ')';
        pats.push({
          name:         false,
          type:         'rx',
          str:          str,
          rx_str:       rx_str,
          description:  desc
        });
      }

      // Build a rx for each pattern type:
      pats_all.
        forEach(function (pat) {
          pat.description = pat.type.toUpperCase() + '(' + pc.to_json(pat.str) + ')';
          if ( pat.name ) {
            pat.col_idx = to_col_idx(pat.name);
            pat.data_idx = to_data_idx(pat.name);
            pat.description = 'COLUMN(' + pc.to_json(pat.name) + '=' + pat.col_idx + ',' + pat.data_idx + ',' + pat.description + ')';
          }
          if ( pat.negate ) {
            pat.description = 'NOT(' + pat.description + ')';
          }
          switch ( pat.type ) {
          case 'rx':
            pat.rx_str = pat.rx_str || pat.str;
            break;
          case 'word':
            pat.rx_str = pc.escape_regexp(pat.str);
            break;
          case 'quote':
            pat.str = pat.str.replace(/\\(["\\])/g, '$1');
            pat.rx_str = pc.escape_regexp(pat.str);
            if ( pat.name )
              pat.rx_str = '^' + pat.rx_str + '$';
            break;
          }
        }
      );

      // Build match_fn for each pat:
      pats.forEach(function (pat) {
        pat.extract_fn = make_extract_fn(pat.data_idx);
        pat.extract_fn_str = pat.extract_fn.toString();
        if ( pat.rx = pc.regexp_maybe(pat.rx_str) ) {
          pat.rx_fn = function (str) {
            result = str.match(pat.rx);
            if ( debug_match )
              console.log("filter.js : match : %s.match(%s)", JSON.stringify(str), JSON.stringify(pat.rx_str));
            return result;
          };
          pat.match_fn = function (row_data) {
            return pat.rx_fn(pat.extract_fn(row_data));
          };
          if ( pat.negate ) {
            pat.match_fn = negate_match_fn(pat.match_fn);
          }
          pc.set_description(pat.description, pat.match_fn);
          pat.match_fn_str = pat.match_fn.toString();
        } else {
          pat.rx_fn = pat.match_fn = false;
        }
        if ( ! pat.col_idx )
          pc.set_description("ROW(" + pc.description(pat.match_fn) + ")", pat.match_fn)
      });

      if ( debug_match_expr )
        console.log("psv : filter.js : pats = %s", JSON.stringify(pats, null, 2));

      var match_fns = pats.map(pat => pat.match_fn);
      var match_fn  = match_fns.indexOf(false) >= 0 ? false : and_fns(match_fns);

      if ( debug_match_expr ) {
        console.log("psv : filter.js : match_fns = %s", JSON.stringify(match_fns));
        console.log("psv : filter.js : match_fn = %s",  JSON.stringify(match_fn));
        console.log("psv : filter.js : desc = %s", pc.description(match_fn))
      }

      return match_fn;
    }

    function parse_filter_fn(filter_str) {
      var pc = parser_combininator;
      try {
        return parse_filter_fn_(filter_str);
      } catch ( err ) {
        console.log("psv : filter.js : parse_filter: error %s : filter_str %s",
                    pc.description(err.toString()),
                    pc.description(filter_str));
        return false; // function (row_data) { return false; };
      }
    }

    function make_extract_fn(data_idx) {
      return data_idx ?
        function (row_data) {
          return row_data[data_idx];
        } : extract_row_text_fn;
    }
    function extract_row_text_fn(row_data) {
      return row_data[0];
    }

    function and_fns(fns) {
      var pc = parser_combininator;
      var desc = 'AND(' + fns.map(pc.description).join(',') + ')';
      var fn  = function (row_data) {
        for ( var i = 0; i < fns.length; i ++ ) {
          if ( ! fns[i](row_data) ) {
            return false;
          }
        }
        return true;
      }
      return pc.set_description(desc, fn);
    }
    function negate_match_fn(match_fn) {
      return function (row_data) {
        return ! match_fn(row_data);
      };
    }

    //////////////////////////////////////////////////

    function each_row(row_fn) {
      if ( debug_row ) console.log("psv : filter.js : each_row : {{{ : %d", dom_rows.length);
      for (var i = 0; i < dom_rows.length; i++)
        row_fn(dom_rows[i]);
      if ( debug_row ) console.log("psv : filter.js : each_row : }}} : %d", dom_rows.length);
    }

    //////////////////////////////////////////////////

    function reset_rows() {
      if ( debug_row ) console.log("psv : filter.js : reset_rows : {{{ : %d", dom_rows.length);
      each_row(function(tr) {
        tr.style.display = '';
      });
      if ( debug_row ) console.log("psv : filter.js : reset_rows : }}} : %d", dom_rows.length);
      dom_matched_row_count.textContent = dom_rows.length;
    }

    function set_filter_input(value) {
      value = value == null ? '' : value.trim();
      dom_filter_input.value = value;
      filter_set_url_query(value);
      return value;
    }

    function clear_filter() {
      reset_rows();
      set_filter_input('');
    }

    //////////////////////////////////////////////////

    function make_row_data(tr) {
      var tds = Array.from(tr.getElementsByTagName("td")); //.toArray();
      var row_data = [''];
      col_idxs.forEach(function (idx) {
        var td = tds[idx];
        var text = (td.textContent || td.innerText).trim();
        row_data[idx + 1] = text;
        row_data[0] += text + ' ';
      });
      if ( debug_row_data ) console.log("psv : filter.js : make_row_data = " + JSON.stringify(row_data));
      return row_data;
    }

    function get_row_data(tr) {
      var data;
      if ( ! (data = tr.cx_filter_row_data) )
        tr.cx_filter_row_data = data = make_row_data(tr);
      return data;
    }

    //////////////////////////////////////////////////

    function filter_rows_by_fn(match_row_fn) {
      var n_rows_visible = 0;
      each_row(function(tr) {
        var row_data = get_row_data(tr);
        var matched = match_row_fn(row_data);
        if ( matched ) {
          n_rows_visible ++;
          tr.style.display = '';
        } else {
          tr.style.display = 'none';
        }
        return matched;
      });
      return dom_matched_row_count.textContent = n_rows_visible;
    }

    function filter_rows_now() {
      filter_rows_clear_timeout();

      var filter_str = dom_filter_input.value.trim();
      var input_ok, row_fn;
      if ( filter_str === '' ) {
        input_ok = true;
      } else {
        if ( (row_fn = parse_filter_fn(filter_str)) )
          input_ok = true;
      }

      if ( input_ok ) {
        filter_set_url_query(filter_str);
        dom_filter_input.classList.remove('cx-error');
      } else {
        dom_filter_input.classList.add('cx-error');
      }

      if ( row_fn ) {
        filter_rows_by_fn(row_fn);
      } else {
        reset_rows();
      }

      return input_ok;
    }

    //////////////////////////////////////////////////

    /*
      See:
      * https://stackoverflow.com/questions/10970078/modifying-a-query-string-without-reloading-the-page
      * https://stackoverflow.com/questions/5999118/how-can-i-add-or-update-a-query-string-parameter
    */
    function filter_set_url_query(value) {
      var searchParams = new URLSearchParams(window.location.search)
      if ( value !== "" ) {
        searchParams.set(query_param, value);
      } else {
        searchParams.delete(query_param);
      }
      if ( history.pushState ) {
        var url_query_string = searchParams.toString();
        if ( url_query_string !== "" ) {
          url_query_string = "?" + url_query_string;
        }
        var newurl = window.location.protocol + "//" + window.location.host + window.location.pathname + url_query_string;
        window.history.pushState({path:newurl}, '', newurl);
      }
    }
    function filter_get_url_query() {
      var searchParams = new URLSearchParams(window.location.search)
      var value = searchParams.get(query_param);
      console.log("psv : filter.js : filter_get_url_query : %s", JSON.stringify(value));
      return value;
    }
    function filter_load_url_query() {
      var value = filter_get_url_query();
      value = set_filter_input(value);
      if ( value !== "" ) {
        filter_rows_now();
      }
    }

    //////////////////////////////////////////////////

    var filter_history = [];
    var filter_history_index = -1;
    function filter_history_save(event) {
      var value = event.target.value.trim();
      if ( ! filter_history.includes(value) ) {
        filter_history_index = filter_history.length;
        filter_history.push(value);
      }
      filter_set_url_query(value);
      if ( debug_history ) console.log("psv : filter.js : filter_history_save : event : %s : filter_history %s @ %d", event, filter_history, filter_history_index);
      return filter_history_index;
    }
    function filter_history_navigate(event, dir) {
      var i = filter_history_index + dir;
      if ( 0 <= i && i < filter_history.length ) {
        filter_history_index = i;
        var value = filter_history[filter_history_index];
        event.target.value = value;
        filter_set_url_query(value);
        if ( debug_history ) console.log("psv : filter.js : filter_history_navigate : event : %s : filter_history %s @ %d", event, filter_history, filter_history_index);
        return true;
      }
      return false;
    }

    //////////////////////////////////////////////////
    // Hook for tablesort afterSort event:

    function filter_aria_sort_changed(event) {
      // console.log("psv : filter.js : filter_aria_sort_changed : event : %s", event);
      for ( var i = 0; i < dom_ths.length; i++) {
        var th = dom_ths[i];
        var sort_order = th.getAttribute("aria-sort");
        var sort_indicator = th.getElementsByClassName("cx-column-sort-indicator")[0];
        // console.log("psv : filter.js : filter_aria_sort_changed : th %d : sort_order %s", i, sort_order);
        if ( sort_order === "descending" ) {
          sort_indicator.innerText = '\u25B2';  // up arrow
          sort_indicator.style.visibility = "visible";
        } else if ( sort_order === "ascending" ) {
          sort_indicator.innerText = '\u25BC';  // down arrow
          sort_indicator.style.visibility = "visible";
        } else {
          sort_indicator.innerText = '_';  // blank
          sort_indicator.style.visibility = "hidden";
        }
      }
    }

    //////////////////////////////////////////////////

    function filter_rows_event(event) {
      // Do nothing if the event was already processed
      if ( ! event || event.defaultPrevented )
        return;
      if ( debug_event ) console.log("psv : filter.js : event : %s : %s", event, event.which);
      switch ( event.which ) {
      case 37: // - left arrow
      case 39: // - right arrow
        break;
      case 13: // - enter/return
        filter_history_save(event);
        break;
      case 38: // - up arrow
        if ( filter_history_navigate(event, -1) )
          filter_rows_now();
        break;
      case 40: // - down arrow
        if ( filter_history_navigate(event, 1) )
          filter_rows_now();
        break;
      default:
        filter_rows_after_timeout();
        return
      }
      event.preventDefault();
    }

    var timeout = null;
    function filter_rows(event) {
      if ( debug_event ) console.log("psv : filter.js : filter_rows : event : %s : %s : %s", event, event.which, timeout);
      filter_rows_event(event);
    }
    function filter_rows_after_timeout() {
      if ( ! timeout ) {
        timeout = setTimeout(function() {
          filter_rows_now();
        }, 500);
      }
    }
    function filter_rows_clear_timeout() {
      if ( timeout ) {
        if ( debug_event ) console.log("psv : filter.js : filter_rows_clear_timeout");
        var tmp = timeout;
        timeout = null;
        clearTimeout(tmp);
      }
    }

    // https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/style
    function dump_style(element) {
      var out = "";
      var elementStyle = element.style;
      var computedStyle = window.getComputedStyle(element, null);

      for (prop in elementStyle) {
        if (elementStyle.hasOwnProperty(prop) || true) {
          out += "  " + prop + " = '" + elementStyle[prop] + "' > '" + computedStyle[prop] + "'\n";
        }
      }
      console.log(out)
      return out;
    }

    function pin_width(element) {
      var comp_style = dom_window.getComputedStyle(element, null);
      var style = element.style;
      style.width = comp_style.width;
    }
    // Construct a map from cx column names to td offsets.
    function make_col_maps(table, tr, cols) {
      col_name_to_idx.clear();
      col_idx_to_name.clear();
      col_to_data_idx.clear();
      col_idxs.length = 0;
      var th_idx = -1;
      $(tr).find('th').each(function (th) {
        var th = this;
        pin_width(th);
        th_idx += 1;
        var name = th.getAttribute("data-filter-name");
        if ( name ) {
          col_idxs.push(th_idx);
          var idx  = parseInt(th.getAttribute("data-column-index"));
          col_to_data_idx.set(name, th_idx + 1);
          if ( idx ) {
            col_to_data_idx.set(idx, th_idx + 1);
            col_to_data_idx.set(idx + "", th_idx + 1);
            col_name_to_idx.set(name, idx);
            col_idx_to_name.set(idx, name);
            col_idx_to_name.set(idx + "", name);
          }

          if ( debug_cols ) console.log("psv : filter.js : %s", JSON.stringify({th_idx: th_idx, name: name, idx: idx}));

          var name = th.getAttribute('data-filter-name-full');
          col_name_to_idx.set(name, idx);
          // dump_style(th);
        }
      });
      // https://stackoverflow.com/a/56795800/1141958
      function map_to_array(map) {
        return Array.from(map, ([name, value]) => [name, value])
      }
      if ( debug_cols ) {
        console.log("psv : filter.js : cols = %s", JSON.stringify(cols));
        console.log("psv : filter.js : col_name_to_idx = %s", JSON.stringify(map_to_array(col_name_to_idx)));
        console.log("psv : filter.js : col_idx_to_name = %s", JSON.stringify(map_to_array(col_idx_to_name)));
        console.log("psv : filter.js : col_to_data_idx = %s", JSON.stringify(map_to_array(col_to_data_idx)));
      }
    }

    function initalize(table_id_) {
      table_id = table_id_;
      dom_window = window;
      var table_sel = $("#" + table_id);
      dom_table = table_sel.toArray()[0]
      dom_ths = table_sel.find(".cx-thead .cx-columms th").toArray();
      var cols = dom_cols   = table_sel.find(".cx-thead .cx-column").toArray();
      var tr = cols && cols[0].parentElement;
      var rows = dom_rows   = table_sel.find(".cx-tbody tr").toArray();
      dom_filter_input      = table_sel.find(".cx-thead .cx-filter-input").toArray()[0]
      dom_matched_row_count = table_sel.find(".cx-filter-matched-row-count").toArray()[0];
      if ( tr )
        make_col_maps(table_sel, tr, cols);

      filter_load_url_query();

      dom_table.addEventListener("afterSort", filter_aria_sort_changed);
      filter_aria_sort_changed(null);

      pin_width(dom_table);

      var tooltips = table_sel.find(".cx-filter-row .cx-tooltip .cx-tooltip-text");
      tooltips.forEach(function (item, index, array) {
        item.innerHTML =
          '<pre>' +
          help_examples + "\n" +
          help_syntax +
          '</pre>';
      });

      if ( debug_init ) {
        console.log("psv : filter.js : DEBUG: table : %s", dom_table);
        console.log("psv : filter.js : DEBUG: tr : %d", tr);
        console.log("psv : filter.js : DEBUG: cols : %d", cols.length);
        console.log("psv : filter.js : DEBUG: rows : %d", rows.length);
      }
      if ( dom_cols.length == 0 )
        console.log("psv : filter.js : ERROR: no columns were found!")
      if ( dom_rows.length == 0 )
        console.log("psv : filter.js : WARNING: no rows were found.")

      return {
        table_id: table_id,
        dom_table: dom_table,
        dom_cols: dom_cols,
        dom_ths: dom_ths,
        dom_rows: dom_rows,
        col_name_to_idx: col_name_to_idx,
        col_idx_to_name: col_idx_to_name,
        filter_rows: filter_rows,
        filter_rows_now: filter_rows_now,
        filter_rows_event: filter_rows_event,
        clear_filter: clear_filter,
        help_examples: help_examples,
        help_syntax:   help_syntax
      };
    }

    return initalize(table_id_);
  };

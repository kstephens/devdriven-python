/*!
 * Row filtering.
 */
var cx_make_filter =
    function(table_id_) {
      var debug = true;

      var table_id = table_id_;

      var dom_window, dom_table, dom_rows, dom_cols,
          dom_filter_input, dom_matched_row_count;

      var col_name_to_idx, col_idx_to_name;
      function to_col_idx(x) {
        return col_name_to_idx.get(x) || col_name_to_idx.get(col_idx_to_name.get(x));
      }

      //////////////////////////////////////////////////
      // Grammar

      function escapeRegExp(str) {
        return str.replaceAll(/[.*+?^$|{}()\[\]]/g, '\\$&');
      }

      function make_parser() {
        var pc = parser_combininator;

        function with_type(t, p) {
          return pc.describe(
            'with_type', arguments,
            pc.when(p,
                    function (str, inp) {
                      return {type: t,
                              str: str};
                    }));
        }

        var name_rx    = pc.trim(pc.rx(/^:([a-z0-9_]+)/i));
        var name       = pc.pred(name_rx, to_col_idx);
        var pat_quote  = pc.trim(pc.rx(/^"((\\["\\]|[^"])*)"/));
        var pat_rx_    = pc.trim(pc.rx(/^\/((\\\/|[^/])*)\//));
        var pat_rx     = pc.pred(pat_rx_, pc.regexp_maybe);
        var pat_word   = pc.trim(pc.rx(/^([^:"\/\s]+)/));
        var pat        = pc.or_(with_type('quote', pat_quote),
                                with_type('rx',    pat_rx),
                                with_type('word',  pat_word));

        var col_pat  = pc.with_keys(['name', 'pat'],
                                    pc.seq(name, pat));
        col_pat = pc.when(col_pat,
                          function (pat, inp) {
                            return Object.assign({name: pat.name}, pat.pat);
                          });

        var bare_pat  =
            pc.when(pat,
                    function (pat, inp) {
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
        '  Examples: ',
        '           ',
        'foo        - Any column contains "foo"                       ',
        'foo bar    - Any column contains "foo" followed by "bar"     ',
        '/^foo/     - Any column starts with "foo"  ',
        ':a bar     - Column "a" contains "bar"     ',
        '',
      ]);

      help_syntax = make_html([
        '  Syntax:                              ',
        '                                       ',
        '<filter>   = <match> *                 ',
        '<match>    = <all> | <column>          ',
        '<all>      = <pattern>                 ',
        '<column>   = <name> <pattern>          ',
        '<pattern>  = <word> | <rx> | <quote>   ',
        '<name>     = /^:[a-z0-9_]+/i           ',
        '<word>     = /^([^:"/\s]+)             ',
        '<rx>       = /^\/.*\/$                 ',
        '<quote>    = /^"([^\\"]+|\\\\|\\")*"/  ',
        ''
      ]);

      //////////////////////////////////////////////////
      // Filter Predicate

      function parse_filter_fn_(filter_str) {
        var debug = true;
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
          pats.push({name:    false,
                     type:    'rx',
                     str:     str,
                     rx_str:  rx_str,
                     description:   desc});
        }

        // Build a rx for each pattern type:
        pats_all.
          forEach(function (pat) {
            pat.description = pat.type.toUpperCase() + '(' + pc.to_json(pat.str) + ')';
            if ( pat.name ) {
              pat.description = 'COLUMN(' + pat.name.toUpperCase() + ',' + pat.description + ')';
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
          });

        // Build match_fn for each pat:
        pats.forEach(function (pat) {
          pat.col_idx = to_col_idx(pat.name);
          pat.extract_fn = make_extract_fn(pat.col_idx);
          pat.extract_fn_str = pat.extract_fn.toString();
          if ( pat.rx = pc.regexp_maybe(pat.rx_str) ) {
            pat.rx_fn = (str => str.match(pat.rx));
            pat.match_fn = function (row_data) {
              return pat.rx_fn(pat.extract_fn(row_data));
            };
            pc.set_description(pat.description, pat.match_fn);
            pat.match_fn_str = pat.match_fn.toString();
          } else {
            pat.rx_fn = pat.match_fn = false;
          }
          if ( ! pat.col_idx )
            pc.set_description("ROW(" + pc.description(pat.match_fn) + ")", pat.match_fn)
        });

        if ( debug )
          console.log("pats = %s", JSON.stringify(pats, null, 2));

        var match_fns = pats.map(pat => pat.match_fn);
        var match_fn  = match_fns.indexOf(false) >= 0 ? false : and_fns(match_fns);

        if ( debug ) {
          console.log("match_fns = %s", JSON.stringify(match_fns));
          console.log("match_fn = %s",  JSON.stringify(match_fn));
          console.log("desc = %s", pc.description(match_fn))
        }

        return match_fn;
      }

      function parse_filter_fn(filter_str) {
        var pc = parser_combininator;
        try {
          return parse_filter_fn_(filter_str);
        } catch ( err ) {
          console.log("parse_filter: error %s : filter_str %s",
                      pc.description(err.toString()),
                      pc.description(filter_str));
          return false; // function (row_data) { return false; };
        }
      }

      function make_extract_fn(col_idx) {
        return col_idx ?
          function (row_data) {
            return row_data[col_idx];
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

      //////////////////////////////////////////////////

      function each_row(row_fn) {
        if ( debug ) console.log("each_row : {{{ : %d", dom_rows.length);
        for (var i = 0; i < dom_rows.length; i++)
          row_fn(dom_rows[i]);
        if ( debug ) console.log("each_row : }}} : %d", dom_rows.length);
      }

      //////////////////////////////////////////////////

      function reset_rows() {
        if ( debug ) console.log("reset_rows : {{{ : %d", dom_rows.length);
        each_row(function(tr) {
          tr.style.display = '';
        });
        if ( debug ) console.log("reset_rows : }}} : %d", dom_rows.length);
        dom_matched_row_count.textContent = dom_rows.length;
      }

      function clear_filter() {
        reset_rows();
        dom_filter_input.value = '';
      }

      //////////////////////////////////////////////////

      function make_row_data(tr) {
        var tds = Array.from(tr.getElementsByTagName("td")); //.toArray();
        var row_data = tds.map(function (td) {
          return (td.textContent || td.innerText).trim();
        });
        row_data[0] = row_data.slice(1).join(' ');
        // if ( debug ) console.log("make_row_data = " + JSON.stringify(row_data));
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
        var filter_str = dom_filter_input.value.trim();
        var input_ok, row_fn;
        if ( filter_str === '' ) {
          input_ok = true;
        } else {
          if ( (row_fn = parse_filter_fn(filter_str)) )
            input_ok = true;
        }

        if ( input_ok ) {
          dom_filter_input.classList.remove('cx-error');
        } else {
          dom_filter_input.classList.add('cx-error');
        }

        if ( row_fn ) {
          filter_rows_by_fn(row_fn);
        } else {
          reset_rows();
        }
      }

      function filter_rows_event(event) {
        // Do nothing if the event was already processed
        if ( ! event || event.defaultPrevented )
          return;
        switch ( event.which ) {
        case 37: // - left arrow
        case 39: // - right arrow
          break;
        case 38: // - up arrow
        case 40: // - down arrow
          // TODO: history
          break;
        default:
          if ( debug ) console.log("event : %s : %s", event, event.which);
          filter_rows_now();
          return;
        }
        event.preventDefault();
      }

      var timeout = null;
      function filter_rows(event) {
        if ( ! timeout ) {
          timeout = setTimeout(function() {
            filter_rows_event(event);
            if ( timeout ) {
              var tmp = timeout;
              timeout = null;
              clearTimeout(tmp);
            }
          }, 500);
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
        style.width  = comp_style.width;
      }
      // Construct a map from cx column names to td offsets.
      function make_col_maps(table, cols) {
        col_name_to_idx = new Map();
        col_idx_to_name = new Map();
        cols.
          filter(function (th) {
            return th.getAttribute("data-filter-name");
          }).
          map(function(th) {
            var idx  = parseInt(th.getAttribute("data-column-index"));

            var name = th.getAttribute('data-filter-name');
            col_name_to_idx.set(name, idx);
            col_idx_to_name.set(idx, name);
            col_idx_to_name.set(idx + "", name);

            if ( debug ) console.log("%s", JSON.stringify({name: name, idx: idx}));

            var name = th.getAttribute('data-filter-name-full');
            col_name_to_idx.set(name, idx);
            // dump_style(th);
            pin_width(th);
          });
        col_idx_to_name.set(0, false);
        col_idx_to_name.set("0", false);
        col_name_to_idx.set(false, 0);
        if ( debug ) {
          console.log("cols = %s", JSON.stringify(cols));
          console.log("col_name_to_idx = %s", JSON.stringify(col_name_to_idx));
          console.log("col_idx_to_name = %s", JSON.stringify(col_idx_to_name));
        }
      }

      function initalize(table_id_) {
        table_id = table_id_;
        dom_window = window;
        var table = dom_table = $("#" + table_id);
        var cols = dom_cols   = table.find(".cx-thead .cx-columns .cx-column").toArray();
        var rows = dom_rows   = table.find(".cx-tbody tr").toArray();
        dom_filter_input      = table.find(".cx-thead .cx-filter-input").toArray()[0]
        dom_matched_row_count = table.find(".cx-filter-matched-row-count").toArray()[0];
        make_col_maps(table, cols);

        pin_width(dom_table.toArray()[0]);

        var tooltips = table.find(".cx-filter-row .cx-tooltip .cx-tooltip-text");
        tooltips.forEach(function (item, index, array) {
          item.innerHTML =
            '<pre>' +
            help_examples + "\n" +
            help_syntax +
            '</pre>';
        });

        if ( debug ) {
          console.log("DEBUG: table : %s", dom_table);
          console.log("DEBUG: cols : %d", cols.length);
          console.log("DEBUG: rows : %d", rows.length);
        }
        if ( dom_cols.length == 0 )
          console.log("ERROR: no columns were found!")
        if ( dom_rows.length == 0 )
          console.log("WARNING: no rows were found.")

        return {
          table_id: table_id,
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

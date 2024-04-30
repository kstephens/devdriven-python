/*!
 * Parser Combinators.
 * Copyright 2021-2024 Kurt Stephens
 * git@kurtstephens.com
 */

var parser_combininator
  = (
    function () {
      var state = {};
      var debug = false;
      // var debug = true;

      //////////////////////////////////////
      // Helpers:

      function zip(arrays) {
        return arrays[0].map(
          function(_,i) {
            return arrays.map(
              function(array) {
                return array[i];
              });
          });
      }

      function escape_regexp(str) {
        return str.replace(/[.*+?^$|{}()\[\]]/g, '\\$&');
      }

      function regexp_maybe(str, opts) {
        try {
          return new RegExp(str, opts);
        } catch ( err ) {
          if ( debug )
            console.log("PC: regexp_maybe: %s", err);
          return undefined;
        }
      }

      function to_json(x) {
        return JSON.stringify(x);
      }

      function constantly(val) {
        return function () { return val; }
      }

      //////////////////////////////////////
      // Documentation:

      var RegExp_proto = Object.getPrototypeOf(/regexp/);

      function description(x) {
        switch ( typeof x ) {
        case 'undefined':
          return 'undefined';
        case 'number':
          return x + '';
        case 'boolean':
          return x + '';
        case 'string':
          return JSON.stringify(x);
        case 'function':
          return x.description || 'function(){...}';
        case 'object':
          if ( x === null ) {
            return null;
          } else if ( x instanceof RegExp ) {
            return x.toString();
          }
          return JSON.stringify(x);
        default:
          throw typeof(x);
        };
      }

      var debug_indent = '';
      function wrap_debug(p) {
        var desc = description(p);
        var p1 = function (inp) {
          console.log("  PC:%s %s(%s) => ...",
                      debug_indent,
                      desc,
                      description(inp));
          var debug_indent_ = debug_indent;
          try {
            debug_indent += ' '
            var result = p(inp);
          } finally {
            debug_indent = debug_indent_;
          }
          console.log("  PC:%s %s(%s) => %s",
                      debug_indent,
                      desc,
                      description(inp),
                      description(result));
          return result;
        };
        p1.description = desc;
        return p1;
      }
      function copy_description(src, dst) {
        return set_description(description(src), dst);
      }
      function set_description(s, p) {
        p.description = s;
        p = debug ? wrap_debug(p) : p;
        return p;
      }
      function describe(prefix, args, p) {
        var args_str = typeof(args) == 'string' ? args : '(' + Array.from(args).map(description).join(', ') + ')';
        return set_description(prefix + args_str, p);
      }

      //////////////////////////////////////

      function falsely_or(m) {
        return m ? false : m;
      }
      function matched(m) {
        return m === false ? false : m;
      }
      function match_item(m) {
        return matched(m) ? m[0] : null;
      }
      function match_input(m) {
        return matched(m) ? m[1] : null;
      }
      function match_empty(m) {
        return matched(m) && m[1].length == 0;
      }

      //////////////////////////////////////
      // Logical:

      function if_(q, t, f) {
        return describe(
          'if', arguments,
          function (inp) {
            return q(inp) ? t(inp) : f(inp);
          })
      }

      function not_(p, false_value) {
        return describe(
          'not_', arguments,
          function (inp) {
            var m = matched(m = p(inp));
            if ( matched(m) ) {
              return false;
            } else {
              return false_value !== null ? false_value : [ null, inp ];
            }
          });
      }

      function or_() {
        var ps = Array.from(arguments);
        return describe(
          'or_', arguments,
          function (inp) {
            var m;
            for ( var i = 0; i < ps.length; ++ i )
              if ( matched(m = ps[i](inp)) )
                return m;
            return false;
          });
      }

      function and_() {
        var ps = Array.from(arguments);
        return describe(
          'and_', arguments,
          function (inp) {
            var m;
            for ( var i = 0; i < ps.length; ++ i )
              if ( ! matched(m = ps[i](inp)) )
                return false;
            return m;
          });
      }


      //////////////////////////////////////
      // Sequences:

      function all(p) {
        return describe(
          'all', arguments,
          function (inp) {
            var m = p(inp);
            return matched(m) && match_empty(m) ? m : false;
          });
      }

      function one(p) {
        return describe(
          'one', arguments,
          function (inp) {
            var m = p(inp);
            return matched(m) ? [ [ m[0] ], m[1] ] : false;
          });
      }

      function zero_or_more(p) {
        return describe(
          'zero_or_more', arguments,
          function (inp) {
            var items = [ ];
            var m;
            while ( matched(m = p(inp)) ) {
              items.push(m[0]);
              inp = m[1];
            }
            return [ items, inp ];
          });
      }

      function at_least(n, p) {
        var zom = zero_or_more(p);
        return describe(
          'at_least', arguments,
          function (inp) {
            return matched(m = zom(inp)) && m[0].length >= n ? m : false;
          });
      }

      function one_or_more(p) {
        return describe(
          'one_or_more', arguments,
          at_least(1, p));
      }

      function seq() {
        var ps = Array.from(arguments);
        return describe(
          'seq', arguments,
          function (inp) {
            var items = [ ];
            for ( var i = 0; i < ps.length; ++ i ) {
              var p = ps[i];
              if ( matched(m = p(inp)) ) {
                items.push(m[0]);
                inp = m[1];
              } else {
                return false;
              }
            }
            return items.length == ps.length ? [ items, inp ] : false;
          });
      }

      //////////////////////////////////////
      // Leaf fns:

      function eq(seq) {
        return describe(
          'eq', arguments,
          function (inp) {
            return inp === seq ? [ seq, seq.slice(0, 0) ] : false;
          });
      }
      function eos() {
        return describe(
          'eos', arguments,
          function (inp) {
            return inp.length == 0;
          });
      }
      function rx(re, opts) {
        if ( typeof re === 'string' )
          re = new Regexp(re, opts);
        return describe(
          'rx', [re],
          function (inp) {
            var m = inp.match(re);
            return m ? [ m[1] || m[0], inp.substring(m.index + m[0].length) ] : false;
          });
      }
      function trim(p) {
        return describe(
          'trim', arguments,
          function (inp) {
            var m = p(inp.trim());
            return matched(m) ? [ m[0], m[1].trim() ] : false;
          });
      }

      function safe(p) {
        return describe(
          'safe', arguments,
          function (inp) {
            try {
              return p(inp);
            }
            catch ( err ) {
              console.log("safe: error %s: inp %s : parser %s",
                          description(err.toString()),
                          description(inp),
                          description(p));
              return false;
            }
          });
      }

      function trace(p) {
        return describe(
          'trace', arguments,
          function (inp) {
            console.log("trace: inp %s | result ... | parser %s : ...",
              description(inp),
              description(p));
            var result = p(inp);
            console.log("trace: inp %s | result %s | parser %s",
              description(inp),
              description(result),
              description(p));
            return result;
          });
      }

      //////////////////////////////////////
      // Conditional binding:

      function with_keys(ns, p) {
        return describe(
          'with_keys', arguments,
          function (inp) {
            var m;
            if ( matched(m = p(inp)) ) {
              m = [
                Object.fromEntries(zip([ns, m[0]])),
                m[1]
              ];
            }
            return m;
          }
        );
      }

      function pred(p, f) {
        return describe(
          'pred', arguments,
          function (inp) {
            var m;
            return matched(m = p(inp)) && f(m[0], m[1]) ? m : false;
          }
        );
      }

      function when(p, f) {
        return describe(
          'when', arguments,
          function (inp) {
            var m;
            if ( matched(m = p(inp)) ) {
              m = [
                f(m[0], m[1]),
                m[1]
              ];
            }
            return m;
          }
        );
      }

      /////////////////////////////
      // Top-level:

      function parse(p, inp, state_) {
        state = state_ || { };
        return p(inp);
      }

      return {
        to_json: to_json,
        parse: parse,
        matched: matched,
        match_empty: match_empty,
        match_input: match_input,
        match_parsed: match_item,
        safe: safe,
        trace: trace,
        alt: or_,
        if_, if_,
        or_: or_,
        and_: and_,
        not_: not_,
        all: all,
        one: one,
        zero_or_more: zero_or_more,
        at_least: at_least,
        one_or_more: one_or_more,
        seq: seq,
        eq: eq,
        eos: eos,
        rx: rx,
        trim: trim,
        with_keys: with_keys,
        pred: pred,
        when: when,
        falsely_or: falsely_or,
        escape_regexp: escape_regexp,
        description: description,
        set_description: set_description,
        copy_description: copy_description,
        describe: describe,
        constantly: constantly,
        regexp_maybe: regexp_maybe
      };
  }
)();


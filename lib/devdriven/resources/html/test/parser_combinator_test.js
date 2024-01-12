
function parser_combinator_test() {
  var pc = parser_combinator;
  var p;
  function t(inp, expected) {
    console.log("\n  ------------------------------");
    console.log("  parser:    %s", description(p));
    console.log("  input:     %j", inp);
    console.log("  expected:  %j", expected);
    var actual = p(inp);
    console.log("  actual:    %j", actual);
    console.log("  ------------------------------");
    if ( JSON.stringify(expected) !== JSON.stringify(actual) ) {
      throw 'test failed!';
    }
    return actual;
  }

  p = eq('abc');
  t('abc',
    ['abc', '']);
  t(' abc',
    false);

  p = rx(/^[a-z]+/);
  t('abc REST',
   ["abc"," REST"]);
  t(' abc REST',
   false);
  t('1 REST',
   false);

  p = trim(rx(/^[a-z]+/));
  t('abc REST',
   ["abc","REST"]);
  t(' abc REST',
   ["abc","REST"]);
  t('1 REST',
   false);

  p = alt(rx(/^[a-z]+/), rx(/^\d+/));
  t('abc REST',
   ["abc"," REST"]);
  t('1 REST',
   ["1"," REST"]);
  t(' 1 REST',
   false);

  p = alt(with_keys(['key'],
                    rx(/^[a-z]+/)),
          with_keys(['val'],
                    rx(/^\d+/)));
  t('abc REST',
   [{"key":"a"}," REST"]);
  t('1 REST',
    [{"val":"1"}," REST"]);
  t(' 1 REST',
   false);

  p = seq(rx(/^[a-z]+/), rx(/^\d+/));
  t('abc REST',
   false);
  t('abc 123 REST',
   false);
  t('abc123 REST',
   [["abc","123"]," REST"]);

  p = seq(trim(rx(/^[a-z]+/)),
          trim(rx(/^\d+/)));
  t('abc 123  REST',
   [["abc","123"],"REST"]);
  t('  abc   123   REST',
   [["abc","123"],"REST"]);

  p = seq(trim(rx(/^[a-z]+/)),
          trim(rx(/^\d+/)),
          eos());
  t('abc 123',
    [["abc","123",""],""]);
  t('  AbC   1 REST',
   false);

  p = all(
    seq(trim(rx(/^[a-z]+/)),
        trim(rx(/^\d+/))));
  t('abc 123',
    [["abc","123"],""]);
  t('  AbC   1 REST',
   false);

  p = one(
    seq(trim(rx(/^[a-z]+/)),
        trim(rx(/^\d+/))));
  t('abc 123',
    [[["abc","123"]],""]);
  t('  abc   123   REST',
    [[["abc","123"]],"REST"]);
  t(' OTHER',
   false);

  p = zero_or_more(trim(rx(/^\d+/)));
  t('  REST',
    [[],"  REST"]);
  t('123  REST',
   [["123"],"REST"]);
  t('123 45 REST',
   [["123","45"],"REST"]);

  p =
    zero_or_more(seq(trim(rx(/^[a-z]+:/)),
                     trim(rx(/^\d+/))));
  t('  REST',
    [[], '  REST']);
  t('a: 123  REST',
    [[["a:","123"]],
     "REST"]);
  t('a: 123 b: 45 REST',
    [[["a:","123"],
      ["b:","45"]],
     "REST"]);

  p =
    one_or_more(
      with_keys(['key', 'val'],
                seq(trim(rx(/^[a-z]+/)),
                    trim(rx(/^\d+/)))));
  t('  REST',
    false);
  t('abc 123  REST',
    [[{"key":"abc","val":"123"}],
     "REST"]);
  t(' abc 123 xyz 45REST',
    [[{"key":"abc","val":"123"},
      {"key":"xyz","val":"45"}],
     "REST"]);

  //////////////////////////////

  function with_type(t, p) {
    return pc.describe(
      'with_type',
      [t, p],
      when(p,
           function (pat, inp) {
             return {type: t,
                     pat: pat};
           }));
  }

  var col        = trim(rx(/^([a-z0-9_]+):/i))
  var pat_quote  = trim(rx(/^"((\\"|[^"])*)"/))
  var pat_rx     = trim(rx(/^\/((\\\/|[^/])*)\//))
  var pat_word   = rx(/^\s*(\S+)/)
  var pat        = alt(with_type('quote', pat_quote),
                       with_type('rx',    pat_rx),
                       with_type('word',  pat_word));
  var col_pat    = with_keys(['col', 'pat'],
                             seq(col, pat));
  var bare_pat  =
      when(trim(pat_word),
           function (pat, inp) {
             return {col: "*",
                     pat: pat};
           });
  p = all(one_or_more(alt(col_pat, bare_pat)));

  t(' ',
    false);

  t(' word1  word2 123  ',
    [[{"col":"*", "pat":{"type":"word","val":"word1"}},
      {"col":"*", "pat":{"type":"word","val":"word2"}},
      {"col":"*", "pat":{"type":"word","val":"123"}}],
     ""]
   );

  t('word:123',
    [[{"col":"word",
       "pat":{"type":
            "word",
            "val":"123"}}],
     ""]);
  t('  quote:  "quoted \\" string"  ',
    [[{"col":"quote",
       "pat":{"type":"quote",
            "val":"quoted \\\" string"}}],
     ""]);
  t('rx:/a? \\/+regex*/',
    [[{"col":"rx",
       "pat":{"type":"rx",
            "val":"a? \\/+regex*"}}],""]);

  r =
    t(' this:"q. \\"ed" word1  that:word2 123.5 other: /regex\\? */ ',
      [[{"col":"this",
         "pat":{"type":"quote",
                "val":"q. \\\"ed"}},
        {"col":"*",
         "pat":{"type":"word",
                "val":"word1"}},
        {"col":"that",
         "pat":{"type":"word",
                "val":"word2"}},
        {"col":"*",
         "pat":{"type":"word",
                "val":"123.5"}},
        {"col":"other",
         "pat":{"type":"rx",
                "val":"regex\\? *"}}],
       ""]
     );
  var col_pats = r[0];
  var is_bare_pat = x => x.col === '*';

  console.log("%s", JSON.stringify(col_pats, null, 2));
  col_pats.
    filter(x => x.pat.type == 'rx').
    forEach(x => x.pat.rx_str = x.pat.val);
  col_pats.
    filter(x => x.pat.type == 'word').
    forEach(x => x.pat.rx_str = escape_regexp(x.pat.val));
  col_pats.
    filter(x => x.pat.type == 'quote').
    forEach(function(x) {
      x.pat.val = x.pat.val.replace(/\\"/g, '"');
      x.pat.rx_str = '^' + escape_regexp(x.pat.val) + '$';
    });

  bare_pats_rx_str =
    col_pats.
    filter(is_bare_pat).
    map(x => x.pat.rx_str).
    join('.+')
  col_pats = col_pats.filter(x => ! is_bare_pat(x))
  if ( bare_pats_rx_str !== '' ) {
    col_pats.push({col: "*",
                   pat: {type: 'rx',
                         val: bare_pats_rx_str,
                         rx_str: bare_pats_rx_str}})
  }
  console.log("%s", JSON.stringify(col_pats, null, 2));
}

# I/O

## `in`

`in` - Read input.

```NONE
psv in [--auto] [--raw] [FILE] [file:///FILE] [https?://URL] [-]
```


Aliases: `i`, `-i`

If no arguments are given, read from STDIN.

Arguments:

|                 |             |
| --------------- | ----------- |
|  `FILE`         | Read FILE.  |
|  `file:///FILE` | Read FILE.  |
|  `https?://URL` | GET URL.    |
|  `-`            | Read STDIN. |

Options:

|                 |                                      |
| --------------- | ------------------------------------ |
|  `--auto`, `-a` | Attempt to infer format from suffix. |
|  `--raw`, `-r`  | Do not attempt infer format.         |

Examples:

```NONE
# in: read from STDIN:
$ cat a.tsv | psv in -
a	b	c	d
1	b1	23.763	xspdf
2	b2	-98.73	qwer
3	b3	3451	bixop
1	b4	1.234	zxy
```


```NONE
$ cat a.tsv | psv in
a	b	c	d
1	b1	23.763	xspdf
2	b2	-98.73	qwer
3	b3	3451	bixop
1	b4	1.234	zxy
```


```NONE
# in: HTTP support:
$ psv in https://tinyurl.com/4sscj338
a	b	c	d
1	b1	23.763	xspdf
2	b2	-98.73	qwer
3	b3	3451	bixop
1	b4	1.234	zxy
```



----------------------------------------------------------

## `out`

`out` - write output to URLs.

```NONE
psv out [--encoding=ENC] [FILE] [file///FILE] [https?://...] [-]
```


Aliases: `o`, `o-`

If no arguments are given, write to STDOUT.

Arguments:

|                 |               |
| --------------- | ------------- |
|  `FILE`         | Write FILE.   |
|  `file///FILE`  | Write FILE.   |
|  `https?://...` | PUT URL.      |
|  `-`            | Write STDOUT. |

Options:

|                   |               |
| ----------------- | ------------- |
|  `--encoding=ENC` | Use encoding. |

Examples:

```NONE
# out: Convert TSV to CSV and save to a file:
$ psv in a.tsv // -tsv // csv- // out a.csv

```



----------------------------------------------------------

# Format

## `table-in`

`table-in` - Parse table.

```NONE
psv table-in [--fs=REGEX] [--rs=REGEX] [--max-cols=COUNT] [--columns=COL1,...  |] [--header] [--column=FMT] [--encoding=ENC] [--skip=REGEX]
```


Aliases: `-table`

Options:

|                     |                                     |
| ------------------- | ----------------------------------- |
|  `--fs=REGEX`       | Field separator.                    |
|  `--rs=REGEX`       | Record separator.                   |
|  `--max-cols=COUNT` | Maximum columns.                    |
|  `--header`, `-h`   | Column names are in first row.      |
|  `--column=FMT`     | Column name printf template.        |
|  `--encoding=ENC`   | Encoding of input.                  |
|  `--skip=REGEX`     | Records matching REGEX are skipped. |

Examples:

```NONE
# -table: Parse generic table:
$ psv in users.txt // -table --fs=':'
       c1 c2     c3     c4      c5              c6                 c7
0    root  x      0      0    root           /root          /bin/bash
1  daemon  x      1      1  daemon       /usr/sbin  /usr/sbin/nologin
2     bin  x      2      2     bin            /bin  /usr/sbin/nologin
3     sys  x      3      3     sys            /dev  /usr/sbin/nologin
4   games  x      5     60   games      /usr/games  /usr/sbin/nologin
5     man  x      6     12     man  /var/cache/man  /usr/sbin/nologin
6    mail  x      8      8    mail       /var/mail  /usr/sbin/nologin
7  backup  x     34     34  backup    /var/backups  /usr/sbin/nologin
8  nobody  x  65534  65534  nobody    /nonexistent  /usr/sbin/nologin
9    sshd  x    122  65534               /run/sshd  /usr/sbin/nologin
```


```NONE
# -table: Skip users w/o login:
$ psv in users.txt // -table --fs=':' --skip='.*nologin'
     c1 c2 c3 c4    c5     c6         c7
0  root  x  0  0  root  /root  /bin/bash
```


```NONE
# -table: Generate columns named col01, col02, ...:
$ psv in users.txt // -table --fs=':' --column='col%02d'
       c1 c2     c3     c4      c5              c6                 c7
0    root  x      0      0    root           /root          /bin/bash
1  daemon  x      1      1  daemon       /usr/sbin  /usr/sbin/nologin
2     bin  x      2      2     bin            /bin  /usr/sbin/nologin
3     sys  x      3      3     sys            /dev  /usr/sbin/nologin
4   games  x      5     60   games      /usr/games  /usr/sbin/nologin
5     man  x      6     12     man  /var/cache/man  /usr/sbin/nologin
6    mail  x      8      8    mail       /var/mail  /usr/sbin/nologin
7  backup  x     34     34  backup    /var/backups  /usr/sbin/nologin
8  nobody  x  65534  65534  nobody    /nonexistent  /usr/sbin/nologin
9    sshd  x    122  65534               /run/sshd  /usr/sbin/nologin
```


```NONE
# -table: Set column names or generate them:
$ psv in users.txt // -table --fs=':' --columns=login,,uid,gid,,home,shell
    login c2    uid    gid      c5            home              shell
0    root  x      0      0    root           /root          /bin/bash
1  daemon  x      1      1  daemon       /usr/sbin  /usr/sbin/nologin
2     bin  x      2      2     bin            /bin  /usr/sbin/nologin
3     sys  x      3      3     sys            /dev  /usr/sbin/nologin
4   games  x      5     60   games      /usr/games  /usr/sbin/nologin
5     man  x      6     12     man  /var/cache/man  /usr/sbin/nologin
6    mail  x      8      8    mail       /var/mail  /usr/sbin/nologin
7  backup  x     34     34  backup    /var/backups  /usr/sbin/nologin
8  nobody  x  65534  65534  nobody    /nonexistent  /usr/sbin/nologin
9    sshd  x    122  65534               /run/sshd  /usr/sbin/nologin
```


```NONE
# Convert text data to CSV:
$ psv in us-states.txt // -table --header --fs="\s{2,}" // csv- // o us-states.csv

```


```NONE
# -table: Split fields by 2 or more whitespace chars:
$ psv in us-states.txt // -table --header --fs="\s{2,}" // head 5 // md
|   Rank | State        |   FIPS Code | Population   |
|-------:|:-------------|------------:|:-------------|
|      1 | California   |       06000 | 39,029,342   |
|      2 | Texas        |       48000 | 30,029,572   |
|      3 | Florida      |       12000 | 22,244,823   |
|      4 | New York     |       36000 | 19,677,151   |
|      5 | Pennsylvania |       42000 | 12,972,008   |
```


```NONE
# -table: Split 3 fields:
$ psv in users.txt // -table --fs=':' --max-cols=3
       c1 c2     c3                                           c4
0    root  x      0                       0:root:/root:/bin/bash
1  daemon  x      1         1:daemon:/usr/sbin:/usr/sbin/nologin
2     bin  x      2                 2:bin:/bin:/usr/sbin/nologin
3     sys  x      3                 3:sys:/dev:/usr/sbin/nologin
4   games  x      5        60:games:/usr/games:/usr/sbin/nologin
5     man  x      6      12:man:/var/cache/man:/usr/sbin/nologin
6    mail  x      8           8:mail:/var/mail:/usr/sbin/nologin
7  backup  x     34     34:backup:/var/backups:/usr/sbin/nologin
8  nobody  x  65534  65534:nobody:/nonexistent:/usr/sbin/nologin
9    sshd  x    122           65534::/run/sshd:/usr/sbin/nologin
```



----------------------------------------------------------

## `table-out`

`table-out` - Generate table.

```NONE
psv table-out [--fs=STR] [--rs=STR] [--header]
```


Aliases: `table-`

Options:

|             |                   |
| ----------- | ----------------- |
|  `--fs=STR` | Field separator.  |
|  `--rs=STR` | Record separator. |
|  `--header` | Emit header.      |

Examples:

```NONE
$ psv in a.csv // table-
a b c d
1 b1 23.763 xspdf
2 b2 -98.73 qwer
3 b3 3451.0 bixop
1 b4 1.234 zxy
```


```NONE
$ psv in a.csv // table- --fs='|'
a|b|c|d
1|b1|23.763|xspdf
2|b2|-98.73|qwer
3|b3|3451.0|bixop
1|b4|1.234|zxy
```



----------------------------------------------------------

## `tsv-in`

`tsv-in` - Parse TSV.

```NONE
psv tsv-in [--header]
```


Aliases: `-tsv`

Options:

|             |                      |
| ----------- | -------------------- |
|  `--header` | First row is header. |

Examples:

```NONE
# Convert TSV stdin to CSV stdout:
$ cat a.tsv | psv -tsv // csv-
a,b,c,d
1,b1,23.763,xspdf
2,b2,-98.73,qwer
3,b3,3451.0,bixop
1,b4,1.234,zxy
```


```NONE
# Convert TSV to Markdown:
$ psv in a.tsv // md
|   a | b   |        c | d     |
|----:|:----|---------:|:------|
|   1 | b1  |   23.763 | xspdf |
|   2 | b2  |  -98.73  | qwer  |
|   3 | b3  | 3451     | bixop |
|   1 | b4  |    1.234 | zxy   |
```


```NONE
# Convert HTTP TSV content to Markdown:
$ psv in https://tinyurl.com/4sscj338 // -tsv // md
|   a | b   |        c | d     |
|----:|:----|---------:|:------|
|   1 | b1  |   23.763 | xspdf |
|   2 | b2  |  -98.73  | qwer  |
|   3 | b3  | 3451     | bixop |
|   1 | b4  |    1.234 | zxy   |
```



----------------------------------------------------------

## `tsv-out`

`tsv-out` - Generate TSV.

```NONE
psv tsv-out
```


Aliases: `tsv-`

Examples:

```NONE
# Convert CSV to TSV:
$ psv in a.csv // tsv-
a	b	c	d
1	b1	23.763	xspdf
2	b2	-98.73	qwer
3	b3	3451.0	bixop
1	b4	1.234	zxy
```



----------------------------------------------------------

## `csv-in`

`csv-in` - Parse CSV.

```NONE
psv csv-in [--header]
```


Aliases: `-csv`

Options:

|             |                      |
| ----------- | -------------------- |
|  `--header` | First row is header. |

Examples:

```NONE
# Use first row as header:
$ psv in a.csv // -csv
   a   b         c      d
0  1  b1    23.763  xspdf
1  2  b2   -98.730   qwer
2  3  b3  3451.000  bixop
3  1  b4     1.234    zxy
```


```NONE
# Generate arbitrary columns:
$ psv in a.csv // -csv --no-header
  c1  c2      c3     c4
0  a   b       c      d
1  1  b1  23.763  xspdf
2  2  b2  -98.73   qwer
3  3  b3  3451.0  bixop
4  1  b4   1.234    zxy
```


```NONE
# Convert CSV to JSON:
$ psv in a.csv // -csv // json-
[
  {
    "a":1,
    "b":"b1",
    "c":23.763,
    "d":"xspdf"
  },
  {
    "a":2,
    "b":"b2",
    "c":-98.73,
    "d":"qwer"
  },
  {
    "a":3,
    "b":"b3",
    "c":3451.0,
    "d":"bixop"
  },
  {
    "a":1,
    "b":"b4",
    "c":1.234,
    "d":"zxy"
  }
]
```



----------------------------------------------------------

## `csv-out`

`csv-out` - Generate CSV.

```NONE
psv csv-out
```


Aliases: `csv-`, `csv`

Examples:

```NONE
# tsv, csv: Convert TSV to CSV:
$ psv in a.tsv // -tsv // csv-
a,b,c,d
1,b1,23.763,xspdf
2,b2,-98.73,qwer
3,b3,3451.0,bixop
1,b4,1.234,zxy
```



----------------------------------------------------------

## `markdown-in`

`markdown-in` - Parse Markdown.

```NONE
psv markdown-in
```


Aliases: `-markdown`, `-md`, `md-in`

Examples:

```NONE
# Convert TSV to Markdown to CSV:
$ psv in a.tsv // md- // out a.md

```


```NONE
$ psv in a.md // -md // csv
a,b,c,d
1,b1,23.763,xspdf
2,b2,-98.73,qwer
3,b3,3451,bixop
1,b4,1.234,zxy
```



----------------------------------------------------------

## `markdown-out`

`markdown-out` - Generate Markdown.

```NONE
psv markdown-out
```


Aliases: `markdown-`, `markdown`, `md-out`, `md-`, `md`

Examples:

```NONE
# Convert TSV on STDIN to Markdown:
$ cat a.tsv | psv -tsv // md
|   a | b   |        c | d     |
|----:|:----|---------:|:------|
|   1 | b1  |   23.763 | xspdf |
|   2 | b2  |  -98.73  | qwer  |
|   3 | b3  | 3451     | bixop |
|   1 | b4  |    1.234 | zxy   |
```



----------------------------------------------------------

## `json-in`

`json-in` - Parse JSON.

```NONE
psv json-in [--orient=ORIENT]
```


Aliases: `-json`, `-js`

Options:

|                    |                                    |
| ------------------ | ---------------------------------- |
|  `--orient=ORIENT` | Orientation: see pandas read_json. |

----------------------------------------------------------

## `json-out`

`json-out` - Generate JSON array of objects.

```NONE
psv json-out
```


Aliases: `json-`, `json`, `js-`, `js`

Examples:

```NONE
# csv, json: Convert CSV to JSON:
$ psv in a.csv // -csv // json-
[
  {
    "a":1,
    "b":"b1",
    "c":23.763,
    "d":"xspdf"
  },
  {
    "a":2,
    "b":"b2",
    "c":-98.73,
    "d":"qwer"
  },
  {
    "a":3,
    "b":"b3",
    "c":3451.0,
    "d":"bixop"
  },
  {
    "a":1,
    "b":"b4",
    "c":1.234,
    "d":"zxy"
  }
]
```



----------------------------------------------------------

## `dataframe-in`

`dataframe-in` - Read Pandas Dataframe pickle.

```NONE
psv dataframe-in
```


Aliases: `-dataframe`

----------------------------------------------------------

## `dataframe-out`

`dataframe-out` - Write Pandas DataFrame pickle.

```NONE
psv dataframe-out
```


Aliases: `dataframe-`, `dataframe`

----------------------------------------------------------

## `html-out`

`html-out` - Generate HTML.

```NONE
psv html-out [--title=NAME] [--header] [--simple] [--filtering] [--sorting] [--row-index] [--table-only] [--styled]
```


Aliases: `html-`, `html`

Options:

|                       |                                              |
| --------------------- | -------------------------------------------- |
|  `--title=NAME`       | Set `&lt;title&gt;` and add a `&lt;div&gt;`. |
|  `--header`, `-h`     | Add table header.                            |
|  `--simple`, `-S`     | Minimal format.                              |
|  `--filtering`, `-f`  | Add filtering UI.                            |
|  `--sorting`, `-s`    | Add sorting support.                         |
|  `--row-index`, `-i`  | Add row index to first column.               |
|  `--table-only`, `-T` | Render only a `&lt;table&gt;`.               |
|  `--styled`           | Add style.                                   |

Examples:

```NONE
$ psv in a.csv // html // o a.html

```


```NONE
$ w3m -dump a.html
┌─┬──┬───────┬─────┐
│a│b │   c   │  d  │
├─┼──┼───────┼─────┤
│1│b1│23.763 │xspdf│
├─┼──┼───────┼─────┤
│2│b2│-98.73 │qwer │
├─┼──┼───────┼─────┤
│3│b3│3451.0 │bixop│
├─┼──┼───────┼─────┤
│1│b4│1.234  │zxy  │
└─┴──┴───────┴─────┘
```


```NONE
$ psv in users.txt // -table --fs=":" // html --title=users.txt // o users-with-title.html

```


```NONE
$ w3m -dump users-with-title.html
users.txt
┌──────┬──┬─────┬─────┬──────┬──────────────┬─────────────────┐
│  c1  │c2│ c3  │ c4  │  c5  │      c6      │       c7        │
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│root  │x │0    │0    │root  │/root         │/bin/bash        │
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│daemon│x │1    │1    │daemon│/usr/sbin     │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│bin   │x │2    │2    │bin   │/bin          │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│sys   │x │3    │3    │sys   │/dev          │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│games │x │5    │60   │games │/usr/games    │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│man   │x │6    │12   │man   │/var/cache/man│/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│mail  │x │8    │8    │mail  │/var/mail     │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│backup│x │34   │34   │backup│/var/backups  │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│nobody│x │65534│65534│nobody│/nonexistent  │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│sshd  │x │122  │65534│      │/run/sshd     │/usr/sbin/nologin│
└──────┴──┴─────┴─────┴──────┴──────────────┴─────────────────┘
```


```NONE
$ psv in users.txt // -table --fs=":" // html --no-header // o users-no-header.html

```


```NONE
$ w3m -dump users-no-header.html
┌──────┬─┬─────┬─────┬──────┬──────────────┬─────────────────┐
│root  │x│0    │0    │root  │/root         │/bin/bash        │
├──────┼─┼─────┼─────┼──────┼──────────────┼─────────────────┤
│daemon│x│1    │1    │daemon│/usr/sbin     │/usr/sbin/nologin│
├──────┼─┼─────┼─────┼──────┼──────────────┼─────────────────┤
│bin   │x│2    │2    │bin   │/bin          │/usr/sbin/nologin│
├──────┼─┼─────┼─────┼──────┼──────────────┼─────────────────┤
│sys   │x│3    │3    │sys   │/dev          │/usr/sbin/nologin│
├──────┼─┼─────┼─────┼──────┼──────────────┼─────────────────┤
│games │x│5    │60   │games │/usr/games    │/usr/sbin/nologin│
├──────┼─┼─────┼─────┼──────┼──────────────┼─────────────────┤
│man   │x│6    │12   │man   │/var/cache/man│/usr/sbin/nologin│
├──────┼─┼─────┼─────┼──────┼──────────────┼─────────────────┤
│mail  │x│8    │8    │mail  │/var/mail     │/usr/sbin/nologin│
├──────┼─┼─────┼─────┼──────┼──────────────┼─────────────────┤
│backup│x│34   │34   │backup│/var/backups  │/usr/sbin/nologin│
├──────┼─┼─────┼─────┼──────┼──────────────┼─────────────────┤
│nobody│x│65534│65534│nobody│/nonexistent  │/usr/sbin/nologin│
├──────┼─┼─────┼─────┼──────┼──────────────┼─────────────────┤
│sshd  │x│122  │65534│      │/run/sshd     │/usr/sbin/nologin│
└──────┴─┴─────┴─────┴──────┴──────────────┴─────────────────┘
```


```NONE
$ psv in users.txt // -table --fs=":" // html -fs // o users-with-fs.html

```


```NONE
$ w3m -dump users-with-fs.html
┌─────────────────────────────────────────────────────────────┐
│             [                    ] X 10  /  10              │
├──────┬──┬─────┬─────┬──────┬──────────────┬─────────────────┤
│  c1  │c2│ c3  │ c4  │  c5  │      c6      │       c7        │
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│root  │x │0    │0    │root  │/root         │/bin/bash        │
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│daemon│x │1    │1    │daemon│/usr/sbin     │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│bin   │x │2    │2    │bin   │/bin          │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│sys   │x │3    │3    │sys   │/dev          │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│games │x │5    │60   │games │/usr/games    │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│man   │x │6    │12   │man   │/var/cache/man│/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│mail  │x │8    │8    │mail  │/var/mail     │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│backup│x │34   │34   │backup│/var/backups  │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│nobody│x │65534│65534│nobody│/nonexistent  │/usr/sbin/nologin│
├──────┼──┼─────┼─────┼──────┼──────────────┼─────────────────┤
│sshd  │x │122  │65534│      │/run/sshd     │/usr/sbin/nologin│
└──────┴──┴─────┴─────┴──────┴──────────────┴─────────────────┘
```



----------------------------------------------------------

## `sql-`

`sql-` - Write SQL.

```NONE
psv sql-
```


Aliases: `sql`

Examples:

```NONE
# sql: Convert TSV to SQL schema:
$ psv in a.tsv // sql
CREATE TABLE "__table__" (
"index" INTEGER,
  "a" INTEGER,
  "b" TEXT,
  "c" REAL,
  "d" TEXT
)
```



----------------------------------------------------------

## `yaml-out`

`yaml-out` - Generate YAML.

```NONE
psv yaml-out
```


Aliases: `yaml-`, `yaml`, `yml-`, `yml`

Examples:

```NONE
$ psv in a.csv // yaml
- a: 1
  b: b1
  c: 23.763
  d: xspdf
- a: 2
  b: b2
  c: -98.73
  d: qwer
- a: 3
  b: b3
  c: 3451.0
  d: bixop
- a: 1
  b: b4
  c: 1.234
  d: zxy
```



----------------------------------------------------------

## `xls-in`

`xls-in` - Read XLS Spreadsheet.

```NONE
psv xls-in [--sheet-name=NAME] [--header]
```


Aliases: `-xls`

Options:

|                      |                  |
| -------------------- | ---------------- |
|  `--sheet-name=NAME` | Sheet name.      |
|  `--header`, `-h`    | Generate header. |

Examples:

```NONE
$ psv in a.xlsx // -xls // md
|   a | b   |        c | d     |
|----:|:----|---------:|:------|
|   1 | b1  |   23.763 | xspdf |
|   2 | b2  |  -98.73  | qwer  |
|   3 | b3  | 3451     | bixop |
|   1 | b4  |    1.234 | zxy   |
```


```NONE
$ psv in a.xlsx // -xls --no-header // md
| c0   | c1   | c2     | c3    |
|:-----|:-----|:-------|:------|
| a    | b    | c      | d     |
| 1    | b1   | 23.763 | xspdf |
| 2    | b2   | -98.73 | qwer  |
| 3    | b3   | 3451   | bixop |
| 1    | b4   | 1.234  | zxy   |
```



----------------------------------------------------------

## `xls-out`

`xls-out` - Generate XLS Spreadsheet.

```NONE
psv xls-out [--sheet-name=NAME] [--header]
```


Aliases: `xls-`, `xls`

Options:

|                      |                  |
| -------------------- | ---------------- |
|  `--sheet-name=NAME` | Sheet name.      |
|  `--header`, `-h`    | Generate header. |

Examples:

```NONE
$ psv in a.csv // xls // o a.xlsx

```


```NONE
$ file a.xlsx
a.xlsx: Microsoft Excel 2007+
```



----------------------------------------------------------

## `extract`

`extract` - Extract fields by Regexp.

```NONE
psv extract
```


Aliases: `rx`, `re`, `rex`

Examples:

```NONE
# Extract by names:
$ psv in users.txt // extract '^(?P<login>[^:]+)' // md
| login   |
|:--------|
| root    |
| daemon  |
| bin     |
| sys     |
| games   |
| man     |
| mail    |
| backup  |
| nobody  |
| sshd    |
```


```NONE
$ psv in users.txt // extract '^(?P<login>[^:]+):(?P<rest>.*)' // md
| login   | rest                                                |
|:--------|:----------------------------------------------------|
| root    | x:0:0:root:/root:/bin/bash                          |
| daemon  | x:1:1:daemon:/usr/sbin:/usr/sbin/nologin            |
| bin     | x:2:2:bin:/bin:/usr/sbin/nologin                    |
| sys     | x:3:3:sys:/dev:/usr/sbin/nologin                    |
| games   | x:5:60:games:/usr/games:/usr/sbin/nologin           |
| man     | x:6:12:man:/var/cache/man:/usr/sbin/nologin         |
| mail    | x:8:8:mail:/var/mail:/usr/sbin/nologin              |
| backup  | x:34:34:backup:/var/backups:/usr/sbin/nologin       |
| nobody  | x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin |
| sshd    | x:122:65534::/run/sshd:/usr/sbin/nologin            |
```


```NONE
# Extract unnamed group:
$ psv in users.txt // extract --unnamed '^(?P<login>[^:]+)(.*)' // md
| login   | c2                                                   |
|:--------|:-----------------------------------------------------|
| root    | :x:0:0:root:/root:/bin/bash                          |
| daemon  | :x:1:1:daemon:/usr/sbin:/usr/sbin/nologin            |
| bin     | :x:2:2:bin:/bin:/usr/sbin/nologin                    |
| sys     | :x:3:3:sys:/dev:/usr/sbin/nologin                    |
| games   | :x:5:60:games:/usr/games:/usr/sbin/nologin           |
| man     | :x:6:12:man:/var/cache/man:/usr/sbin/nologin         |
| mail    | :x:8:8:mail:/var/mail:/usr/sbin/nologin              |
| backup  | :x:34:34:backup:/var/backups:/usr/sbin/nologin       |
| nobody  | :x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin |
| sshd    | :x:122:65534::/run/sshd:/usr/sbin/nologin            |
```


```NONE
# Extract unnamed groups using a template:
$ psv in users.txt // extract --unnamed='group-%d' '^(?P<login>[^:]+)(.*)' // md
| login   | group-2                                              |
|:--------|:-----------------------------------------------------|
| root    | :x:0:0:root:/root:/bin/bash                          |
| daemon  | :x:1:1:daemon:/usr/sbin:/usr/sbin/nologin            |
| bin     | :x:2:2:bin:/bin:/usr/sbin/nologin                    |
| sys     | :x:3:3:sys:/dev:/usr/sbin/nologin                    |
| games   | :x:5:60:games:/usr/games:/usr/sbin/nologin           |
| man     | :x:6:12:man:/var/cache/man:/usr/sbin/nologin         |
| mail    | :x:8:8:mail:/var/mail:/usr/sbin/nologin              |
| backup  | :x:34:34:backup:/var/backups:/usr/sbin/nologin       |
| nobody  | :x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin |
| sshd    | :x:122:65534::/run/sshd:/usr/sbin/nologin            |
```



----------------------------------------------------------

# Manipulation

## `range`

`range` - Subset of rows.

```NONE
psv range [--start=START] [--end=END] [--step=STEP] [start [end] [step]] [[start]:[end]:step]
```


Aliases: `r`

Arguments:

|                       |                          |
| --------------------- | ------------------------ |
|  `start [end] [step]` | For 1 or more arguments. |
|  `[start]:[end]:step` | Python-style range.      |

Options:

|                  |                |
| ---------------- | -------------- |
|  `--start=START` | Inclusive.     |
|  `--end=END`     | Non-inclusive. |
|  `--step=STEP`   | Default: 1.    |

Examples:

```NONE
# range: select a range of rows:
$ psv in a.tsv // seq --start=0 // range 1 3 // md
|   a | b   |       c | d     |   __i__ |
|----:|:----|--------:|:------|--------:|
|   2 | b2  |  -98.73 | qwer  |       1 |
|   3 | b3  | 3451    | bixop |       2 |
```


```NONE
# range: every even row:
$ psv in a.tsv // seq --start=0 // range --step=2 // md
|   a | b   |        c | d     |   __i__ |
|----:|:----|---------:|:------|--------:|
|   1 | b1  |   23.763 | xspdf |       0 |
|   3 | b3  | 3451     | bixop |       2 |
```



----------------------------------------------------------

## `head`

`head` - First N rows

```NONE
psv head
```


Aliases: `h`

N : Default: 10

Examples:

```NONE
# head:
$ psv in us-states.txt // -table // head 5 // md
| c1   | c2         | c3    | c4         | c5         | c6   |
|:-----|:-----------|:------|:-----------|:-----------|:-----|
| Rank | State      | FIPS  | Code       | Population |      |
| 1    | California | 06000 | 39,029,342 |            |      |
| 2    | Texas      | 48000 | 30,029,572 |            |      |
| 3    | Florida    | 12000 | 22,244,823 |            |      |
| 4    | New        | York  | 36000      | 19,677,151 |      |
```



----------------------------------------------------------

## `tail`

`tail` - Last N rows

```NONE
psv tail
```


Aliases: `t`

N : Default: 10

Examples:

```NONE
# tail: last 3 rows:
$ psv in us-states.txt // -table // tail 3 // md
|   c1 | c2       | c3    | c4       | c5    | c6      |
|-----:|:---------|:------|:---------|:------|:--------|
|   49 | District | of    | Columbia | 11000 | 671,803 |
|   50 | Vermont  | 50000 | 647,064  |       |         |
|   51 | Wyoming  | 56000 | 581,381  |       |         |
```



----------------------------------------------------------

## `reverse`

`reverse` - Reverse rows.  Same as "range --step=-1"

```NONE
psv reverse
```


Aliases: `tac`

Examples:

```NONE
# reverse:
$ psv in a.tsv // seq // tac // md
| a   | b   | c   | d   | __i__   |
|-----|-----|-----|-----|---------|
```



----------------------------------------------------------

## `shuffle`

`shuffle` - shuffle rows.

```NONE
psv shuffle [--seed=SEED]
```


Aliases: `rand`

Options:

|                |         |
| -------------- | ------- |
|  `--seed=SEED` | String. |

Examples:

```NONE
$ psv in a.tsv // shuffle --seed=5 // md
|   a | b   |        c | d     |
|----:|:----|---------:|:------|
|   3 | b3  | 3451     | bixop |
|   1 | b4  |    1.234 | zxy   |
|   2 | b2  |  -98.73  | qwer  |
|   1 | b1  |   23.763 | xspdf |
```



----------------------------------------------------------

## `cut`

`cut` - Cut specified columns.

```NONE
psv cut [NAME] [I] [COL:-] [*] [NAME*]
```


Aliases: `c`, `x`

psv in a.tsv // cut 2,d // md

Arguments:

|          |                                             |
| -------- | ------------------------------------------- |
|  `NAME`  | Select name.                                |
|  `I`     | Select index.                               |
|  `COL:-` | Remove column.                              |
|  `*`     | Add all columns.                            |
|  `NAME*` | Any columns starting with &quot;NAME&quot;. |

Examples:

```NONE
# cut: select columns by index and name:
# cut: remove c, put d before other columns,
$ psv in a.tsv // cut d '*' c:- // md
| d     |   a | b   |
|:------|----:|:----|
| xspdf |   1 | b1  |
| qwer  |   2 | b2  |
| bixop |   3 | b3  |
| zxy   |   1 | b4  |
```



----------------------------------------------------------

## `uniq`

`uniq` - Return unique rows.

```NONE
psv uniq
```


Aliases: `u`

----------------------------------------------------------

## `sort`

`sort` - Sort rows by columns.

```NONE
psv sort [--reverse] [--numeric] [--coerce=TYPE] [COL] [COL:-] [COL:+]
```


Aliases: `s`

Arguments:

|          |                         |
| -------- | ----------------------- |
|  `COL`   | Sort by COL ascending.  |
|  `COL:-` | Sort by COL descending. |
|  `COL:+` | Sort by COL ascending.  |

Options:

|                    |                        |
| ------------------ | ---------------------- |
|  `--reverse`, `-r` | Sort descending.       |
|  `--numeric`, `-n` | Sort as numeric.       |
|  `--coerce=TYPE`   | Sort by coerced value. |

Examples:

```NONE
# sort: increasing:
$ psv in a.tsv // seq i // sort c // md
|   a | b   |        c | d     |   i |
|----:|:----|---------:|:------|----:|
|   2 | b2  |  -98.73  | qwer  |   2 |
|   1 | b4  |    1.234 | zxy   |   4 |
|   1 | b1  |   23.763 | xspdf |   1 |
|   3 | b3  | 3451     | bixop |   3 |
```


```NONE
# sort: decreasing:
$ psv in a.tsv // seq i // sort -r c // md
|   a | b   |        c | d     |   i |
|----:|:----|---------:|:------|----:|
|   3 | b3  | 3451     | bixop |   3 |
|   1 | b1  |   23.763 | xspdf |   1 |
|   1 | b4  |    1.234 | zxy   |   4 |
|   2 | b2  |  -98.73  | qwer  |   2 |
```


```NONE
# sort: by a decreasing, c increasing:
$ psv in a.tsv // seq i // md
|   a | b   |        c | d     |   i |
|----:|:----|---------:|:------|----:|
|   1 | b1  |   23.763 | xspdf |   1 |
|   2 | b2  |  -98.73  | qwer  |   2 |
|   3 | b3  | 3451     | bixop |   3 |
|   1 | b4  |    1.234 | zxy   |   4 |
```


```NONE
$ psv in a.tsv // seq i // sort a:- c // md
|   a | b   |        c | d     |   i |
|----:|:----|---------:|:------|----:|
|   3 | b3  | 3451     | bixop |   3 |
|   2 | b2  |  -98.73  | qwer  |   2 |
|   1 | b4  |    1.234 | zxy   |   4 |
|   1 | b1  |   23.763 | xspdf |   1 |
```



----------------------------------------------------------

## `grep`

`grep` - Search for rows where columns match a regex.

```NONE
psv grep [--all] [--any] [--fixed-strings] [--ignore-case] [--invert-match] [COL REGEX ...] [REGEX]
```


Aliases: `g`

Arguments:

|                  |                                                    |
| ---------------- | -------------------------------------------------- |
|  `COL REGEX ...` | Select rows where COL REGEX pairs match.           |
|  `REGEX`         | Select rows where REGEX is applied to all columns. |

Options:

|                          |                                                            |
| ------------------------ | ---------------------------------------------------------- |
|  `--all`                 | All patterns must match.                                   |
|  `--any`                 | Any pattern must match.                                    |
|  `--fixed-strings`, `-F` | Match fixed string.                                        |
|  `--ignore-case`, `-i`   | Ignore case distinctions.                                  |
|  `--invert-match`, `-v`  | Invert the sense of matching, to select non-matching rows. |

Examples:

```NONE
# grep: match columns by regex:
$ psv in a.tsv // grep d 'x' // md
|   a | b   |        c | d     |
|----:|:----|---------:|:------|
|   1 | b1  |   23.763 | xspdf |
|   3 | b3  | 3451     | bixop |
|   1 | b4  |    1.234 | zxy   |
```


```NONE
$ psv in a.tsv // grep d '^x' // md
|   a | b   |      c | d     |
|----:|:----|-------:|:------|
|   1 | b1  | 23.763 | xspdf |
```


```NONE
$ psv in a.tsv // grep d 'x.+p' // md
|   a | b   |        c | d     |
|----:|:----|---------:|:------|
|   1 | b1  |   23.763 | xspdf |
|   3 | b3  | 3451     | bixop |
```


```NONE
# grep: match where d contains "x" and b ends with "3":
$ psv in a.tsv // grep d 'x' b '3$' // md
|   a | b   |    c | d     |
|----:|:----|-----:|:------|
|   3 | b3  | 3451 | bixop |
```



----------------------------------------------------------

## `translate`

`translate` - Translate characters.

```NONE
psv translate [--delete] [SRC DST COL,...] [-d DEL COL,...]
```


Aliases: `tr`

Similar to Unix tr command.

Arguments:

|                    |                                        |
| ------------------ | -------------------------------------- |
|  `SRC DST COL,...` | Map chars from SRC to DST in each COL. |
|  `-d DEL COL,...`  | Delete chars in DEL in each COL.       |

Options:

|                   |                    |
| ----------------- | ------------------ |
|  `--delete`, `-d` | Delete characters. |

Examples:

```NONE
# translate: change characters in specific field:
$ psv in us-states.txt // -table --header --fs="\s{2,}" // tr ',' '_' Population // head // md
|   Rank | State          |   FIPS Code |   Population |
|-------:|:---------------|------------:|-------------:|
|      1 | California     |       06000 |   39_029_342 |
|      2 | Texas          |       48000 |   30_029_572 |
|      3 | Florida        |       12000 |   22_244_823 |
|      4 | New York       |       36000 |   19_677_151 |
|      5 | Pennsylvania   |       42000 |   12_972_008 |
|      6 | Illinois       |       17000 |   12_582_032 |
|      7 | Ohio           |       39000 |   11_756_058 |
|      8 | Georgia        |       13000 |   10_912_876 |
|      9 | North Carolina |       37000 |   10_698_973 |
|     10 | Michigan       |       26000 |   10_034_113 |
```


```NONE
# translate: delete characters:
$ psv in us-states.txt // -table --header --fs="\s{2,}" // tr -d ', ' // head // md
|   Rank | State         |   FIPS Code |   Population |
|-------:|:--------------|------------:|-------------:|
|      1 | California    |       06000 |     39029342 |
|      2 | Texas         |       48000 |     30029572 |
|      3 | Florida       |       12000 |     22244823 |
|      4 | NewYork       |       36000 |     19677151 |
|      5 | Pennsylvania  |       42000 |     12972008 |
|      6 | Illinois      |       17000 |     12582032 |
|      7 | Ohio          |       39000 |     11756058 |
|      8 | Georgia       |       13000 |     10912876 |
|      9 | NorthCarolina |       37000 |     10698973 |
|     10 | Michigan      |       26000 |     10034113 |
```



----------------------------------------------------------

## `null`

`null` - Does nothing.

```NONE
psv null
```


Examples:

```NONE
# null: does nothing:
$ psv in a.tsv // null IGNORED --OPTION=VALUE // md
|   a | b   |        c | d     |
|----:|:----|---------:|:------|
|   1 | b1  |   23.763 | xspdf |
|   2 | b2  |  -98.73  | qwer  |
|   3 | b3  | 3451     | bixop |
|   1 | b4  |    1.234 | zxy   |
```



----------------------------------------------------------

# Summaries

## `count`

`count` - Count of unique column values.

```NONE
psv count [--column=NAME] [COL ...]
```


Arguments:

|            |                      |
| ---------- | -------------------- |
|  `COL ...` | Columns to group by. |

Options:

|                  |                             |
| ---------------- | --------------------------- |
|  `--column=NAME` | Default: &quot;count&quot;. |

Examples:

```NONE
# Count the number of transfers by Payer:
$ psv in transfers.csv // count Payer // md
| Payer   |   count |
|:--------|--------:|
| Alice   |       2 |
| Bob     |       4 |
| William |       1 |
```


```NONE
# Count the number of transfers from Payer to Payee:
$ psv in transfers.csv // count Payer,Payee // md
| Payer   | Payee   |   count |
|:--------|:--------|--------:|
| Alice   | Frank   |       1 |
| Alice   | Joe     |       1 |
| Bob     | Alice   |       3 |
| Bob     | Joe     |       1 |
| William | Rich    |       1 |
```


```NONE
# Count the number of transfers from Payee:
$ psv in transfers.csv // count --column=PayeeTransfers Payee // md
| Payee   |   PayeeTransfers |
|:--------|-----------------:|
| Alice   |                3 |
| Frank   |                1 |
| Joe     |                2 |
| Rich    |                1 |
```



----------------------------------------------------------

## `summary`

`summary` - Summary of column values.

```NONE
psv summary [COL,... [STAT,...] [GROUP-BY,...]] [COL,...] [STAT,...] [GROUP-BY,...]
```


Arguments:

|                                      |                                                                     |
| ------------------------------------ | ------------------------------------------------------------------- |
|  `COL,... [STAT,...] [GROUP-BY,...]` | COLs to summarize STATs grouped by GROUP-BY.                        |
|  `COL,...`                           | Any numeric columns separated by &quot;,&quot;.                     |
|  `STAT,...`                          | One or more of: &#x27;count,sum,min,max,mean,median,std,skew&#x27;. |
|  `GROUP-BY,...`                      | Any column not in the COL list.                                     |

Examples:

```NONE
# Summary of transfers by Payer and Payee:
$ psv in transfers.csv // summary Amount '*' Payer,Payee // md
| Payer   | Payee   |   Amount_count |   Amount_sum |   Amount_min |   Amount_mean |   Amount_median |   Amount_std |   Amount_max |   Amount_skew |
|:--------|:--------|---------------:|-------------:|-------------:|--------------:|----------------:|-------------:|-------------:|--------------:|
| Alice   | Frank   |              1 |        10.99 |        10.99 |         10.99 |           10.99 |     nan      |        10.99 |     nan       |
| Alice   | Joe     |              1 |        45.23 |        45.23 |         45.23 |           45.23 |     nan      |        45.23 |     nan       |
| Bob     | Alice   |              3 |       114.33 |         1.99 |         38.11 |           12.34 |      53.8476 |       100    |       1.66034 |
| Bob     | Joe     |              1 |        30.25 |        30.25 |         30.25 |           30.25 |     nan      |        30.25 |     nan       |
| William | Rich    |              1 |         9.33 |         9.33 |          9.33 |            9.33 |     nan      |         9.33 |     nan       |
```


```NONE
# Summary of transfers by Payer:
$ psv in transfers.csv // summary Amount count,sum Payer // md
| Payer   |   Amount_count |   Amount_sum |
|:--------|---------------:|-------------:|
| Alice   |              2 |        56.22 |
| Bob     |              4 |       144.58 |
| William |              1 |         9.33 |
```


```NONE
# Sum of Fee by Payee:
$ psv in transfers.csv // summary Fee sum Payee // md
| Payee   |   Fee_sum |
|:--------|----------:|
| Alice   |     15.7  |
| Frank   |      1.01 |
| Joe     |      3.75 |
| Rich    |      0.25 |
```


```NONE
# Summary of all transfer Ammount and Fee:
$ psv in transfers.csv // cut Amount,Fee // summary Amount,Fee // md
| index   |   Amount_count |   Amount_sum |   Amount_min |   Amount_mean |   Amount_median |   Amount_std |   Amount_max |   Amount_skew |   Fee_count |   Fee_sum |   Fee_min |   Fee_mean |   Fee_median |   Fee_std |   Fee_max |   Fee_skew |
|:--------|---------------:|-------------:|-------------:|--------------:|----------------:|-------------:|-------------:|--------------:|------------:|----------:|----------:|-----------:|-------------:|----------:|----------:|-----------:|
| Amount  |              7 |       210.13 |         1.99 |       30.0186 |           12.34 |      34.1981 |          100 |       1.76746 |         nan |    nan    |     nan   |  nan       |       nan    | nan       |       nan |   nan      |
| Fee     |            nan |       nan    |       nan    |      nan      |          nan    |     nan      |          nan |     nan       |           7 |     20.71 |       0.1 |    2.95857 |         1.01 |   5.36956 |        15 |     2.5277 |
```



----------------------------------------------------------

## `stats`

`stats` - Table of column names and basic statistics.

```NONE
psv stats
```


Examples:

```NONE
$ psv in a.tsv // stats // cols // cut name,dtype.name // md
| name   | dtype.name   |
|:-------|:-------------|
| name   | object       |
| count  | int64        |
| first  | object       |
| middle | object       |
| last   | object       |
| min    | object       |
| mean   | float64      |
| median | float64      |
| max    | object       |
| std    | float64      |
| q25    | float64      |
| q50    | float64      |
| q75    | float64      |
```


```NONE
$ psv in a.tsv // stats // cut name,count,min,max
  name  count    min     max
0    a      4      1       3
1    b      4     b1      b4
2    c      4 -98.73  3451.0
3    d      4  bixop     zxy
```



----------------------------------------------------------

# Types

## `coerce`

`coerce` - Corece column types.

```NONE
psv coerce [COL:TYPE ...]
```


Aliases: `astype`

TYPES:

* `numeric`      - to `int64` or `float64`.
* `int`          - to `int64`.
* `float`        - to `float64`.
* `timedelta`    - string to `timedelta64[ns]`.
* `datetime`     - string to `datetime`.
* `second`       - string to `timedelta64[ns]` to `float` seconds.
* `minute`       - string to `timedelta64[ns]` to `float` minutes.
* `hour`         - string to `timedelta64[ns]` to `float` hours.
* `day`          - string to `timedelta64[ns]` to `float` days.
* `ipaddr`       - string to `ipaddress`.  See python `ipaddress` module.

Arguments:

|                 |                           |
| --------------- | ------------------------- |
|  `COL:TYPE ...` | Column to coerce to TYPE. |

Examples:

```NONE
$ psv in us-states.csv // shuffle // head 10 // cut State,Population // csv- // o us-states-sample.csv

```


```NONE
$ psv in us-states-sample.csv // sort Population
           State  Population
8        Montana   1,122,867
2          Maine   1,385,340
3  New Hampshire   1,395,231
0          Idaho   1,939,033
5       Illinois  12,582,032
9   Pennsylvania  12,972,008
6       New York  19,677,151
4        Florida  22,244,823
7       Oklahoma   4,019,800
1      Louisiana   4,590,241
```


```NONE
$ psv in us-states-sample.csv // coerce Population:int // sort Population
           State  Population
8        Montana     1122867
2          Maine     1385340
3  New Hampshire     1395231
0          Idaho     1939033
7       Oklahoma     4019800
1      Louisiana     4590241
5       Illinois    12582032
9   Pennsylvania    12972008
6       New York    19677151
4        Florida    22244823
```



----------------------------------------------------------

# Metadata

## `add-sequence`

`add-sequence` - Add a column with a sequence of numbers or random values.

```NONE
psv add-sequence [--column=NAME] [--start=START] [--step=STEP] [--uuid]
```


Aliases: `seq`

Options:

|                  |                             |
| ---------------- | --------------------------- |
|  `--column=NAME` | Default: &quot;__i__&quot;. |
|  `--start=START` | Default: 1.                 |
|  `--step=STEP`   | Default: 1.                 |
|  `--uuid`        | Generate a UUID-4.          |

Examples:

```NONE
# add-sequence: add a column with a sequence:
$ psv in a.tsv // seq // md
|   a | b   |        c | d     |   __i__ |
|----:|:----|---------:|:------|--------:|
|   1 | b1  |   23.763 | xspdf |       1 |
|   2 | b2  |  -98.73  | qwer  |       2 |
|   3 | b3  | 3451     | bixop |       3 |
|   1 | b4  |    1.234 | zxy   |       4 |
```


```NONE
# add-sequence: start at 0:
$ psv in a.tsv // seq --start=0 // md
|   a | b   |        c | d     |   __i__ |
|----:|:----|---------:|:------|--------:|
|   1 | b1  |   23.763 | xspdf |       0 |
|   2 | b2  |  -98.73  | qwer  |       1 |
|   3 | b3  | 3451     | bixop |       2 |
|   1 | b4  |    1.234 | zxy   |       3 |
```


```NONE
# add-sequence: step by 2:
$ psv in a.tsv // seq --step=2 // md
|   a | b   |        c | d     |   __i__ |
|----:|:----|---------:|:------|--------:|
|   1 | b1  |   23.763 | xspdf |       1 |
|   2 | b2  |  -98.73  | qwer  |       3 |
|   3 | b3  | 3451     | bixop |       5 |
|   1 | b4  |    1.234 | zxy   |       7 |
```


```NONE
# add-sequence: start at 5, step by -2:
$ psv in a.tsv // seq --start=5 --step=-2 // md
|   a | b   |        c | d     |   __i__ |
|----:|:----|---------:|:------|--------:|
|   1 | b1  |   23.763 | xspdf |       5 |
|   2 | b2  |  -98.73  | qwer  |       3 |
|   3 | b3  | 3451     | bixop |       1 |
|   1 | b4  |    1.234 | zxy   |      -1 |
```


```NONE
# add-sequence: generate UUIDs:
$ psv in a.tsv // seq --uuid // md
|   a | b   |        c | d     | __i__                                |
|----:|:----|---------:|:------|:-------------------------------------|
|   1 | b1  |   23.763 | xspdf | 6c6b3d60-ab24-4baf-9073-f8bbb5ac1b79 |
|   2 | b2  |  -98.73  | qwer  | 13945e3a-7d6c-4dea-b429-e80874b3baf2 |
|   3 | b3  | 3451     | bixop | 1f1ca8fa-5841-4070-bcdf-034e616e84d8 |
|   1 | b4  |    1.234 | zxy   | 34cff4d1-20bc-4443-8f22-eddfcfa959b9 |
```



----------------------------------------------------------

## `rename-columns`

`rename-columns` - Rename columns.

```NONE
psv rename-columns [OLD-COL:NEW-NAME ...]
```


Aliases: `rename`

Arguments:

|                         |                    |
| ----------------------- | ------------------ |
|  `OLD-COL:NEW-NAME ...` | Columns to rename. |

Examples:

```NONE
# rename-columns: rename column 'b' to 'Name':
$ psv in a.tsv // rename b:Name // md
|   a | Name   |        c | d     |
|----:|:-------|---------:|:------|
|   1 | b1     |   23.763 | xspdf |
|   2 | b2     |  -98.73  | qwer  |
|   3 | b3     | 3451     | bixop |
|   1 | b4     |    1.234 | zxy   |
```



----------------------------------------------------------

## `infer-objects`

`infer-objects` - Infer column types.

```NONE
psv infer-objects
```


Aliases: `infer`

----------------------------------------------------------

## `show-columns`

`show-columns` - Table of column names and attributes.

```NONE
psv show-columns
```


Aliases: `columns`, `cols`

See numpy.dtype.

Examples:

```NONE
# Column metadata columns:
$ psv in a.tsv // cols // cols // cut name,dtype.name // md
| name            | dtype.name   |
|:----------------|:-------------|
| name            | object       |
| dtype.name      | object       |
| dtype.kind      | object       |
| dtype.char      | object       |
| dtype.num       | int64        |
| dtype.str       | object       |
| dtype.itemsize  | int64        |
| dtype.byteorder | object       |
| dtype.subdtype  | object       |
| dtype.shape     | object       |
| dtype.hasobject | bool         |
| dtype.flags     | int64        |
| dtype.isbuiltin | int64        |
| dtype.isnative  | int64        |
| dtype.descr     | object       |
| dtype.alignment | int64        |
| dtype.base      | object       |
| dtype.metadata  | object       |
```


```NONE
# Column metadata:
$ psv in a.tsv // cols // cut name,dtype.name,dtype.kind,dtype.isnative // md
| name   | dtype.name   | dtype.kind   |   dtype.isnative |
|:-------|:-------------|:-------------|-----------------:|
| a      | int64        | i            |                1 |
| b      | object       | O            |                1 |
| c      | float64      | f            |                1 |
| d      | object       | O            |                1 |
```



----------------------------------------------------------

## `env-`

`env-` - Show env.

```NONE
psv env-
```


Examples:

```NONE
# env: display proccessing info:
$ psv in a.tsv // show-columns // md // env-
{
  "now": "2024-03-15 01:57:38.891398+0000",
  "history": [
    [
      "<< IoIn: in a.tsv >>",
      "<< DataFrame: (4, 4) >>",
      "application/x-pandas-dataframe",
      null
    ],
    [
      "<< ShowColumns: show-columns >>",
      "<< DataFrame: (4, 18) >>",
      "application/x-pandas-dataframe",
      null
    ],
    [
      "<< MarkdownOut: markdown-out >>",
      "<< str: | name   | dtype.name   | dtype.kind  ... >>",
      null,
      null
    ],
    [
      "<< EnvOut: env- >>",
      null,
      null,
      null
    ]
  ],
  "xform": {
    "first": [
      "in",
      "a.tsv"
    ],
    "last": [
      null
    ],
    "prev": [
      null
    ],
    "next": [
      "show-columns"
    ],
    "current": [
      "<< EnvOut: env- >>",
      null,
      null,
      null
    ]
  },
  "Content-Type": "application/x-psv-env",
  "Content-Encoding": null,
  "input.paths": [
    "a.tsv"
  ]
}
```



----------------------------------------------------------

# Expression Evaluation

## `eval`

`eval` - Evaluate expression for each row.

```NONE
psv eval [--columns=COL,...] [--normalize] [STATEMENT ...]
```


Aliases: `each`

Variable Bindings:
Columns are bound to variables:
  * `inp`    : input table.
  * `out`    : output table.
  * `row`    : current row.
  * `ind`    : row index.
  * `offset` : row offset (zero origin).

When expression returns:
  * "FINISH" : all remaining rows are dropped.
  * "BREAK"  : all remaining rows (inclusive) are dropped.
  * False    : the row is removed.
  * Dict     : the row is updated and new columns are added.

Arguments:

|                  |             |
| ---------------- | ----------- |
|  `STATEMENT ...` | Statements. |

Options:

|                      |                                                                            |
| -------------------- | -------------------------------------------------------------------------- |
|  `--columns=COL,...` | Columns bound within STATEMENT.                                            |
|  `--normalize`, `-n` | Column bound within STATEMENT are normalized to r&#x27;^[a-z0-9_]+$&#x27;. |

Examples:

```NONE
$ psv in a.tsv // eval "c *= 2"
   a   b       c      d
0  1  b1  47.526  xspdf
1  2  b2 -197.46   qwer
2  3  b3  6902.0  bixop
3  1  b4   2.468    zxy
```


```NONE
$ psv in a.tsv // eval "return c > 0"
   a   b       c      d
0  1  b1  23.763  xspdf
1  3  b3  3451.0  bixop
2  1  b4   1.234    zxy
```


```NONE
$ psv in a.tsv // eval "return {'i': offset, 'd_length': 2}"
   a   b         c      d  i  d_length
0  1  b1    23.763  xspdf  0         2
1  2  b2   -98.730   qwer  1         2
2  3  b3  3451.000  bixop  2         2
3  1  b4     1.234    zxy  3         2
```


```NONE
$ psv in a.tsv // eval "return {'c': c * 2, 'f': len(d)}"
   a   b         c      d  f
0  1  b1    47.526  xspdf  5
1  2  b2  -197.460   qwer  4
2  3  b3  6902.000  bixop  5
3  1  b4     2.468    zxy  3
```


```NONE
$ psv in a.tsv // rename d:dCamelCase // eval +n 'dCamelCase *= 2'
   a   b       c  dCamelCase
0  1  b1  23.763  xspdfxspdf
1  2  b2  -98.73    qwerqwer
2  3  b3  3451.0  bixopbixop
3  1  b4   1.234      zxyzxy
```


```NONE
$ psv in a.tsv // rename d:dCamelCase // eval -n 'd_camel_case *= 2'
   a   b       c  dCamelCase
0  1  b1  23.763  xspdfxspdf
1  2  b2  -98.73    qwerqwer
2  3  b3  3451.0  bixopbixop
3  1  b4   1.234      zxyzxy
```



----------------------------------------------------------

## `select`

`select` - Select rows.

```NONE
psv select [LOGICAL-EXPRESSION ...]
```


Aliases: `where`

When expression is True, the row is selected.
"BREAK" and "FINISH" conditions in `eval` command also apply.

Arguments:

|                           |                     |
| ------------------------- | ------------------- |
|  `LOGICAL-EXPRESSION ...` | Logical expression. |

Examples:

```NONE
$ psv in a.tsv // select "c > 0"
   a   b       c      d
0  1  b1  23.763  xspdf
1  3  b3  3451.0  bixop
2  1  b4   1.234    zxy
```



----------------------------------------------------------

## `repl`

`repl` - Start an interactive REPL.

```NONE
psv repl [`inp`] [`out`]
```


Arguments:

|          |                              |
| -------- | ---------------------------- |
|  ``inp`` | Input table.                 |
|  ``out`` | Output table; copy of `inp`. |

----------------------------------------------------------

# Documentation

## `example`

`example` - Show examples.

```NONE
psv example [--run] [--generate] SEARCH-STRING
```


Aliases: `ex`, `examples`

Arguments:

|                  |                               |
| ---------------- | ----------------------------- |
|  `SEARCH-STRING` | Matches name, aliases, brief. |

Options:

|                |                             |
| -------------- | --------------------------- |
|  `--run`, `-r` | Run examples.               |
|  `--generate`  | Generate and save examples. |

----------------------------------------------------------

## `help`

`help` - This help document.

```NONE
psv help [--verbose] [--list] [--plain] [--raw] [--sections] [--markdown]
```


Options:

|                     |                   |
| ------------------- | ----------------- |
|  `--verbose`, `-v`  | Show more detail. |
|  `--list`, `-l`     | List commands.    |
|  `--plain`, `-p`    | Show plain docs.  |
|  `--raw`, `-r`      | Raw detail.       |
|  `--sections`, `-s` | List sections.    |
|  `--markdown`       | Emit Markdown.    |

----------------------------------------------------------


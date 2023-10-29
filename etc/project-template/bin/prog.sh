#!/usr/bin/env bash
prog_name="$(basename "$0")"
prog_base="$(readlink -f "$(dirname "$0")/..")"
PATH="$PATH:$prog_base/bin"
[[ -f "$prog_base/venv/bin/activate" ]] && . "$prog_base/venv/bin/activate"

cmd-help() {
  cat <<EOF
# Description

???

See: \`bin/$prog_name help\`

# Directories

* ?

# Usage

~~~
bin/$prog_name [COMMAND] ...
~~~

# Commands

|                     |                                             |
| ------------------- | ------------------------------------------- |
| \`COMMAND-1-???\`   | ???
| \`COMMAND-2-???\`   | ???

# Examples

~~~
export FOO=foobar
bin/$prog_name COMMAND-1
~~~

# Env Vars

* \`ENVVAR-1\` - ???

EOF
  # Render: bin/$progname help | markdown_py -x tables -x toc -x fenced_code
  exit 0
}

# This doesnt work:

cmd-COMMAND-1() {
  run "$0.py" COMMAND-1 "$@"
}

###########################

main() {
  now="$(date '+%Y%m%d-%H%M%S')"
  today="$(date '+%Y-%m-%d')"
  [[ -z "$*" ]] && cmd-help
  -argv-parse-commands run-cmd "$@"
}

run-cmd() {
  local cmd="$1"; shift
  "cmd-$cmd" "$@" || exit $?
}

###########################

http-PUT() {
  local file="$1" url_base="$2"
  url="$url_base/$(basename "$file")"
  run curl -sLk --fail -X PUT --data-binary "@$file" "$url" || return $?
}

run() {
  echo "run : $*" >&2
  "$@"
}

. "$prog_base/lib/bash/argv.sh"

###########################

main "$@"

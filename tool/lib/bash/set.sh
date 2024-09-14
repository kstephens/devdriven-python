#!/bin/bash

# Old Bash doesn't have assocs.
# declare -A cmd_ran=()
set_files=()
trap 'rm -f "${set_files[@]}"' EXIT

set-create() {
  local var="$1" name="${2:-$1}"
  local set_file="$(mktemp -t "ran-$$.XXXXXX")"
  set_files+=("$set_file")
  echo -n '' > "$set_file"
  printf -v "$var" '%s' "$set_file"
}
set-contains() {
  # log INFO "set-contains $1 '$2'"
  grep --color=never -qxF -m 1 "$2" "$1"
}
set-append() {
  echo "$2" >> "$1"
  sort -u -o "$1" "$1"
  # log INFO "set-append $1 '$2'"
}

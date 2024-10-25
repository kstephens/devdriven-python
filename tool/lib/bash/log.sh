#!/bin/bash

# Assoc arrays are not avail in old Bash versions.
log__FATAL__priority=10
log__FATAL__color="1;31"
log__ERROR__priority=20
log__ERROR__color="31"
log__WARN__priority=30
log__WARN__color="33"
log__INFO__priority=40
log__INFO__color="34"
log__DEBUG__priority=80
log__DEBUG__color="36"
log__TRACE__priority=90
log__TRACE__color="2;37"

log_file=/dev/stderr
log_indent=
log_tz=UTC
log-setup-timestamp() {
  log_date="$(which $* true | head -1)"
  for log_date_opts in -Ins -Iseconds ''
  do
    $log_date $log_date_opts >/dev/null 2>&1 && break
  done
}
log-setup-timestamp /opt/homebrew/Cellar/coreutils/*/libexec/gnubin/date date

log-level() {
  log_level="$1"
  local level_var="log__${log_level}__priority"
  log_level_num="${!level_var:-$log_level}"
}
log-level INFO
log() {
  (
    set +x
    log- "$@"
  )
}
log-() {
  local level="$1"; shift
  local level_num
  # declare -p level log_level level_num log_level_num >&2
  if log-is-enabled "$level"
  then
    local log_timestamp="$(TZ=$log_tz $log_date $log_date_opts 2>/dev/null)"
    local color_code="log__${level}__color"; color_code="${!color_code:-1}"
    printf $'\e[%sm  ### %s : %-6s %s: %s%s\e[0m\n' "$color_code" "$log_timestamp" "$level" "$log_indent" "$*" >> "$log_file"
  fi
}

log-is-enabled() { # level
  local level="$1"
  local level_var="log__${level}__priority"
  level_num="${!level_var:-$level}"
  # declare -p level log_level level_num log_level_num
  (( level_num <= log_level_num ))
}

log-test-example() {
  (
    for log_level in 0 10 50 100
    do
      log-level "$log_level"
      for level in FATAL ERROR WARN INFO DEBUG TRACE 99
      do
        log $level "at log_level=$log_level log_level_num=$log_level_num"
      done
    done
  )
}
# log-test-example; exit

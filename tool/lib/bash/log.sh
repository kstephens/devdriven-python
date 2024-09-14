#!/bin/bash

log__FATAL__priority=10
log__FATAL__color="1;31"
log__ERROR__priority=20
log__ERROR__color="31"
log__WARN__priority=30
log__WARN__color="1;33"
log__INFO__priority=40
log__INFO__color="34"
log__DEBUG__priority=80
log__DEBUG__color="2;36"
log__TRACE__priority=90
log__TRACE__color="2;37"

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
  if log-enabled "$level"
  then
    local color_code_var="log__${level}__color"
    local color_code="${!color_code_var:-1}"
    printf $'\e[%sm  ### %05d : %-6s : %s%s\e[0m\n' "$color_code" "$SECONDS" "$level" "$*" >&2
  fi
}

log-enabled() { # level
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
      for level in FATAL ERROR WARN INFO DEBUG TRACE 99
      do
        declare -p log_level level
        log $level "at log_level=$log_level log_level_num=$log_level_num"
      done
    done
  )
}
# log-test-example; exit

#!/usr/bin/env bash

declare -g  argv_argv0='' argv_args=()
declare -gA argv_set=() argv_options=() argv_flags=()

-argv-parse() {
  argv_argv0='' argv_args=() argv_set=() argv_options=() argv_flags=()
  local arg
  while [[ $# -gt 0 ]]
  do
    arg="$1"; shift
    if [[ "$arg" == '--' ]]
    then
      argv_args+=("$@")
      break
    else
      -argv-parse-arg "$arg"
    fi
  done
}

-argv-parse-arg() {
  local arg="$1"
  local is_flag is_opt key val
  # echo '  ### -argv-parse-arg vvvvvvvvvvvvvvvvvvvvvvvv'
  # declare -p arg
  case "$arg"
  in
    --*=*) is_opt=1
      val="${arg#--*=}"
      key="${arg#--}"; key="${key%%=*}"
      ;;
    --*) is_opt=1 is_flag=1
      val=1 key="${arg#--}"
      ;;
    ++*) is_opt=1 is_flag=1
      val='' key="${arg#++}"
      ;;
    --no-*) is_opt=1 is_flag=1
      val='' key="${arg#--no-}"
      ;;
    *)
      if [[ -z "$argv_argv0" ]]
      then
        argv_argv0="$arg"
      else
        argv_args+=("$arg")
      fi
      ;;
  esac
  if [[ -n "$is_opt" ]]
  then
    key="${key//-/_}"
    argv_set["$key"]=1
    argv_options["$key"]="$val"
    [[ -n "$is_flag" ]] && argv_flags["$key"]="$val"
  fi
  # declare -p is_opt is_flag key val
  # echo '  ### -argv-parse-arg ^^^^^^^^^^^^^^^^^^^^^^^^'
}

-argv-parse-commands() {
  local f="$1" f_argv=() arg; shift
  for arg in "$@"
  do
    case "$arg"
    in
      ,)    -argv-invoke-command "$f" "${f_argv[@]}" ; f_argv=() ;;
      ,*)   -argv-invoke-command "$f" "${f_argv[@]}" ; f_argv=()
            arg="${arg#,}" ; f_argv+=("$arg") ;;
      *,)   f_argv+=("${arg%,}")
            -argv-invoke-command "$f" "${f_argv[@]}" ; f_argv=() ;;
      *)    f_argv+=("$arg") ;;
    esac
  done
  -argv-invoke-command "$f" "${f_argv[@]}"
}

-argv-invoke-command() {
  local f="$1"; shift
  if [[ $# -gt 0 ]]
  then
    -argv-parse "$@"
    "$f" "$argv_argv0" "${argv_args[@]}"
  fi
}

#############################

-argv-test-show-cmd() {
  local argv=("$@")
  echo "  ### -argv-test-show-cmd ##############################"
  declare -p argv argv_argv0 argv_args argv_options argv_flags argv_set
}

-argv-test-parse() {
  # set -x
  -argv-parse-commands -argv-test-show-cmd "$@"
}

#############################

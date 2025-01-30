# sudo apt-get install inotify-tools
# brew install fswatch

shopt -s globstar
pwd="$(realpath "$PWD")"

prepare-watch-cmd() {
  inotifywait="$(which inotifywait 2>/dev/null | head -1)"
  fswatch="$(which fswatch 2>/dev/null| head -1)"

  if [[ -x "$inotifywait" ]]
  then
    local files_opt=($(ls -d ${files[*]} 2>/dev/null))
    local events_opt=' CREATE MODIFY ATTRIB MOVE DELETE'
    local excludes_opt=" ${excludes[*]}"
    read_vars='dir events file'
    watch_cmd=(
      $inotifywait
      --quiet
      --monitor
      ${events_opt// / --event }
      ${excludes_opt// / --exclude }
      --recursive "${files_opt[@]}"
    )
  elif [[ -x "$fswatch" ]]
  then
    local files_opt=($(ls -d ${files[*]} 2>/dev/null))
    local events_opt='Created Updated Removed'
    local excludes_opt="${excludes[*]}"
    excludes_opt="${excludes_opt//./\\.}"
    # local includes_opt="$(ls -d "${files[@]}" 2>/dev/null)"
    # includes_opt="${includes_opt//./\\.}"
    read_vars='file'
    watch_cmd=(
      $fswatch
      # --quiet
      --extended
      ${events_opt// / --event=}
      --exclude=${excludes_opt// /|}
      # --include=${includes_opt// /|}
      "${files_opt[@]}"
    )
  else
    echo "cannot find inotifywait or fswatch"
    exit 99
  fi
}

watch-files-main() {
  dir='' file='' events='' file_last=''
  prepare-watch-cmd
  echo "${watch_cmd[*]@Q}"
  "${watch_cmd[@]}" |
  while read -r ${read_vars:?}
  do
    file="$dir$file"
    file="${file#$pwd/}"
    rtn=0 fail=0
    # [[ "$file" == "$file_last" ]] && continue
    if [[ $verbose ]]
    then
      declare -p $read_vars
    fi
    # echo "  ### ####################################################"
    # echo "  ### {{{ $file ..."
    file-changed "$file"
    # echo "  ### }}} $file $fail"
    # echo "  ### ####################################################"
    dir='' file='' events=''
  done
}

cmd() {
  [[ $fail != 0 ]] && return $fail
  echo "  ### .... . $*"
  "$@"; local rtn=$?
  if [[ $rtn == 0 ]]
  then
    echo "  ### OK   $*"
  else
    fail=$rtn
    echo "  ### FAIL $*"
  fi
  return $rtn
}

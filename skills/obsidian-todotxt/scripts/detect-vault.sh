#!/usr/bin/env bash
# Walks up from $PWD looking for .obsidian/ directories.
# Outputs COUNT=N on the first line, then one absolute vault path per line.
_dir="$PWD"; _out=""; _n=0
while [ "$_dir" != "/" ]; do
  if [ -d "$_dir/.obsidian" ]; then
    _out="${_out}${_dir}
"; _n=$((_n+1))
  fi
  _dir="$(dirname "$_dir")"
done
echo "COUNT=$_n"
printf '%s' "$_out"

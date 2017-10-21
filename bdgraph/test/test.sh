#!/bin/bash

main() {
  # none -> int

  temp="$(mktemp -d)"
  failures=0
  passes=0

  for file in *.bdot; do

    python3 ../bdgraph.py "$file" "$temp/$file.test"

    if [[ ! -z "$(diff "output/$file.dot" "$temp/$file.test")" ]]; then
      echo "Regression in $file"
      diff "output/$file.dot" "$temp/$file.test"
      echo
      let failures++

    else
      let passes++
    fi
  done

  rm -rf "$temp"

  echo "Finished with $passes tests passed, $failures failures"
  return $failures
}

exit main "$@"

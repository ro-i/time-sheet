#!/bin/bash
set -e

config_file="$1"
sample_file="$2"

# create temporary directory
tmpdir=$(mktemp -d)
old_pwd="$PWD"

# jump into the temporary directory
cd "$tmpdir"

# resulting dumps will be named 'avg_time_[...]' and 'over_quota[...]'
python3 "${old_pwd}/timesheet/timesheet.py" dump "${old_pwd}/$config_file" \
	"${old_pwd}/$sample_file"

# resulting dumps will be named 'val_avg_time_[...]' and 'val_over_quota[...]'
gawk -f "${old_pwd}/tests/validate.awk" "${old_pwd}/$sample_file"

if ! diff --color=auto -d avg_time* val_avg_time*; then
	printf '%s\n' "avg_time test failed"
	fail=1
fi

if ! diff --color=auto  -d over_quota* val_over_quota*; then
	printf '%s\n' "over_quota test failed"
	fail=1
fi

if [[ ! $fail ]]; then
	printf '%s\n' "Test passed."
fi

# jump back to old working directory
cd "$old_pwd"

# delete temporary directory
rm -r "$tmpdir"

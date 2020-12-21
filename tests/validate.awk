#!/usr/bin/gawk -f

# See LICENSE file for copyright and license details.
# time-sheet - https://github.com/ro-i/time-sheet

function iso_to_timestamp(date) {
	if (!date)
		return 0
	date_cmd = "date --date=\"" date "\" '+%s' 2> /dev/null"
	date_cmd | getline timestamp
	close(date_cmd)
	return timestamp
}

# extract the value of a config line of the form 'key = value'
function get_config_value(line) {
	match(line, "^.*=\\s*(.*)", matched)
	# return empty if no match
	return matched[1]
}

function get_tmpfile(pattern) {
	tmpfile_cmd = "mktemp " pattern
	tmpfile_cmd | getline tmpfile
	close(tmpfile_cmd)
	return tmpfile
}


BEGIN {
	ok = 1

	if (ARGC != 3) {
		print "usage: [gawk -f] validate.awk CONFIG_FILE CSV_FILE"
		ok = 0; exit
	}

	# create temporary files
	avg_time_dump = get_tmpfile("val_avg_time_XXXXXXXXXX.dump")
	over_quota_dump = get_tmpfile("val_over_quota_XXXXXXXXXX.dump")

	# we parse csv, so split each line by comma (simplified :-) )
	FS = ","
}


ENDFILE {
	if (!contract || !start_date || !end_date || !quota) {
		print "config file seems wrong"
		ok = 0; exit
	}
}


# process config file (= first file)
NR == FNR {
	# detect start of contract section
	if ($0 ~ /^\[Contract\]$/) {
		contract = 1
		next
	}
	# discard previous sections
	if (!contract)
		next
	# detect end of contract section
	if (contract && ($0 ~ /^\s*$/ || $0 ~ /^\[/)) {
		# contract section ended
		nextfile
	}

	# parse contract section

	if ($0 ~ /^start\s*=/) {
		start_date = iso_to_timestamp(get_config_value($0))
		next
	}
	if ($0 ~ /^end\s*=/) {
		end_date = iso_to_timestamp(get_config_value($0))
		next
	}
	if ($0 ~ /^quota\s*=/) {
		quota = get_config_value($0)
		next
	}
}

# process csv file
{
	# check if entry is included in contract, i.e. timestamp is in the
	# range [start_date;end_date]
	if ($2 < start_date || $2 > end_date)
		next

	# sum working times for each week
	avg_time[strftime("%G/%V", $2)] += $4

	# sum working times for each person id
	over_quota[$3] += $4
}


END {
	# check if an error occurred
	if (!ok)
		exit 1

	# get number of unique person ids
	id_num = length(over_quota)
	if (!id_num) {
		print "error: no unique person ids"
		exit 1
	}

	# get the average working times
	for (i in avg_time)
		avg_time[i] /= id_num

	# traverse avg_time by week indices in ascending order
	PROCINFO["sorted_in"] = "@ind_str_asc"

	# dump avg_time to csv
	for (week in avg_time)
		printf "%s,%.1f\n", week, avg_time[week] > avg_time_dump
	close(avg_time_dump)

	# traverse over_quota by quota value in descending order
	PROCINFO["sorted_in"] = "@val_num_desc"

	# dump over_quota to csv
	for (id in over_quota) {
		# stop if working times get smaller than quota
		if (over_quota[id] <= quota)
			break
		printf "%s,%.1f,%.1f,%.1f\n", id, over_quota[id], quota, \
		       over_quota[id] - quota > over_quota_dump
	}
	close(over_quota_dump)
}

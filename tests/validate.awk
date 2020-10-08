#!/usr/bin/gawk -f

# See LICENSE file for copyright and license details.
# time-sheet - https://github.com/ro-i/time-sheet

function get_week_id_from_timestamp(timestamp) {
	date_cmd = "date --date=@" timestamp " '+%Y/%V'"
	# builtin strftime seems to have a bug? (TODO)
	date_cmd | getline week_id
	close(date_cmd)
}

function iso_to_timestamp(date) {
	date_cmd = "date --date='2020-09-01 00:00:00' '+%s'"
	date_cmd | getline timestamp
	close(date_cmd)
	return timestamp
}


BEGIN {
	ok = 1
	csv_header = ",Datum,Anmeldename,Dauer"
	avg_time_header = "Datum,avg_time"
	over_quota_header = "Anmeldename,Ist,Soll,Differenz"
	quota = 126

	start_date = iso_to_timestamp("2020-09-01 00:00:00")
	end_date = iso_to_timestamp("2021-01-31 23:59:59")

	# create temporary files
	"mktemp val_avg_time_XXXXXXXXXX.dump" | getline avg_time_dump
	"mktemp val_over_quota_XXXXXXXXXX.dump" | getline over_quota_dump

	# we parse csv, so split each line by comma (simplified :-) )
	FS = ","
}


# check csv header (= first line) and skip it afterwards
NR == 1 { 
	if ($0 == csv_header)
		next
	print "error: input csv file seems to be wrong"
	ok = 0
	exit
}

{
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
	print "Datum,avg_time" > avg_time_dump
	for (week in avg_time)
		printf "%s,%.1f\n", week, avg_time[week] > avg_time_dump
	close(avg_time_dump)

	# traverse over_quota by quota value in descending order
	PROCINFO["sorted_in"] = "@val_num_desc"

	# dump over_quota to csv
	print "Anmeldename,Ist,Soll,Differenz" > over_quota_dump
	for (id in over_quota) {
		# stop if working times get smaller than quota
		if (over_quota[id] <= quota)
			break
		printf "%s,%.1f,%.1f,%.1f\n", id, over_quota[id], quota, \
		       over_quota[id] - quota > over_quota_dump
	}
	close(over_quota_dump)
}

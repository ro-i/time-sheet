timesheet
=========

A script to generate statistics from the working hours of teaching assistants
at the Technical University of Munich.

The data is collected by the database activity in
[Moodle](https://www.moodle.tum.de/) and exported to a
[csv file](https://en.wikipedia.org/wiki/Comma-separated_values).

Most teaching assistants have to document their working times, i.e. (among
other things) the correponding date (e.g. 2020-09-28) and working time
(e.g. 2.5 hours).
Assuming a csv file containing this data, where the following columns are the
most relevant ones:
- `Datum`: the date of the working slot
- `Dauer`: the working time
- `Anmeldename`: the tum id of the corresponding teaching assistant
                 (collected by Moodle, thus failsafe)

The presence of those columns is required for this script to work. The column
names will get configurable in the future.

**Note: This script is currently under construction!**

usage
-----

Run `timesheet/timesheet.py infile.csv outfile.pdf` where
- `timesheet/timesheet.py` is the script (run `make` or `make install` if you
  want to install the script, so that you only have to use `timesheet`).
- `infile.csv` is the file with the data to parse.
- `outfile.pdf` is the output pdf to be generated.

You may perform a sample run:
1) `make install`
2) `make samplefile`
3) `timesheet samplefile.csv test.pdf`

test
----

Run `make test` to run the unit tests (only a dummy available at the moment).

In order to test the regular execution of the script, you may want to generate
a sample csv file by running `make samplefile` which will provide a file called
`samplefile.csv`.

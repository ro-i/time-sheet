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
- `DateCol` (e.g. 'Datum'): the date of the working slot
- `DurationCol` (e.g. 'Dauer'): the working time
- `IdCol` (e.g. 'Anmeldename'): the personal id (e.g. tum id, full name or
   email address) of the corresponding person (collected by Moodle, thus
   failsafe)

The presence of those columns is required for this script to work. The column
names are configurable, so it does not matter how they are actually named
(cf. example configuration file `timesheet.conf`).

**Note: This script is currently under construction!**


usage
-----

Run `timesheet/timesheet.py timesheet timesheet.conf infile.csv outfile.pdf`,
where
- `timesheet/timesheet.py` is the script (run `make` or `make install` if you
  want to install the script, so that you only have to use `timesheet`).
- `timesheet.con` is the configuration file.
- `infile.csv` is the file with the data to parse.
- `outfile.pdf` is the output pdf to be generated.

You may perform a sample run:
1) `make install`
2) `make samplefile`
3) `timesheet samplefile.csv test.pdf`


test
----

Run `make test` to run a small and (currently) very simple test.
It is no longer pased on python unit tests, but on a simple reference
implementation using GNU AWK. (Hopefully too simple to be wrong... :-) )


see also
--------
Important documentation:
- https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html
- https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html#named-aggregation


bugs/todo
---------
I am not really sure what happens if your computer uses a timezone different
from Europe/Berlin.

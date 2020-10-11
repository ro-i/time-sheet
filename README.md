timesheet
=========

Initially, this script has been written to generate statistics from the working
hours of teaching assistants at the Technical University of Munich. Meanwhile,
it may also be used for other purposes.

The data may be collected by the database activity in
[Moodle](https://www.moodle.tum.de/) and exported to a
[csv file](https://en.wikipedia.org/wiki/Comma-separated_values) (see also
[RFC 4180](https://tools.ietf.org/html/rfc4180)).

Most teaching assistants have to document their working times, i.e. (among
other things) the corresponding date (e.g. 2020-09-28) and working time
(e.g. 2.5 hours).
Assuming a csv file containing this data, where the following columns are the
most relevant ones:
- `DateCol` (e.g. 'Datum'): the date of the working slot
- `DurationCol` (e.g. 'Dauer'): the working time in hours
- `IdCol` (e.g. 'Anmeldename'): the personal id (e.g. TUM id, full name or
   email address) of the corresponding person (may be collected by Moodle to be
   failsafe)

The presence of those columns is required for this script to work. The column
names are configurable, so it does not matter how they are actually named
(cf. example configuration file `timesheet.conf`).

An example csv file may look as follows:
```
[...],Datum,[...],Dauer,[...],Anmeldename,[...]
[...],1602227585,[...],1.5,[...],ab12cde,[...]
[...],1601503200,[...],0.9,[...],ab12cde,[...]
```
The order of the columns does not matter.

**Note: This script is currently under construction!**


usage
-----

Run `timesheet/timesheet.py timesheet timesheet.conf infile.csv outfile.pdf`,
where
- `timesheet/timesheet.py` is the script (run `make` or `make install` if you
  want to install the script, so that you only have to use `timesheet`).
- `timesheet.conf` is the configuration file.
- `infile.csv` is the file with the data to parse.
- `outfile.pdf` is the output pdf to be generated.

You may perform a sample run:
1) `make samplefile`
2) `timesheet/timesheet.py timesheet timesheet.conf samplefile.csv test.pdf`

For general usage information, you may run `timesheet/timesheet.py --help`.
For the usage information on the specific commands, you may run
- `timesheet/timesheet.py timesheet --help`
- `timesheet/timesheet.py sample --help`
- `timesheet/timesheet.py dump --help`


configuration
-------------

You may configure the name of the input columns as well as the names of the
output table columns and the labels of the output bar chart.
Additionally, you can set the contract information and specify the number of
sample entries to be generated by the `sample` command.
Refer to the sample configuration file `timesheet.conf` for further details.


test
----

Run `make test` to run a small and (currently) very simple test.
It is no longer based on python unit tests, but on a simple reference
implementation using GNU AWK. (Hopefully too simple to be wrong... :-) )

The test dumps the calculated pandas.DataFrame objects to csv files (using the
`dump` command of the script, calculates the same data with AWK, and then
compares the results.

**Caution**: Because of different floating point handling, the tests may
produce false negatives. The data dumps may differ by a slightly different
sort order (e.g. sort two entries with the same floating point sort key) or a
differently rounded value (e.g. 5.0 vs 4.9).
Therefore the `diff` output is displayed.


see also
--------
Important documentation:
- https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html
- https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html#named-aggregation


bugs/todo
---------
- I am not yet sure what happens if your computer uses a timezone different from
  that used to create the csv time sheet.

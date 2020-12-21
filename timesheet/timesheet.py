#!/usr/bin/python3

# See LICENSE file for copyright and license details.
# time-sheet - https://github.com/ro-i/time-sheet

import argparse
import configparser
import datetime
import matplotlib
import numpy
import os
import pandas
import tempfile
import typing
import uuid

from matplotlib import pyplot
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from typing import Any, Dict, List, Optional, Tuple, Union


class Contract:
    '''
    This class represents a contract. A contract is defined by a start
    date, an end date and a total working quota (i.e. average time per
    week multiplied by the number of weeks).

    Arguments:
        start        start date in ISO format ('yyyy-mm-dd hh:mm:ss')
        end          end date in ISO format ('yyyy-mm-dd hh:mm:ss')
        quota        total working quota in hours (float)
    '''

    def __init__(
        self,
        start: str,
        end: str,
        quota: Union[float, str],
    ) -> None:
        check_args(locals())

        self.start: int         = int(iso_to_timestamp(start))
        self.end: int           = int(iso_to_timestamp(end))
        self.quota: float       = float(quota)

        if self.start >= self.end:
            raise ValueError('start date must be before end date')

    def is_included(self, timestamp: int) -> bool:
        '''
        Checks wether a person (defined by 'id') is beneficiary of
        this contract at the time defined by 'timestamp'.
        '''
        return self.start <= timestamp and timestamp <= self.end


class Plot:
    '''
    Plot the TimeSheet object 'timesheet' and write the result to the
    file 'file'.

    Arguments:
        avg_time_title   title of the plot of the average working hours
                         per week
        avg_time_xlabel  x axis label of the average time plot
        avg_time_ylabel  y axis label of the average time plot
        overtime_title   title of the overtimes plot
    '''

    def __init__(
        self,
        timesheet: 'TimeSheet',
        file: str,
        avg_time_title: str,
        avg_time_xlabel: str,
        avg_time_ylabel: str,
        overtime_title: str
    ) -> None:
        check_args(locals())

        self.timesheet: 'TimeSheet' = timesheet
        self.file: str              = file
        self.avg_time_title: str    = avg_time_title
        self.avg_time_xlabel: str   = avg_time_xlabel
        self.avg_time_ylabel: str   = avg_time_ylabel
        self.overtime_title: str    = overtime_title

    def plot_avg_time(self) -> Figure:
        avg_time: pandas.DataFrame = self.timesheet.calc_avg_time()

        fig, ax = pyplot.subplots()

        ax.bar(x = avg_time.index, height = avg_time['avg_time'], color = 'red')
        fig.autofmt_xdate(rotation = 90)

        ax.set_xlabel(self.avg_time_xlabel)
        ax.set_ylabel(self.avg_time_ylabel)
        ax.autoscale(tight = True)
        ax.get_xaxis().set_major_locator(pyplot.MaxNLocator(30 if avg_time.size > 30 else avg_time.size))

        fig.suptitle(self.avg_time_title)

        return fig

    def plot_over_quota(self) -> Figure:
        over_quota: pandas.DataFrame = self.timesheet.calc_over_quota()

        fig, ax = pyplot.subplots()

        table: matplotlib.table.Table
        if over_quota.empty:
            table = matplotlib.table.Table(ax, loc = 'upper center')
        else:
            # 'IdColName' is index
            table = pandas.plotting.table(ax, over_quota, loc = 'upper center')
        table.scale(1, 1.5)

        # show only the table
        ax.axis('off')
        fig.suptitle(self.overtime_title)

        return fig

    def render_pdf(self) -> None:
        # use pdf backend
        matplotlib.use('pdf', force = True)

        with matplotlib.backends.backend_pdf.PdfPages(self.file) as pdf:
            # first page
            pdf.savefig(figure = self.plot_avg_time(), bbox_inches = 'tight')
            # second page
            pdf.savefig(figure = self.plot_over_quota(), bbox_inches = 'tight')


class Sample:
    '''
    Generate a sample csv file.

    Arguments:
        contract            contract to generate sample for
        date_col_name       input date column name
        id_col_name         input id column name
        duration_col_name   input duration column name
        num                 number of random sample entries to be
                            generated
        id_num              number of unique random person ids to be
                            generated
                            (should be significantly less than 'num')
    '''

    def __init__(
        self,
        contract: Contract,
        date_col_name: str,
        id_col_name: str,
        duration_col_name: str,
        num: Union[int, str],
        id_num: Union[int, str],
    ) -> None:
        check_args(locals())

        self.contract: Contract     = contract
        self.date_col_name: str     = date_col_name
        self.id_col_name: str       = id_col_name
        self.duration_col_name: str = duration_col_name
        self.num: int               = int(num)
        self.id_num: int            = int(id_num)

        # get numpy random generator
        self.rng: numpy.random.Generator = numpy.random.default_rng()

    def generate(self) -> pandas.DataFrame:
        return pandas.DataFrame(data = {
            self.date_col_name: self.generate_dates(),
            self.id_col_name: self.generate_ids(),
            self.duration_col_name: self.generate_durations()
        })

    def generate_dates(self) -> pandas.Series:
        '''Generate 'num' random dates inside the contract time span.'''
        return pandas.Series(
            data = self.rng.choice(
                numpy.arange(self.contract.start, self.contract.end),
                size = self.num
            )
        )

    def generate_durations(self) -> pandas.Series:
        '''
        Generate durations of 'num' working slots which will likely take
        between 0 and 5 hours each.
        '''
        return pandas.Series(
            data = self.rng.choice(
                numpy.arange(0.0, 5, 0.1), size = self.num
            )
        )

    def generate_ids(self) -> pandas.Series:
        '''Generate 'num' person identifiers, 'id_num' unique ones.'''
        return pandas.Series(
            data = self.rng.choice(
                [ uuid.uuid4() for _ in range(self.id_num) ],
                size = self.num
            )
        )


class TimeSheet:
    '''
    This class represents a time sheet.
    A time sheet consists of documented working slots. The layout
    looks as follows:
        [...]|     date      |[...]|  id  |[...]|duration (hours)|[...]
             |POSIX TIMESTAMP|     |person|     |    float       |
    So at date x, person y worked z hours. This is a working slot.
    There may be multiple working slots per day per person.

    Arguments:
        df                    pandas.DataFrame holding the relevant
                              columns of the time sheet
        contract              the Contract object associated with this
                              time sheet
        date_col_name         input date column name
        id_col_name           input id column name
        duration_col_name     input duration column name
        actual_col_name       output actual working hours column name
        quota_col_name        output quota working hours column name
        overtime_col_name     output overtime column name
    '''

    def __init__(
        self,
        df: pandas.DataFrame,
        contract: Contract,
        date_col_name: str,
        id_col_name: str,
        duration_col_name: str,
        actual_col_name: str,
        quota_col_name: str,
        overtime_col_name: str
    ) -> None:
        check_args(locals())

        self.df: pandas.DataFrame    = df
        self.contract: Contract      = contract
        self.date_col_name: str      = date_col_name
        self.id_col_name: str        = id_col_name
        self.duration_col_name: str  = duration_col_name
        self.actual_col_name: str    = actual_col_name
        self.quota_col_name: str     = quota_col_name
        self.overtime_col_name: str  = overtime_col_name

    def calc_avg_time(self) -> pandas.DataFrame:
        '''Calculate average working hours per week.'''

        # count unique persons
        ta_count: int = self.df[self.id_col_name].nunique()

        avg_time: pandas.DataFrame = self.df.groupby(
            # group by week
            by = self.df[self.date_col_name].apply(
                get_week_id_from_timestamp
            )
        ).agg(
            # average working time per week per person
            avg_time = pandas.NamedAgg(
                column = self.duration_col_name,
                aggfunc = lambda x: x.sum()/ta_count
            )
        ).round(1)

        return avg_time

    def calc_over_quota(self) -> pandas.DataFrame:
        '''Calculate overtimes.'''

        over_quota: pandas.DataFrame = self.df.set_index(
            self.id_col_name
        ).groupby(
            # group by person
            self.id_col_name
        ).agg(**{
            # sum up actual working hours
            self.actual_col_name: pandas.NamedAgg(
                column = self.duration_col_name, aggfunc = sum
            ),
            # sum up working quota
            self.quota_col_name: pandas.NamedAgg(
                column = self.date_col_name,
                # index: IdColName, values: DateColName
                aggfunc = self.get_working_quota_from_series
            )
        }).query(
            '{} > {}'.format(self.actual_col_name, self.quota_col_name)
        ).astype(
            # ensure .0 as output formatting for better testing
            { self.quota_col_name: 'float' }
        )

        # get difference
        over_quota[self.overtime_col_name] = over_quota[
            self.actual_col_name
        ].sub(
            over_quota[self.quota_col_name]
        )

        # build final dataframe
        over_quota = over_quota[[
            self.actual_col_name,
            self.quota_col_name,
            self.overtime_col_name
        ]].round(
            1
        ).sort_values(
            by = [self.overtime_col_name], ascending = [False]
        )

        return over_quota

    def get_contract(self, timestamp: int) -> Optional[Contract]:
        '''
        Return the contract the given person is included in at the given
        timestamp.
        '''
        if self.contract.is_included(timestamp):
            return self.contract
        else:
            return None

    def get_working_quota_from_series(self, s: pandas.Series) -> float:
        '''
        Get a pandas.Series with 'IdColName' as index and 'DateColName'
        as values. Sum up the working quota.
        '''
        # one might make IdColName a column in order to be able to access it
        return s.apply(
            # iterate over all timestamps
            lambda ts: self.get_contract(ts)
            # now, we have a pandas.Series of Optional[Contract] objects
        ).dropna().drop_duplicates().apply(
            # map Contract to quota
            lambda contract: contract.quota
        ).sum()

    @classmethod
    def from_file(
        cls,
        file: str,
        contract: Contract,
        date_col_name: str,
        id_col_name: str,
        duration_col_name: str,
        actual_col_name: str,
        quota_col_name: str,
        overtime_col_name: str
    ) -> 'TimeSheet':
        '''
        Read file 'file' into a pandas DataFrame using the specified
        columns and create a TimeSheet instance.
        '''
        check_args(locals())

        with open(file, mode = 'r', encoding = 'utf-8') as csv:
            df: pandas.DataFrame = pandas.read_csv(
                csv,
                # element order is ignored
                usecols = (
                    date_col_name,
                    id_col_name,
                    duration_col_name
                ),
                # immediately transform POSIX timestamp to int and durations
                # to floats
                converters = {
                    date_col_name: int,
                    duration_col_name: float
                }
            )

        return cls(
            df                = df,
            contract          = contract,
            date_col_name     = date_col_name,
            id_col_name       = id_col_name,
            duration_col_name = duration_col_name,
            actual_col_name   = actual_col_name,
            quota_col_name    = quota_col_name,
            overtime_col_name = overtime_col_name
        )


def check_args(args: Dict[str, Any]) -> None:
    for key in args:
        if isinstance(args[key], pandas.DataFrame):
            if args[key] is not None and not args[key].empty:
                continue
        elif isinstance(args[key], typing.Iterable):
            if args[key] and all(args[key]):
                continue
        elif args[key]:
                continue
        raise ValueError(
            'invalid argument; {} must not be None or empty'.format(key)
        )


def dump(
    config: configparser.ConfigParser,
    infile: str
) -> None:
    contract: Contract = Contract(
        start = config['Contract']['start'],
        end   = config['Contract']['end'],
        quota = config['Contract']['quota'],
    )

    timesheet: TimeSheet = TimeSheet.from_file(
        file     = infile,
        contract = contract,
        **config['TimeSheet']
    )

    (fd, avg_time_path) = tempfile.mkstemp(
        suffix = '.dump', prefix = 'avg_time_', dir = '.'
    )
    os.close(fd)
    (fd, over_quota_path) = tempfile.mkstemp(
        suffix = '.dump', prefix = 'over_quota_', dir = '.'
    )
    os.close(fd)

    timesheet.calc_avg_time().to_csv(avg_time_path, mode = 'w')
    timesheet.calc_over_quota().to_csv(over_quota_path, mode = 'w')


def get_week_id_from_timestamp(ts: int) -> str:
    '''
    Convert a POSIX timestamp to a string representation of its
    week in the format 'yyyy/ww', e.g. '2020/42'.
    '''
    (year, week, day) = datetime.date.fromtimestamp(ts).isocalendar()
    return '{}/{:02d}'.format(year, week)


def iso_to_timestamp(date: str) -> int:
    '''
    Convert a date given in ISO format ('yyyy-mm-dd hh:mm:ss') to
    a timestamp and return it converted to an integer.
    '''
    return int(datetime.datetime.fromisoformat(date).timestamp())


def sample(
    config: configparser.ConfigParser,
    outfile: str
) -> None:
    contract: Contract = Contract(
        start = config['Contract']['start'],
        end   = config['Contract']['end'],
        quota = config['Contract']['quota'],
    )

    sample: Sample = Sample(
        contract          = contract,
        date_col_name     = config['TimeSheet']['date_col_name'],
        id_col_name       = config['TimeSheet']['id_col_name'],
        duration_col_name = config['TimeSheet']['duration_col_name'],
        **config['Sample']
    )

    sample.generate().to_csv(outfile, mode = 'w')


def timesheet(
    config: configparser.ConfigParser,
    infile: str,
    outfile: str
) -> None:
    contract: Contract = Contract(
        start = config['Contract']['start'],
        end   = config['Contract']['end'],
        quota = config['Contract']['quota'],
    )

    timesheet: TimeSheet = TimeSheet.from_file(
        file     = infile,
        contract = contract,
        **config['TimeSheet']
    )

    plot: Plot = Plot(
        timesheet = timesheet,
        file      = outfile,
        **config['Plot']
    )

    plot.render_pdf()


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description = __doc__
    )
    subparsers: Any = parser.add_subparsers(dest = 'command')

    parser_t: Any = subparsers.add_parser(
        name = 'timesheet',
        help = 'parse a time-sheet csv file, analyze and plot it.'
    )
    parser_s: Any = subparsers.add_parser(
        name = 'sample',
        help = 'generate a sample csv file.'
    )
    parser_v: Any = subparsers.add_parser(
        name = 'dump',
        help = 'dump generated pandas.DataFrames instead of plotting them'
    )

    for sub_parser in [ parser_t, parser_s, parser_v ]:
        sub_parser.add_argument(
            'configfile', metavar = 'CONFIGFILE', nargs = 1,
            help = 'configuration file'
        )
        if sub_parser not in [ parser_t, parser_v ]:
            continue
        sub_parser.add_argument(
            'infile', metavar = 'INFILE', nargs = 1,
            help = 'csv file to analyze'
        )

    parser_s.add_argument(
        'outfile', metavar = 'OUTFILE', nargs = 1, help = 'output csv filename'
    )

    parser_t.add_argument(
        'outfile', metavar = 'OUTFILE', nargs = 1, help = 'output pdf filename'
    )

    args: argparse.Namespace = parser.parse_args()

    config: configparser.ConfigParser = configparser.ConfigParser()
    if args.configfile[0] not in config.read(args.configfile[0]):
        raise SystemExit('cannot read config file')

    if args.command == 'dump':
        dump(config, args.infile[0])
    elif args.command == 'sample':
        sample(config, args.outfile[0])
    elif args.command == 'timesheet':
        timesheet(config, args.infile[0], args.outfile[0])


if __name__ == '__main__':
    main()

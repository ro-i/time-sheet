#!/usr/bin/python3

# See LICENSE file for copyright and license details.
# time-sheet - https://github.com/ro-i/time-sheet

import argparse
import matplotlib
import numpy
import pandas
import datetime
import typing
import sys

from matplotlib import pyplot
from typing import List, Optional, Tuple


# important docs:
# https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html
# https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html#named-aggregation


working_quota: List[Tuple[float, float, float]] = [
    (
        # begin
        datetime.datetime.fromisoformat("2020-09-01 00:00:00").timestamp(),
        # end
        datetime.datetime.fromisoformat("2021-01-31 23:59:59").timestamp(),
        # total quota
        10.5 * 12
    ),
    (
        # begin
        datetime.datetime.fromisoformat("2021-02-01 00:00:00").timestamp(),
        # end
        datetime.datetime.fromisoformat("2021-03-31 23:59:59").timestamp(),
        # total quota
        3.5 * 8
    )
]

# which csv columns are to be read from the given input file?
csv_columns: Tuple[str, str, str] = (
    "Datum", "Dauer", "Anmeldename"
)

# short description of this application
description: str = (
    "Parse a time-sheet csv file and plot it."
)


def get_working_quota_tuple_from_timestamp(
    ts: str
) -> Optional[Tuple[float, float, float]]:
    ts_float: float = float(ts)

    for tuple in working_quota:
        if tuple[0] <= ts_float and ts_float <= tuple[1]:
            return tuple

    return None


def get_working_quota_from_series(s: pandas.Series) -> float:
    return s.apply(get_working_quota_tuple_from_timestamp) \
            .drop_duplicates() \
            .apply(lambda y: y[2] if y is not None else 0) \
            .sum()


def get_week_id_from_timestamp(ts: str) -> str:
    (year, week, day) = datetime.date.fromtimestamp(int(ts)).isocalendar()
    return "{}/{:02d}".format(year, week)


def calc_avg_time(df: pandas.DataFrame) -> pandas.DataFrame:
    # count teaching assistants, i.e. unique TUM IDs (such as "ab12cde")
    ta_count: int = df["Anmeldename"].nunique()
    if ta_count == 0:
        sys.exit("No valid entries found.")

    avg_time: pandas.DataFrame = df.groupby(
        # group by week
        by = df["Datum"].apply(get_week_id_from_timestamp)
    ).agg(
        # average working time per week per teaching assistant
        avg_time = pandas.NamedAgg(
            column = "Dauer", aggfunc = lambda x: x.sum()/ta_count
        )
    )

    return avg_time


def plot_avg_time(df: pandas.DataFrame, ax: matplotlib.axes.Axes) -> None:
    avg_time: pandas.DataFrame = calc_avg_time(df)

    avg_time.plot(ax = ax, kind = "bar", color = "red", legend = False)
    ax.set_xlabel("Kalenderwoche/Jahr")
    ax.set_ylabel("Durchschnittliche Arbeitszeit pro Tutor")


def calc_over_quota(df: pandas.DataFrame) -> pandas.DataFrame:
    over_quota: pandas.DataFrame = df.groupby(
        # group by participant
        "Anmeldename"
    ).agg(
        # sum up actual working hours
        Ist = pandas.NamedAgg(
            column = "Dauer", aggfunc = numpy.sum
        ),
        # sum up working quota
        Soll = pandas.NamedAgg(
            column = "Datum",
            aggfunc = get_working_quota_from_series
        )
    ).query(
        "Ist > Soll"
    )

    # get difference
    over_quota["Differenz"] = over_quota["Ist"].sub(over_quota["Soll"])

    # build final dataframe
    over_quota = over_quota[["Ist", "Soll", "Differenz"]].round(1).\
            sort_values(by = ["Differenz"], ascending = [False])

    return over_quota


def plot_over_quota(df: pandas.DataFrame, ax: matplotlib.axes.Axes) -> bool:
    over_quota: pandas.DataFrame = calc_over_quota(df)
    table: matplotlib.table.Table

    if over_quota.empty:
        table = matplotlib.table.Table(ax, loc = "upper center")
    else:
        # "Anmeldename" is index
        table = pandas.plotting.table(ax, over_quota, loc = "upper center")
    table.scale(1, 1.5)
    # show only the table
    ax.axis("off")

    return not over_quota.empty


def read(infile: str) -> pandas.DataFrame:
    # read file into a pandas DataFrame
    with open(infile, mode = "r", encoding = "utf-8") as file:
        df: pandas.DataFrame = pandas.read_csv(file, usecols = csv_columns)
    return df


def render(df: pandas.DataFrame, outfile: str) -> None:
    # use pdf backend
    matplotlib.use("pdf", force = True)

    with matplotlib.backends.backend_pdf.PdfPages(outfile) as pdf:
        # first page
        fig, ax = pyplot.subplots()
        plot_avg_time(df, ax)
        fig.suptitle("Durschnittliche Arbeitszeit pro Woche pro Tutor")
        pdf.savefig(figure = fig, bbox_inches = "tight")
        # second page
        fig, ax = pyplot.subplots()
        if plot_over_quota(df, ax):
            fig.suptitle("Überstunden")
        else:
            fig.suptitle("keine Überstunden")
        pdf.savefig(figure = fig, bbox_inches = "tight")


def run(infile: str, outfile: str) -> None:
    df: pandas.DataFrame = read(infile)
    render(df, outfile)


def main() -> None:
    argument_parser = argparse.ArgumentParser(description = description)
    argument_parser.add_argument(
        'infile', metavar = 'INFILE', nargs = 1, help = "csv file to analyze"
    )
    argument_parser.add_argument(
        'outfile', metavar = 'OUTFILE', nargs = 1, help = "output pdf filename"
    )
    args: argparse.Namespace = argument_parser.parse_args()

    run(args.infile[0], args.outfile[0])


if __name__ == "__main__":
    main()

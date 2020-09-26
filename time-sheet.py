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
from typing import List, Tuple


# important docs:
# https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html
# https://pandas.pydata.org/pandas-docs/stable/user_guide/groupby.html#named-aggregation


working_quota: List[Tuple[float, float, float]] = [
    (
        # begin
        datetime.datetime.fromisoformat("2020-09-01").timestamp(),
        # end
        datetime.datetime.fromisoformat("2021-01-31").timestamp(),
        # total quota
        10.5 * 12
    ),
    (
        # begin
        datetime.datetime.fromisoformat("2021-02-01").timestamp(),
        # end
        datetime.datetime.fromisoformat("2021-03-31").timestamp(),
        # total quota
        3.5 * 8
    )
]

description: str = (
    "Parse a csv file and plot it. [TODO]"
)


def is_timestamp_in_date_range(ts: str) -> int:
    tuple = get_working_quota_tuple_from_timestamp(ts)
    return True if tuple is not None else False


def get_working_quota_tuple_from_timestamp(ts: str) -> Tuple[float, float, float]:
    for tuple in working_quota:
        if tuple[0] <= ts and ts <= tuple[1]:
            return tuple
    return None


def get_working_quota_from_timestamp(ts: str) -> float:
    tuple = get_working_quota_tuple_from_timestamp(ts)
    return tuple[2] if tuple is not None else 0


def get_working_quota_from_series(s: pandas.Series) -> float:
    return s.apply(get_working_quota_tuple_from_timestamp) \
            .drop_duplicates() \
            .apply(lambda y: y[2] if y is not None else 0) \
            .sum()


def get_week_id_from_timestamp(ts: str) -> int:
    (year, week, day) = datetime.date.fromtimestamp(int(ts)).isocalendar()
    return str(week) + "/" + str(year)


def plot_avg_time(df: pandas.DataFrame, ax: matplotlib.axes.Axes) -> None:
    # count teaching assistants, i.e. unique TUM IDs (such as "ab12cde")
    ta_count: int = df["Anmeldename"].nunique()
    if ta_count == 0:
        sys.exit("No valid entries found.")

    # use date as index
    avg_time: pandas.DataFrame = df.set_index("Datum")

    avg_time = avg_time.groupby(
        # group by week
        by = get_week_id_from_timestamp
    ).agg(
        # average working time per week per teaching assistant
        avg_time = pandas.NamedAgg(
            column = "Dauer", aggfunc = lambda x: x.sum()/ta_count
        )
    )

    # "Datum" should become a column again ( named "index")
    avg_time.reset_index(inplace = True)

    # plot
    avg_time.plot(ax = ax, kind = "bar", x = "index", y = "avg_time",
                  color = "red", legend = False)
    ax.set_xlabel("Kalenderwoche/Jahr")
    ax.set_ylabel("Durchschnittliche Arbeitszeit pro Tutor")


def plot_over_quota(df: pandas.DataFrame, ax: matplotlib.axes.Axes) -> bool:
    over_quota: pandas.DataFrame = df[["Anmeldename", "Datum", "Dauer"]].groupby(
        # group by participant
        "Anmeldename"
    ).agg(
        # sum up actual working hours
        actual_work = pandas.NamedAgg(
            column = "Dauer", aggfunc = numpy.sum
        ),
        # sum up working quota
        working_quota = pandas.NamedAgg(
            column = "Datum",
            aggfunc = get_working_quota_from_series
        )
    ).query(
        "actual_work > working_quota"
    )

    # get difference
    over_quota["diff"] = over_quota["actual_work"].sub(over_quota["working_quota"])

    if over_quota.empty:
        table: matplotlib.table.Table = matplotlib.table.Table(
            ax, loc = "upper center"
        )
    else:
        table: matplotlib.table.Table = pandas.plotting.table(
            # "Anmeldename" is index
            ax, over_quota[["actual_work", "working_quota", "diff"]],
            colLabels = ["Ist", "Soll", "Differenz"], loc = "upper center",
        )
    table.scale(1, 1.5)
    # show only the table
    ax.axis("off")

    return not over_quota.empty


argument_parser = argparse.ArgumentParser(description = description)
argument_parser.add_argument(
    'infile', metavar = 'INFILE', nargs = 1, help = "csv file to analyze"
)
argument_parser.add_argument(
    'outfile', metavar = 'OUTFILE', nargs = 1, help = "output pdf filename"
)
args: argparse.Namespace = argument_parser.parse_args()


# read file into a pandas DataFrame
with open(args.infile[0], mode = "r", encoding = "utf-8") as file:
    df: pandas.DataFrame = pandas.read_csv(file)


# use pdf backend
matplotlib.use("pdf", force = True)

with matplotlib.backends.backend_pdf.PdfPages(args.outfile[0]) as pdf:
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


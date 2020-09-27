#!/usr/bin/python3

# See LICENSE file for copyright and license details.
# time-sheet - https://github.com/ro-i/time-sheet

import argparse
import datetime
import numpy
import random
import string
import typing

from typing import List


# other columns are currently not needed
csv_header: str = "Datum,Dauer,Anmeldename\n"

# begin of date range for random date generation
dates_begin: int = int(datetime.datetime.fromisoformat("2020-09-01 00:00:00").timestamp())
# end of date range for random date generation
dates_end: int = int(datetime.datetime.fromisoformat("2021-03-31 23:59:59").timestamp())

# number of random samples to be generated
sample_num: int = 2000
# number of unique tum ids to be generated
# (should be significantly less than "sample_num")
sample_tum_id_num: int = 50


def file_build() -> str:
    dates = generate_dates()
    tum_ids = generate_tum_ids()
    working_times = generate_working_times()

    file = csv_header
    for i in range(sample_num):
        file += ','.join([dates[i], working_times[i], tum_ids[i]]) + "\n"
    return file


def file_write(file: str, content: str) -> None:
    with open(file, "x") as f:
        f.write(content)


def generate_dates() -> List[str]:
    return [
        str(date)
        for date in random.sample(range(dates_begin, dates_end), sample_num)
    ]


def generate_tum_ids() -> List[str]:
    tum_ids: List[str] = [ ''.join(
        random.sample(string.ascii_lowercase, 2)
        + random.sample(string.digits, 2)
        + random.sample(string.ascii_lowercase, 3)
    ) for i in range(sample_tum_id_num) ]

    return random.choices(tum_ids, k = sample_num)


def generate_working_times() -> List[str]:
    return [
        str(i)
        for i in random.choices(
            list(numpy.arange(0.1, 11.1, 0.1)), k = sample_num
        )
    ]


argument_parser = argparse.ArgumentParser()
argument_parser.add_argument(
    'file', metavar = 'FILE', nargs = 1,
    help = "name of csv file to be generated (file must not exist)"
)
args: argparse.Namespace = argument_parser.parse_args()


content: str = file_build()
file_write(args.file[0], content)

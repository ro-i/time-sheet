#!/usr/bin/python3

# See LICENSE file for copyright and license details.
# time-sheet - https://github.com/ro-i/time-sheet

import unittest

from timesheet import timesheet as ts
from timesheet import timesheetsample as tss


class TimeSheetTest(unittest.TestCase):
    def test_dummy(self) -> None:
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()

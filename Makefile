# See LICENSE file for copyright and license details.
# time-sheet - https://github.com/ro-i/time-sheet

# or /usr/local
prefix_dir = $(HOME)/.local

# default target
.PHONY: install
install:
	install -m 0700 -T ./timesheet/timesheet.py '$(prefix_dir)/bin/timesheet'

.PHONY: clean
clean:
	rm -f ./timesheet.py ./samplefile.csv

.PHONY: samplefile
samplefile:
	python3 ./timesheet/timesheetsample.py samplefile.csv

.PHONY: uninstall
uninstall:
	rm -f '$(prefix_dir)/bin/timesheet'

# do not throw a Makefile error on test failures
.PHONY: test
test:
	@python3 -m unittest --quiet || true

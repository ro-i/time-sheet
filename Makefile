# See LICENSE file for copyright and license details.
# time-sheet - https://github.com/ro-i/time-sheet

# or /usr/local
prefix_dir = $(HOME)/.local
config_file = timesheet.conf
sample_file = samplefile.csv

# default target
.PHONY: install
install:
	install -m 0700 -T ./timesheet/timesheet.py '$(prefix_dir)/bin/timesheet'

.PHONY: clean
clean:
	rm -f ./timesheet.py ./'$(samplefile)'

.PHONY: samplefile
samplefile:
	python3 ./timesheet/timesheet.py sample '$(config_file)' '$(sample_file)'

.PHONY: uninstall
uninstall:
	rm -f '$(prefix_dir)/bin/timesheet'

.PHONY: test
test: samplefile
	bash ./tests/test.sh '$(config_file)' '$(sample_file)'


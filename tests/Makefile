# Description: SIT - Svn with gIT extensions, test suite
# Author:      Joachim Lechner
# Licence:     GNU GENERAL PUBLIC LICENSE, Version 2, June 1991
# Source:      https://github.com/joachimlechner/sit

TARGETS_LOGS=
TARGETS_LOGS+=basic
TARGETS_LOGS+=diff
TARGETS_LOGS+=diff2
TARGETS_LOGS+=diff3
TARGETS_LOGS+=merge
TARGETS_LOGS+=merge2
TARGETS_LOGS+=stash
TARGETS_LOGS+=diff_single
TARGETS_LOGS+=diff_multi

TARGETS=
TARGETS+=$(addsuffix .python2.log, $(TARGETS_LOGS))
TARGETS+=$(addsuffix .python3.log, $(TARGETS_LOGS))

default: $(TARGETS)

CWD:=$(shell pwd)
#CWD:=$(shell pwd | xargs realpath)
CWD_REAL = ${PWD}

always:

%.python2.log: %.sh always
	echo "SIT=\"python $(CWD)/../sit.py\"" > sit_cmd.sh
	./$< | tee $@.tmp
	cat $@.tmp | sed "s,$(CWD),\.\.\.,g" | sed "s,$(CWD_REAL),\.\.\.,g" | sed "s,$(USER),<user>,g" | sed 's,[0-9]\{4\}\.[0-9]\{2\}\.[0-9]\{2\}\.[0-9]\{2\}_[0-9]\{2\}_[0-9]\{2\},<DATE_TIME>,g' | sed 's,[0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\},<TIME>,g' | sed 's,[0-9]\{2\}\.[0-9]\{2\}\.[0-9]\{4\},<DATE>,g' > $@

%.python3.log: %.sh always
	echo "SIT=\"python3 $(CWD)/../sit.py\"" > sit_cmd.sh
	./$< | tee $@.tmp
	cat $@.tmp | sed "s,$(CWD),\.\.\.,g" | sed "s,$(CWD_REAL),\.\.\.,g" | sed "s,$(USER),<user>,g" | sed 's,[0-9]\{4\}\.[0-9]\{2\}\.[0-9]\{2\}\.[0-9]\{2\}_[0-9]\{2\}_[0-9]\{2\},<DATE_TIME>,g' | sed 's,[0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\},<TIME>,g' | sed 's,[0-9]\{2\}\.[0-9]\{2\}\.[0-9]\{4\},<DATE>,g' > $@

test:
	echo $(CWD)
	echo $(CWD_REAL)
	echo $(USER)

clean:
	rm -rf $(TARGETS)

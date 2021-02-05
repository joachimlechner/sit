# Description: SIT - Svn with gIT extensions, test suite
# Author:      Joachim Lechner
# Licence:     GNU GENERAL PUBLIC LICENSE, Version 2, June 1991
# Source:      https://github.com/joachimlechner/sit

TARGETS=
TARGETS+=basic.log
TARGETS+=diff.log
TARGETS+=merge.log
TARGETS+=stash.log

default: $(TARGETS)

CWD:=$(shell pwd)

always:

%.log: %.sh always
	echo "SIT=\"python $(CWD)/../sit.py\"" > sit_cmd.sh
	./$< | tee $@.tmp
	cat $@.tmp | sed "s,$(CWD),\.\.\.,g" | sed "s,$(USER),<user>,g" | sed 's,[0-9]\{4\}\.[0-9]\{2\}\.[0-9]\{2\}\.[0-9]\{2\}_[0-9]\{2\}_[0-9]\{2\},<DATE_TIME>,g' | sed 's,[0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\},<TIME>,g' | sed 's,[0-9]\{2\}\.[0-9]\{2\}\.[0-9]\{4\},<DATE>,g' > $@

test:
	echo $(CWD)
	echo $(USER)

clean:
	rm -rf $(TARGETS)

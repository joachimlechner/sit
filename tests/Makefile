# Description: SIT - Svn with gIT extensions, test suite
# Author:      Joachim Lechner
# Licence:     GNU GENERAL PUBLIC LICENSE, Version 2, June 1991
# Source:      https://github.com/joachimlechner/sit

TARGETS=
TARGETS+=basic.log

default: $(TARGETS)

CWD:=$(shell pwd)

%.log: %.sh
	echo "SIT=\"python $(CWD)/../sit.py\"" > sit_cmd.sh
	./$< | tee $@.tmp
	cat $@.tmp | sed "s,$(CWD),\.\.\.,g" | sed "s,$(USER),<user>,g" > $@

test:
	echo $(CWD)
	echo $(USER)

clean:
	rm -rf $(TARGETS)

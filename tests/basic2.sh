#!/bin/bash

# Description: SIT - Svn with gIT extensions, test suite - basic test
# Author:      Joachim Lechner
# Licence:     GNU GENERAL PUBLIC LICENSE, Version 2, June 1991
# Source:      https://github.com/joachimlechner/sit

#set -x
set -e

source ./scripts/setup.sh
source ./scripts/helper_functions.sh
source ./sit_cmd.sh

setup_path "${PREFIX_EXAMPLE_PATH}_basic2" "Setup basic2"

source ./scripts/setup_env2.sh
./scripts/setup_server2.sh
./scripts/setup_user2.sh

cd user1/

######################
execute "$SIT status" "show status"
execute "$SIT branch" "show branches"

######################
touch t
execute "$SIT add t"
execute "$SIT commit -m \"test\""
execute "$SIT update"
execute "$SIT status"

######################
execute "$SIT branch testbranch -m \"testbranch\""
execute "$SIT branch testbranch2 -a"

execute "$SIT checkout testbranch2"

touch t2
execute "$SIT add t2"
execute "$SIT commit -m \"testbranch\""

touch t3
execute "$SIT update"
execute "$SIT add t3"
execute "$SIT stash push 'test'"
execute "$SIT status"

execute "$SIT branch"

execute "$SIT stash list"

touch t4
execute "$SIT add t4"
execute "$SIT stash push 'test2'"

#execute "$SIT stash apply 'test'"
execute "$SIT stash list"
execute "$SIT stash pop 'test'"
execute "$SIT status"

execute "svn ls ^/$PROJECT_PATH/stashes"

#execute "$SIT diff trunk -t diff -v --debug "
#execute "$SIT diff trunk -t meld -v --debug "
#execute "$SIT diff trunk -v --debug"
execute "$SIT diff trunk -t diff"
#
#execute "$SIT branch"

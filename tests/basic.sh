#!/bin/bash

# Description: SIT - Svn with gIT extensions, test suite - basic test
# Author:      Joachim Lechner
# Licence:     GNU GENERAL PUBLIC LICENSE, Version 2, June 1991
# Source:      https://github.com/joachimlechner/sit

#set -x
set -e

source ./scripts/setup.sh
source ./scripts/helper_functions.sh

setup_path "${PREFIX_EXAMPLE_PATH}_basic" "Setup basic"

./scripts/setup_server1.sh
./scripts/setup_user1.sh

cd user1/

######################
execute "sit status" "show status"
execute "sit branch" "show branches"

######################
touch t
execute "sit add t"
execute "sit commit -m \"test\""
execute "sit update"
execute "sit status"

######################
execute "sit branch testbranch -m \"testbranch\""
execute "sit branch testbranch2 -a"

execute "sit checkout testbranch2"

touch t2
execute "sit add t2"
execute "sit commit -m \"testbranch\""

touch t3
execute "sit update"
execute "sit add t3"
execute "sit stash push 'test'"
execute "sit status"

execute "sit branch"

execute "sit stash list"

touch t4
execute "sit add t4"
execute "sit stash push 'test2'"

#execute "sit stash apply 'test'"
execute "sit stash list"
execute "sit stash pop 'test'"
execute "sit status"

execute "svn ls ^/stashes"

#execute "sit diff trunk -t diff -v --debug "
#execute "sit diff trunk -t meld -v --debug "
#execute "sit diff trunk -v --debug"
execute "sit diff trunk -t diff"
#
#execute "sit branch"

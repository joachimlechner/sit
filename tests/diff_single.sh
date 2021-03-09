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

setup_path "${PREFIX_EXAMPLE_PATH}_diff_single" "Setup diff"

source ./scripts/setup_env2.sh
./scripts/setup_server2.sh
./scripts/setup_user2.sh

cd user1/

########################
echo "file" > file

########################
execute "$SIT add *"
execute "$SIT commit . -m 'test'"

echo "file_changed" > file

execute "svn status"
execute "$SIT diff file -t diff"
#execute "$SIT diff file -v -debug"


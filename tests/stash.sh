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

setup_path "${PREFIX_EXAMPLE_PATH}_stash" "Setup stash"

source ./scripts/setup_env2.sh
./scripts/setup_server2.sh
./scripts/setup_user2.sh

cd user1/

mkdir test
cd test
echo test_data1 > test_file1
echo test_data2 > test_file2
mkdir sub_test1
cd sub_test1
echo sub_test1_data1 > sub_test1_file1
cd ..
mkdir sub_test2
cd ..
echo test_data4 > test_file4

execute "$SIT add test test_file4"
execute "$SIT status" "show status"
execute "$SIT commit . -m 'test blabla'"

############
cd test/sub_test1
echo sub_test1_data2 > sub_test1_file2
execute "$SIT add sub_test1_file2"

execute "$SIT rm sub_test1_file1"

execute "$SIT remove ../test_file1"

pwd
execute "$SIT stash push test_stash -a"

execute "$SIT stash apply test_stash"

execute "sit status"

execute "svn status ../../"

execute "$SIT stash list"

execute "$SIT stash drop test_stash -a"



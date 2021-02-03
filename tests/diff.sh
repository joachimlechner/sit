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

setup_path "${PREFIX_EXAMPLE_PATH}_diff" "Setup diff"

source ./scripts/setup_env2.sh
./scripts/setup_server2.sh
./scripts/setup_user2.sh

cd user1/

mkdir test
cd test
echo test_data1 > test_file1
echo test_data2 > test_file2
mkdir sub_test
cd sub_test
echo test_data3 > test_file3
cd ..
mkdir sub_test2
cd ..
echo test_data4 > test_file4

execute "$SIT add test test_file4"
execute "$SIT status" "show status"
execute "$SIT commit . -m 'test blabla'"

execute "svn update"

cd test
execute "svn rm test_file1"
echo test_data2a > test_file2
cd sub_test

execute "$SIT status" "show status"
execute "$SIT status ." "show status"

execute "pwd"
execute "$SIT diff -t diff"
execute "$SIT diff -t diff ."


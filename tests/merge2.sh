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

setup_path "${PREFIX_EXAMPLE_PATH}_merge2" "Setup diff"

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
    echo sub_test_data1 > sub_test_file1
    cd ..
  mkdir sub_test2
  cd ..
echo test_data4 > test_file4

execute "$SIT add test test_file4"
execute "$SIT status" "show status"
execute "$SIT commit . -m 'test blabla'"

execute "$SIT update"

execute "$SIT branch test -a"

#########################
execute "$SIT checkout test"
execute "$SIT branch"

echo test_data4a > test_file4
echo test_data5 > test_file5
execute "$SIT add test_file5"
cd test
  cd sub_test2
    echo sub_test2_data1 > sub_test2_file1
    execute "$SIT add sub_test2_file1"

    execute "$SIT status"
    execute "$SIT commit -m 'test2'"

#########################
    execute "$SIT checkout trunk"

    echo sub_test2_data2 > sub_test2_file2
    execute "$SIT add sub_test2_file2"
    echo test_data4b > ../../test_file4
    execute "$SIT commit -m 'test3'"

    echo sub_test2_data2a > sub_test2_file2

    execute "$SIT status"

    execute "$SIT merge test"

    execute "$SIT merge test -f"
    execute "$SIT status"
cd ../..


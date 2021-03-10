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

setup_path "${PREFIX_EXAMPLE_PATH}_diff2" "Setup diff"

source ./scripts/setup_env2.sh
./scripts/setup_server2.sh
./scripts/setup_user2.sh

cd user1/

mkdir test
cd test
  echo test_data1 > test_file1
  echo test_data2 > test_file2
  ln -s sub_test sub_test_link
  ln -s sub_test3/sub_sub_test3 sub_sub_test_link3
  ln -s sub_test3/sub_sub_test3test_file3 sub_sub_test3_data_link
  mkdir sub_test
  cd sub_test
    echo test_data3 > test_file3
  cd ..
  mkdir sub_test2
  mkdir sub_test3
  cd sub_test3
    mkdir sub_sub_test3
    cd sub_sub_test3
      echo test_data3 > test_file3
      cd ..
    cd ..
  cd ..
echo test_data4 > test_file4

execute "$SIT add test test_file4 .sitconfig"
execute "$SIT status" "show status"
execute "$SIT commit . -m 'test blabla'"

execute "svn update"

cd test
  execute "svn rm test_file1"
  echo test_data2a > test_file2
  rm sub_test_link
  cd sub_test
    rm test_file3
    ln -s ../sub_test3/sub_sub_test3/test_file3

    execute "$SIT status" "show status"
    execute "$SIT status ." "show status"

    execute "pwd"
    execute "$SIT diff -t diff"
    execute "$SIT diff -t diff ."
  cd ..
  execute "svn status ."
  execute "$SIT diff -t diff ."
#  execute "$SIT diff -t kdiff3 ."


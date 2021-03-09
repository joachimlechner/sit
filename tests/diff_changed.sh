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
echo "file_base" > file_base
echo "file_base_changed" > file_base_changed
echo "file_base_removed" > file_base_removed
ln -sf file_base file_link_base_changed
ln -sf file_base file_link_base_removed

mkdir directory_base
mkdir directory_base_changed
mkdir directory_base_removed
ln -sf directory_base directory_link_base_changed
ln -sf directory_base directory_link_base_removed

echo "file_in_directory_base" > directory_base/file_in_directory_base
echo "file_in_directory_base_changed" > directory_base/file_in_directory_base_changed
echo "file_in_directory_base_removed" > directory_base/file_in_directory_base_removed

########################
execute "$SIT add *"
execute "$SIT commit . -m 'test'"

execute "$SIT branch test -a"

echo "file_changed" > file1
echo "file_changed2" > file2
svn rm file3


execute "$SIT checkout test"

echo "file_changed" > file1
echo "file_changed2" > file2
svn rm file3

execute "svn status"
execute "$SIT diff -v --debug"


#!/bin/bash

# Description: SIT - Svn with gIT extensions, test suite
# Author:      Joachim Lechner
# Licence:     GNU GENERAL PUBLIC LICENSE, Version 2, June 1991
# Source:      https://github.com/joachimlechner/sit

#set -x

source ./scripts/helper_functions.sh

setup_path "user1" "create local / sandbox repository for user1"

REPO_PATH=`realpath ../server1/repo`

# initialize local repository
execute "svn checkout file://$REPO_PATH/trunk ." ""



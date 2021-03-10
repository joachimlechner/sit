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

setup_path "${PREFIX_EXAMPLE_PATH}_diff3" "Setup diff"

source ./scripts/setup_env2.sh
./scripts/setup_server2.sh
./scripts/setup_user2.sh

cd user1/

########################
echo "file" > file
echo "file_to_svn_remove" > file_to_svn_remove
echo "file_to_remove" > file_to_remove
echo "file_to_modify" > file_to_modifiy
echo "file_other" > file_other

ln -s file file_link
ln -s file file_link_to_remove
ln -s file file_link_to_svn_remove
ln -s file file_link_to_modify

DIRS="dir dir_to_remove dir_to_svn_remove dir_to_modify dir_other"
for DIR in $DIRS; 
do
  mkdir empty_$DIR
  mkdir $DIR
  echo "file_in__${DIR}" > $DIR/file_in__$DIR
  echo "file_in__${DIR}__to_remove" > dir/file_in__${DIR}__to_remove
  echo "file_in__${DIR}__to_modify" > dir/file_in__${DIR}__to_modify
  ln -s dir ${DIR}_link
done

########################
execute "$SIT add * .sitconfig"
execute "$SIT commit . -m 'init'"
execute "$SIT branch test -a"
execute "$SIT checkout test"

########################
rm -rf file_to_remove
svn rm file_to_svn_remove
echo "file_to_modify => modified" > file_to_modifiy

rm -rf file_link_to_remove
svn rm file_link_to_svn_remove
ln -sf file_other file_link_to_modify

DIRS="dir_to_remove"
for DIR in $DIRS; 
do
  rm -rf empty_$DIR
  rm -rf $DIR
  rm -rf ${DIR}_link
done

DIRS="dir_to_svn_remove"
for DIR in $DIRS;
do
  svn rm empty_$DIR
  svn rm $DIR
  svn rm ${DIR}_link
done

DIRS="dir_to_modify"
for DIR in $DIRS;
do
  svn mv empty_$DIR empty_${DIR}_modified
#  svn add empty_${DIR}_modified
  svn mv $DIR ${DIR}_modified
#  svn add ${DIR}_modified
  ln -sf dir_other ${DIR}_link
done

########################
## add svn stuff

echo "file_to_add" > file_to_add
svn add file_to_add

ln -s dir file_link_to_add
svn add file_link_to_add

mkdir empty_dir_to_add
svn add empty_dir_to_add

mkdir dir_to_add
echo "file_in__dir_to_add" > dir_to_add/file_in__dir_to_add
svn add dir_to_add


########################
execute "$SIT status" "show status"

execute "$SIT diff -t diff"
#execute "$SIT diff -v --debug"

# execute "$SIT diff trunk"

# execute "$SIT commit -a"
# execute "$SIT diff trunk test"

# execute "$SIT checkout trunk"

# FIXXME: check files modified on other branch ! => opposite view - double modified / to merge

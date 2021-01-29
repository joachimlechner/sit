#!/bin/bash

# Description: SIT - Svn with gIT extensions, test suite
# Author:      Joachim Lechner
# Licence:     GNU GENERAL PUBLIC LICENSE, Version 2, June 1991
# Source:      https://github.com/joachimlechner/sit

function setup_path {
  path=$1
  message=$2
  echo -e "\n################################################"
  echo "# setup: $message"
  rm -rf $path
  mkdir $path 
  cd $path
  ln -s ../scripts .
  pwd
}

function remove_path {
  path=$1
  message=$2
  echo -e "\n################################################"
  echo "# setup: $message"
  rm -rf $path
}

function header_message {
  echo ""
  echo "######################################################################################"
  echo "# $1"
  echo "######################################################################################"
  echo ""
}

function execute {
  cmd=$1
  description=$2
  echo ""
  echo " .============================================================================"
  if [[ $description ]]; then
     echo " |             $description"
  fi
  echo " | Executing:  $cmd"
  echo " |============================================================================"
  eval $cmd
  echo " '============================================================================"
  echo ""
}

function wait_for_enter {
  #read -n 1 -s -r -p "Press any key to continue"
  read -p "Press enter to continue"
}

function wait_for_any_key {
  read -n 1 -s -r -p "Press any key to continue"
}


function execute_but_wait_before {
  cmd=$1
  description=$2
  echo ""
  echo " .============================================================================"
  echo " |             $description"
  echo " | Executing:  $cmd"
  echo " |============================================================================"

  wait_for_enter

  eval $cmd
  echo " '============================================================================"
  echo ""
}




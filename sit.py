#!/usr/bin/python

# Description: SIT - Svn with gIT extensions, main script
# Author:      Joachim Lechner
# Licence:     GNU GENERAL PUBLIC LICENSE, Version 2, June 1991
# Source:      https://github.com/joachimlechner/sit

import argparse
import os
import subprocess
import sys
from inspect import getsourcefile
from os.path import abspath
from os.path import realpath
from os.path import dirname

# add path where script is located to be able to read all submodules
# submodules are expected to be located / must be located parallel to this file !
sys.path.insert(0, dirname(realpath(getsourcefile(lambda:0))))

from sit_c import *
from tools_c import *

def cmd_status(**parameters):
    the_sit.sit_status(parameters)

def cmd_commit(**parameters):
    the_sit.sit_commit(parameters)

def cmd_add(**parameters):
    the_sit.sit_add(parameters)

def cmd_remove(**parameters):
    the_sit.sit_remove(parameters)

def cmd_branch(**parameters):
    the_sit.sit_branch(parameters)

def cmd_checkout(**parameters):
    the_sit.sit_checkout(parameters)

def cmd_reset(**parameters):
    the_sit.sit_reset(parameters)

def cmd_diff(**parameters):
    the_sit.sit_diff(parameters)

def cmd_update(**parameters):
    the_sit.sit_update(parameters)

def cmd_merge(**parameters):
    the_sit.sit_merge(parameters)
    
def subcmd_stash_list(**parameters):
    the_sit.sit_stash_list(parameters)

def subcmd_stash_drop(**parameters):
    the_sit.sit_stash_drop(parameters)
    
def subcmd_stash_apply(**parameters):
    the_sit.sit_stash_apply(parameters)

def subcmd_stash_push(**parameters):
    the_sit.sit_stash_push(parameters)
    
if __name__ == '__main__':
    the_tools = tools_c() 
    the_sit = sit_c(os.path.abspath(os.getcwd()), the_tools) 

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subparser')

    if the_sit.is_svn_path():
        
        ########################
        parser_sit_merge = subparsers.add_parser('merge', help="Merge given branch to local branch")
        parser_sit_merge.add_argument('branch', nargs=1, help='The target branch, if missing all branches are considered')
        parser_sit_merge.add_argument('-t', dest="branch_type", nargs=1, default=[None], help='The branch type to use for merging from')
        parser_sit_merge.add_argument('-f', dest="ignore_modified_sandbox", action='store_const', help='Force merging even if local modified folders/files exist', const=True, default=False)
        parser_sit_merge.add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
        parser_sit_merge.add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)
        
        ########################
        parser_sit_branch = subparsers.add_parser('branch', help="Show branches or create a branch from the current branch")
        parser_sit_branch.add_argument('branch', nargs='?', help='The target branch, if missing all branches are considered')
        parser_sit_branch.add_argument('-d', dest="avoid_user_name_prefix_to_branch", action='store_const', help='Do not append username to branch name when creating', const=True, default=False)
        parser_sit_branch.add_argument('-f', dest="ignore_modified_sandbox", action='store_const', help='Force creating of branch even if local modified folders/files exist', const=True, default=False)
        parser_sit_branch.add_argument('-t', dest="branch_type", nargs=1, default=the_sit.get_default_branch_type(), help='The branch type to use for branching to')
        parser_sit_branch.add_argument('-m', dest="message", nargs=1, help='The message to use when creating a new branch', default="")
        parser_sit_branch.add_argument('-a', dest="auto_message", action='store_const', help='Use automatic generated log message for operation', const=True, default=False)
        parser_sit_branch.add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
        parser_sit_branch.add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)

        ########################
        parser_sit_add = subparsers.add_parser('add', help="add files/folders to version control")
        parser_sit_add.add_argument('options', nargs='*', help='File(s)/Folder(s) to add', default="")
        parser_sit_add.add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
        parser_sit_add.add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)

        ########################
        parser_sit_remove = {}
        for subcmd in ["remove", "rm"]:
            parser_sit_remove[subcmd] = subparsers.add_parser(subcmd, help="remove files/folders to version control")
            parser_sit_remove[subcmd].add_argument('options', nargs='*', help='File(s)/Folder(s) to remove', default="")
            parser_sit_remove[subcmd].add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
            parser_sit_remove[subcmd].add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)
 
        ########################
        parser_sit_commit = subparsers.add_parser('commit', help='commit changes of the top relative to the local path, or for the given path')
        parser_sit_commit.add_argument('path', nargs='?', help='The path to commit', default=the_sit.get_relative_path_to_root())
        parser_sit_commit.add_argument('-m', dest="message", nargs=1, help='The message to use for commit', default="")
        parser_sit_commit.add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
        parser_sit_commit.add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)

        ########################
        parser_sit_reset = subparsers.add_parser('reset', help='reset changes to head of the top relative to the local path, or for the given path')
        parser_sit_reset.add_argument('path', nargs='?', help='The path to commit', default=the_sit.get_relative_path_to_root())
        parser_sit_reset.add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
        parser_sit_reset.add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)

        ########################
        # sit diff @head    ===    sit diff           local changes
        # sit diff branch_type:branch@revision        default_branch_type should have precedence ! - still if name is unique we can use if from other => war if there are multiple branches !
        # sit diff @revision/prev
        # sit diff @revision/prev/head @revision/prev/head
        # sit diff @revision/head/prev branch_type:branch@revision
        # sit diff branch_type:branch@revision branch_type:branch@revision path/file
        # sit diff <path/file>
        # shortcut for branch_types => t: b: r: if there are no other branch names that have similar namings ! selection must be unique if branch_type is given !
        parser_sit_diff = subparsers.add_parser('diff', help="Diff files between branches and/or revisions")
        # FIXME: sequence to use ?
        parser_sit_diff.add_argument('branch_branch_pathfile', nargs='*', help='Select the branch, branch2, and the file/path to diff. Note that branch=branch2 if only one branch is given, the default branch is the actual one! Items in (...) are optional ! No revision means head/actual status in case of branch is sandbox. Format: (((<branch_type>:)<branch>)(@<revison/prev/head>)) (((<branch2_type>:)<branch2>)(@<revison/prev>)) (<path/file>)')
        parser_sit_diff.add_argument('-t', dest="diff_tool", nargs=1, default=["kdiff3"], help='The diff tool to use. Supported are kdiff3/meld/diff. Default is kdiff3.')
        parser_sit_diff.add_argument('-d', dest="diff_dir", nargs=1, default="/tmp", help='The temporary directory for creating diff data')
        parser_sit_diff.add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
        parser_sit_diff.add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)
       
        ########################
        parser_sit_checkout = subparsers.add_parser('checkout', help="Checkout/change to different branch")
        parser_sit_checkout.add_argument('branch', help='The branch name to checkout/change to')
        parser_sit_checkout.add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
        parser_sit_checkout.add_argument('-t', dest="branch_type", nargs=1, default=None, help='The branch type to use for branching to')
        parser_sit_checkout.add_argument('-f', dest="ignore_modified_sandbox", action='store_const', help='Force checkout of branch even if local modified folders/files exist', const=True, default=False)
        parser_sit_checkout.add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)

        ########################
        parser_sit_status = subparsers.add_parser('status')
        parser_sit_status.add_argument('path', nargs='?', default=the_sit.get_relative_path_to_root())
        parser_sit_status.add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
        parser_sit_status.add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)

        ########################
        parser_sit_update = subparsers.add_parser('update', help="Update path or complete sandbox")
        parser_sit_update.add_argument('path', nargs='?', default=the_sit.get_relative_path_to_root())
        parser_sit_update.add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
        parser_sit_update.add_argument('-f', dest="ignore_modified_sandbox", action='store_const', help='Force update even if local modified folders/files exist', const=True, default=False)
        parser_sit_update.add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)

        ########################
        parser_sit_stash = subparsers.add_parser('stash', help="Stash command")
        #
        subparsers_sit_stash = parser_sit_stash.add_subparsers(dest='subsubparser')

        ############
        parser_sit_stash_push = subparsers_sit_stash.add_parser('push', help="Push modifications to stash")
        parser_sit_stash_push.add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
        parser_sit_stash_push.add_argument('-a', dest="auto_message", action='store_const', help='Use automatic generated log message for operation', const=True, default=False)
        parser_sit_stash_push.add_argument('name', nargs='?', default=None)
        parser_sit_stash_push.add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)
        
        parser_sit_stash_drop = subparsers_sit_stash.add_parser('drop', help="Drop selected stash")
        parser_sit_stash_drop.add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
        parser_sit_stash_drop.add_argument('-a', dest="auto_message", action='store_const', help='Use automatic generated log message for operation', const=True, default=False)
        parser_sit_stash_drop.add_argument('name', nargs='?', default=None)
        parser_sit_stash_drop.add_argument('-u', dest="username", nargs=1, default=[ os.environ['USER'] ], help='The username to use')
        parser_sit_stash_drop.add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)

        parser_sit_stash_apply = {}
        for subcmd in ["apply", "pop"]:
            parser_sit_stash_apply[subcmd] = subparsers_sit_stash.add_parser(subcmd, help="Apply selected stash")
            parser_sit_stash_apply[subcmd].add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
            parser_sit_stash_apply[subcmd].add_argument('-a', dest="auto_message", action='store_const', help='Use automatic generated log message for remove operation', const=True, default=False)
            parser_sit_stash_apply[subcmd].add_argument('name', nargs='?', default=None)
            parser_sit_stash_apply[subcmd].add_argument('-u', dest="username", nargs=1, default=[ os.environ['USER'] ], help='The username to use')
            parser_sit_stash_apply[subcmd].add_argument('-f', dest="ignore_modified_sandbox", action='store_const', help='Force update even if local modified folders/files exist', const=True, default=False)
            parser_sit_stash_apply[subcmd].add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)
        
        parser_sit_stash_list = subparsers_sit_stash.add_parser('list', help="List stashes") #, aliases=['st'])
        parser_sit_stash_list.add_argument('-v', dest="verbose", action='store_const', help='Verbose what is done', const=True, default=False)
        parser_sit_stash_list.add_argument('-u', dest="username", nargs=1, default=[ os.environ['USER'] ], help='The username to use')
        parser_sit_stash_list.add_argument('--debug', dest="debug", action='store_const', help='Debug enable', const=True, default=False)
        
    else: # if not inside a sandbox then

        ########################
        parser_sit_status = subparsers.add_parser('clone') #, aliases=['st'])

        # FIXME: to implement

    kwargs = vars(parser.parse_args())
    if 'subparser' in kwargs:
        subparser_name = kwargs.pop('subparser')
        if subparser_name == "rm":
            subparser_name = "remove"
    else:
        subparser_name = None

    if 'subsubparser' in kwargs:
        subsubparser_name = kwargs.pop('subsubparser')
        if subparser_name == "stash":
            if subsubparser_name == "pop":
                subsubparser_name = "apply"
    else:
        subsubparser_name = None

    if(kwargs['debug']):
        print(kwargs)
        print(subparser_name)
        print(subsubparser_name)
        print('----------------------------')
    
    try:
        if subsubparser_name:
            globals()['subcmd_' + subparser_name + '_' + subsubparser_name](**kwargs)
        elif subparser_name:
            globals()['cmd_' + subparser_name](**kwargs)
    except KeyboardInterrupt:
        print("\n")
        the_tools.error("User Abort detected.")
    except SitException as e:
        the_tools.error("Error detected:\n " + str(e))

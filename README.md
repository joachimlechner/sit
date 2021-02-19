# SIT - Svn with gIT extensions

written by Joachim Lechner

Licence: GNU GENERAL PUBLIC LICENSE, Version 2, June 1991

## The idea
Subversion (svn) misses some neat features that git supports, which were tried to port over with this project.
The basic idea is to have a wrapper script arround svn for easy usage of svn.

### Features
Here some of the implemented features
* all commands operate in all sub folders with the branch root not the actual sub folder
* address branches by <branch_name> only (no requirement for ^/...)
* graphical directory diff (git difftool -d)
* stashing (git stash) per user

### Limitations
To support this some limitations are taken into account:
* default svn directory structure
  ^/trunk
  ^/branches/<branch_name>
  ^/tags/<tag_name>
  ^/releases/<release_name>
* for stashes a new folder is required
  ^/stashes/<stash_name>
* Only basic functionality is taken into account. No special constructs are taken into account at the moment (e.g. externals). Some might work some not.
* Only one branch is checkedout at a time in the sandbox folder. That is the sandbox starts always with ^/trunk or ^/branch/<branch_name>.
* tags/releases are not supported for branching, they are only shown in the sit branch command!

## Supported Commands

### sit status
show status

in all directories return status beginning from the branch root 

### sit add
add file to repository

### sit checkout <branch_name>/<trunk/master>
checkout/change the actual branch

### sit branch
list all branches/tags/releases/trunk, or create branches

###sit merge <branch_name>/<trunk/master>
merge with branches

### sit stash
stashes like in git. The stashes are placed in ^/stashes/<stash_name>.
The <stash_name> includes the user name, a <short_id>, and the creation date.
This is required to be able to have the stash history from the naming, and to have separate stashes for each user.
The data is placed always in the repository and so all users can see them.
It is possible that another user can apply the stash to his repository.

#### sit stash apply/pop <stash_short_name>/<stash_id>/<>
apply saved stash / merge the committed changes from the stash

#### sit stash push <stash_short_name>/<stash_id>/<>
create stash of current state that is not committed yet

#### sit stash drop <stash_short_name>/<stash_id>/<>
remove stash

#### sit stash list
List all available stashes

### to be implemented
* clone
* .svnignores
* setup - create basic environemnt
* forward some missing svn commands to be able to complete need to use the svn command

### Requirements
* Python 2.7 upwards
* Note that with python 3.x inquirer package is used for branch selection
* Subversion >= 1.7 (carret notation (^/trunk), single .svn folder in main repo (at least its not tested from my side))
* Linux (at least more is not tested from my side, but you can check if it works by running the included test suite)

### Installation

Include this path in the PYTHONPATH variable.

An alias to the main script sit.py should also be fine.

alias sit=<THIS_PATH>/sit.py


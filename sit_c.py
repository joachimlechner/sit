# Description: SIT - Svn with gIT extensions, main sit class
# Author:      Joachim Lechner
# Licence:     GNU GENERAL PUBLIC LICENSE, Version 2, June 1991
# Source:      https://github.com/joachimlechner/sit

import subprocess
import re
import os
from os.path import abspath
from os import path

import time
from pprint import pprint

from sit_exceptions import *

import traceback

from tools_c import *

# FIXME: support user prefix for branches / subfolders for branches ?
# FIXME: make use of relative urls instead of full branches ?
# FIXME: get rid of full path urls => use ^ instead


###############################################################
class sit_c:
    
    ###############################################################
    # Members

    sit_debug = False
    
    ####################
    # configuration
    max_config_lines_to_read = 10000
    cfg_editor = ""
    cfg_difftool = "diff"
    cfg_find_exclude_dir = []
    cfg_auto_update_before_merge = True
    cfg_auto_update_after_commit = True
    cfg_disable_update_before_merge = False
    cfg_disable_update_after_commit = False
    
    ####################
    sandbox_is_svn_path = False
    repository_url = ""
    repository_root = ""
    sandbox_root_path = ""
    sandbox_actual_path = "" 
    relative_url = ""
    relative_branch_root_url = ""
    relative_path = "" 
    repository_revision = ""
    sandbox_revision = ""
    project_path = ""
    branch_type = "" 
    branch_name = ""
    branch_types = ['trunk', 'branches', 'tags', 'releases', 'stashes']
    branch_types_no_trunk = ['branches', 'tags', 'releases', 'stashes']
    default_branch_type = 'branches'
    trunk_names = ['trunk', 'master', 'main']
    default_trunk_name = 'trunk'
    default_trunk_type = 'trunk'
    sandbox_branch_id = 'sandbox_branch_id'
    default_stash_folder = 'stashes'
    default_stash_separator = '#'
    auto_message_prefix = "AUTO_MESSAGE: "
    
    tools = None
    
    ###############################################################
    def __init__(self, path, tools):
        self.tools = tools
        self.sandbox_actual_path = path
        self.sandbox_is_svn_path = False

        verbose = 0

        command = '{ svn info . 2>/dev/null || test $? = 1; }'
        lines = self.tools.run_external_command_and_get_results(command, verbose)

        for line in lines:
            self.sandbox_is_svn_path = True
           
            p = re.compile(r'^Relative URL: (.+)$')
            m = p.match(line)
            if m:
                self.relative_url = str(m.group(1))
            
            p = re.compile(r'^Repository Root: (.+)$')
            m = p.match(line)
            if m:
                self.repository_root = str(m.group(1))
            
            p = re.compile(r'^Working Copy Root Path: (.+)$')
            m = p.match(line)
            if m:
                self.sandbox_root_path = str(m.group(1))
            
            p = re.compile(r'^Revision: (\d+)$')
            m = p.match(line)
            if m:
                self.sandbox_revision = str(m.group(1))
  
            p = re.compile(r'^URL: (.+)$')
            m = p.match(line)
            if m:
                self.repository_url = str(m.group(1))

        if self.sandbox_is_svn_path:

            for res in self.tools.run_external_command_and_get_results('svn info ' + self.repository_url + ' 2>/dev/null', verbose):
                p = re.compile(r'^Revision: (\d+)$')
                m = p.match(res)
                if m:
                    self.repository_revision = str(m.group(1))
                    
            relative_branch_root_url_list = self.relative_url.split("/")[::-1]
            
            # decode relative path
            s = self.sandbox_actual_path
            s = re.sub(r"^" + str(self.sandbox_root_path), '', s)
            s = re.sub(r'^(/+)', '', s)
            s = re.sub(r'(/+)$', '', s)
            p = s.split('/')
            if len(s) == 0:
                self.relative_path = "."
            else:
                l = []
                for s in p:
                    l.append("..")
                    relative_branch_root_url_list.pop(0)
                self.relative_path = '/'.join(l)

            self.relative_branch_root_url = "/".join(relative_branch_root_url_list[::-1])

            # decode type and branch name
            p = re.compile('^(\^([^\^]*|))/(' + '|'.join(self.branch_types) + ')(/([^/]+)(/|)|)')
            m = p.match(self.relative_url)
            if m:
                if str(m.group(3)) in self.trunk_names:
                    self.project_path          = str(m.group(1))
                    self.branch_type           = self.default_trunk_name
                    self.branch_name           = self.default_trunk_type
                else:
                    self.project_path              = str(m.group(1))
                    self.branch_type               = str(m.group(3))
                    self.branch_name               = str(m.group(5))
            else:
                raise SitExceptionParseError("Cannot match branch type/name in <" + self.relative_url + ">")

            self.read_configuration()

    ###############################################################
    def read_configuration(self):
        # default configuration located at ~/.sitconfig override in repo/.sitconfig

        self.read_configuration_from_file(os.path.expanduser("~") + "/.sitconfig")
        self.read_configuration_from_file(self.sandbox_root_path + "/.sitconfig")
    
    ###############################################################
    def read_configuration_from_file(self, filename):
        if self.tools.does_file_exist(filename):
            if self.sit_debug:
                self.tools.debug("Reading configuration from " + filename)
                
            try:
                data = self.tools.read_file(filename, "#", self.max_config_lines_to_read)
            except ToolException as e:
                raise SitException("Could not read data from " + filename + " beacuse:\n" + str(e))

            # configuration lines of the form: foo = bar
            p_editor = '^\s*EDITOR\s*=\s*(\S+.+)\s*$'
            p_difftool = '^\s*DIFFTOOL\s*=\s*(\S+.+)\s*$'
            p_find_exclude_dir = '^\s*FIND_EXCLUDE_DIR\s*=\s*(\S+.+)\s*$'
            p_auto_update_after_commit = '^\s*AUTO_UPDATE_AFTER_COMMIT\s*=\s*(\S+.+)\s*$'
            p_auto_update_before_merge = '^\s*AUTO_UPDATE_BEFORE_MERGE\s*=\s*(\S+.+)\s*$'
            p_disable_update_after_commit = '^\s*DISABLE_UPDATE_AFTER_COMMIT\s*=\s*(\S+.+)\s*$'
            p_disable_update_before_merge = '^\s*DISABLE_UPDATE_BEFORE_MERGE\s*=\s*(\S+.+)\s*$'
            
            for data_item in data:
                self.cfg_editor = self.decode_cfg_data(self.cfg_editor, p_editor, data_item)
                self.cfg_difftool = self.decode_cfg_data(self.cfg_difftool, p_difftool, data_item)
                
                self.cfg_auto_update_after_commit = self.decode_cfg_data_true_false(self.cfg_auto_update_after_commit, p_auto_update_after_commit, data_item)
                self.cfg_auto_update_before_merge = self.decode_cfg_data_true_false(self.cfg_auto_update_before_merge, p_auto_update_before_merge, data_item)
                self.cfg_disable_update_after_commit = self.decode_cfg_data_true_false(self.cfg_disable_update_after_commit, p_disable_update_after_commit, data_item)
                self.cfg_disable_update_before_merge = self.decode_cfg_data_true_false(self.cfg_disable_update_before_merge, p_disable_update_before_merge, data_item)

                new_find_exclude_dir = self.decode_cfg_data_list(self.cfg_find_exclude_dir, p_find_exclude_dir, data_item)
                if new_find_exclude_dir:
                    self.cfg_find_exclude_dir.append(new_find_exclude_dir)
                
    ###############################################################
    def decode_cfg_data_list(self, values, regular_expression, data):
        return self.decode_cfg_data(None, regular_expression, data)
                    
    def decode_cfg_data(self, value, regular_expression, data):
        p_data = re.compile(regular_expression)
        m_data = p_data.match(data)
        if m_data:
            return m_data.group(1)
        else:
            return value

    def decode_cfg_data_true_false(self, value, regular_expression, data):
        value_next = self.decode_cfg_data(None, regular_expression, data)
        p_true  = re.compile('^(1|True|TRUE)$')
        p_false = re.compile('^(0|False|FALSE)$')
        if value_next:
            if p_true.match(value_next):
                return True
            elif p_false.match(value_next):
                return False
            else:
                return value                
        else:
            return value
    
    ###############################################################
    def show(self):

        if self.sandbox_is_svn_path:
            print("---------------------------------------")
            print("editor:                                                " + self.cfg_editor)
            print("difftool:                                              " + self.cfg_difftool)
            print("exclude dirs:                                          " + ', '.join(self.cfg_find_exclude_dir))
            print("auto_update_before_merge:                              " + str(self.cfg_auto_update_before_merge))
            print("disable_update_before_merge:                           " + str(self.cfg_disable_update_before_merge))
            print("auto_update_after_commit:                              " + str(self.cfg_auto_update_after_commit))
            print("disable_update_after_commit:                           " + str(self.cfg_disable_update_after_commit))
            print("---------------------------------------")
            print("Path (sandbox_actual_path):                            " + self.sandbox_actual_path) 
            print("Relative path (relative_path):                         " + self.relative_path)
            print("Relative URL (relative_url):                           " + self.relative_url)
            print("Relative Branch URL (relative_branch_root_url):        " + self.relative_branch_root_url)
            print("Repository URL (repository_url):                       " + self.repository_url)
            print("Repository Root (repository_root):                     " + self.repository_root)
            print("Repository Revision (repository_revision):             " + self.repository_revision)
            print("Sandbox root path (sandbox_root_path):                 " + self.sandbox_root_path)
            print("Sandbox Revision (sandbox_revision):                   " + self.sandbox_revision)
            print("project path (project_path):                           " + self.project_path)
            print("branch type (branch_type):                             " + self.branch_type)
            print("branch name (branch_name):                             " + self.branch_name)           
            print("---------------------------------------")
        else:
            print("No SVN folder found")

    ###############################################################
    def get_repository_root(self):
        if self.sandbox_is_svn_path:
            return self.repository_root
        else:
            raise SitExceptionInternalFatalError("Unexpected position reached")

    ###############################################################
    def get_relative_path_to_root(self):
        if self.sandbox_is_svn_path:
            return self.relative_path
        else:
            raise SitExceptionInternalFatalError("Unexpected position reached")

        
    ###############################################################
    def get_branch_name(self):
        if self.sandbox_is_svn_path:
            return self.branch_name
        else:
            raise SitExceptionInternalFatalError("Unexpected position reached")

    ###############################################################
    def is_svn_path(self):
        return self.sandbox_is_svn_path

    ###############################################################
    def is_equal_to_relative_path(self, path):
        if self.sandbox_is_svn_path:
            if path == self.relative_path:
                return True
            else:
                return False
        else:
            return False

    ###############################################################
    def is_equal_to_branch(self, branch_name, branch_type):
        return branch_name == self.branch_name

    ###############################################################
    def get_branch_types(self):
        return self.branch_types

    ###############################################################
    def get_default_branch_type(self):
        return self.default_branch_type

    ###############################################################
    def get_branch_merged_name(self, branch_name, branch_type):
        if branch_name in self.trunk_names:
            return self.default_trunk_name
        else:
            return branch_type + '/' + branch_name

    ###############################################################
    def get_branch_repository_url(self, branch_name, branch_type):
        if branch_name in self.trunk_names:
            return self.project_path + '/' + self.default_trunk_name
        else:
            return self.project_path + '/' + branch_type + '/' + branch_name

    ###############################################################
    def get_branch_repository_url_merged(self, branch_type_and_name):
        p = re.compile('^([^/]+)/([^/]+)')
        m = p.match(branch_type_and_name)
        if m:
            return self.get_branch_repository_url(m.group(2), m.group(1))
        else:
            raise SitExceptionInternalFatalError("Could not convert branch_type_and_name to branch_name and branch_type")

        
    ###############################################################
    def split_branch_merged(self, branch_type_and_name):
        p = re.compile('^([^/]+)/([^/]+)')
        m = p.match(branch_type_and_name)
        if m:
            return [m.group(1), m.group(2)]
        else:
            raise SitExceptionInternalFatalError("Could not convert branch_type_and_name to branch_name and branch_type")

    ###############################################################
    def get_branch_selected_type(self, branch_selected):
        return branch_selected[0]

    ###############################################################
    def get_branch_selected_name(self, branch_selected):
        return branch_selected[1]
        
    ###############################################################
    def is_repository_url_existing(self, repository_url, verbose=False):
       if ''.join(self.tools.run_external_command_and_get_results('{ svn info ' + repository_url + ' 2>/dev/null || test $? = 1; }', verbose)) == "":
            return False
       else:
            return True

    ###############################################################
    def is_sandbox_modified(self, verbose=0):
        if ''.join(self.tools.run_external_command_and_get_results('svn status -q ' + self.relative_path, verbose)) == "":
            return False
        else:
            return True

    ###############################################################
    ###############################################################
    ###############################################################
    def sit_add(self, parameters):
        if(parameters['debug']):
            self.show()

        self.tools.process("Adding")
        self.tools.run_external_command("svn add " + ' '.join(parameters['options']), parameters['verbose'])

    ###############################################################
    def sit_remove(self, parameters):
        if(parameters['debug']):
            self.show()
            
        self.tools.run_external_command("svn remove " + ' '.join(parameters['options']), parameters['verbose'])

    ###############################################################
    def sit_commit(self, parameters):
        if(parameters['debug']):
            self.show()

        message = ' '.join(parameters['message'])
            
        try:
            self.do_commit(parameters['path'], message, parameters['verbose'])
        except SitException as e:
            raise SitExceptionAbort("Aborting due execution error.\n" + str(e))
        else:
            
            if not self.cfg_disable_update_after_commit:
                if not self.cfg_auto_update_after_commit:
                    tbd = 1
                    #try:
                    #    revision = self.tools.select_from_list("What revision to branch from?", choice)
                    #except ToolException as e:
                    #    raise SitExceptionAbort("Aborting due selection error.\n" + str(e))
                self.do_update(parameters['verbose'])
        
    ###############################################################
    def do_commit(self, path, message, verbose):
        self.tools.process("Committing data in " + path)
        command = "svn commit " + path
        if message:
            command = command + " -m \'" + message + '\''
        elif self.cfg_editor != "":
            command = "SVN_EDITOR=" + self.cfg_editor + " " + command
            
        try:
            self.tools.run_external_command_no_print(command, verbose)
        except ToolException as e:
            raise SitExceptionAbort("Aborting due execution error.\n" + str(e))
        
    ###############################################################
    def sit_reset(self, parameters):
        if(parameters['debug']):
            self.show()

        self.do_reset(parameters['path'], parameters['verbose'])

    ###############################################################
    def do_reset(self, path, verbose):
        self.tools.process("Resetting " + path)
        self.tools.run_external_command("svn revert -R " + path, verbose)
        
    ###############################################################
    def sit_branch(self, parameters):
        if(parameters['debug']):
            self.show()
        
        if not parameters['branch']:
            # list branches
            for i_branch_type in self.branch_types:
                print(i_branch_type + ':')
                if i_branch_type == "trunk": # FIXME: support differen trunk names
                    command = 'svn ls ' + self.project_path + '/' + ' | grep trunk/'
                else:
                    command = 'svn ls ' + self.project_path + '/' + i_branch_type

                for branch_full_path in self.tools.run_external_command_and_get_results(command, parameters['verbose']):
                    p = re.compile(r'^([^/]+)/$')
                    m = p.match(branch_full_path)
                    if m:
                        branch_name = str(m.group(1))
                        if self.is_equal_to_branch(branch_name, i_branch_type):
                            print(" * " + branch_name)
                        else:
                            print("   " + branch_name)
        else:
            # create branch from current branch + revision
            # os.environ['HOME']
            # svn does not update automatically on commit
            # hence svn info shows the revision from last update only
            # when branching we might want to branch from the actual version or from a committed one
            # how to select this by the user ?
            # show list of available revisions from head to current version - to be selected by the user
            # if version between remote and local is different
            # svn info local
            # svn info ^/trunk / branch 

            if not parameters['avoid_user_name_prefix_to_branch']:
                branch = os.environ['USER'] + "." + parameters['branch']
            else:
                branch = parameters['branch']

            branch_to = self.get_branch_repository_url(branch, parameters['branch_type'])

            if not parameters['ignore_modified_sandbox']:
                if self.is_sandbox_modified(parameters['verbose']):
                    raise SitExceptionAbort("Aborting operation. The sandbox is modified. Overwrite with -f option.")

            if parameters['message']:
                branch_message = ' '.join(parameters['message'])
            elif parameters['auto_message']:
                branch_message = "auto_message"
            else: # use svn edit command if none given
                branch_message = None

            self.do_branch(branch, branch_to, branch_message, parameters['verbose'])

    ###############################################################
    def do_branch(self, branch, branch_to_url, message, verbose):
            if self.is_repository_url_existing(branch_to_url):
                raise SitExceptionAbort("Aborting operation. There is already a branch with the same name existing <" + branch_to_url + ">.")

            if self.repository_revision == self.sandbox_revision:
                if message is "auto_message":
                    message = self.auto_message_prefix + "creating branch " + branch + " (" + branch_to_url + ") from " + self.relative_branch_root_url + "@" + self.repository_revision
                self.do_copy(self.relative_branch_root_url, self.repository_revision, branch_to_url, message, verbose)
                return self.repository_revision
            else:
                revisions = []
                log = ""
                for res in self.tools.run_external_command_and_get_results('svn log -r' + self.sandbox_revision + ':' + self.repository_revision + ' ' + self.relative_branch_root_url, verbose):
                    p = re.compile(r'^r(\d+) | ')
                    m = p.match(res)
                    if m:
                        revisions.append(str(m.group(1)))
                    log = log + res
                
                if revisions:
                    self.tools.info("Repository and Sandbox Revision Missmatches. Select revision to branch from.")
                    try:
                        revision = self.tools.select_from_list("What revision to branch from?", revisions)
                    except ToolException as e:
                        raise SitExceptionAbort("Aborting due selection error.\n" + str(e))
                else:
                    # if nothing changed then use sandbox revision ?! -
                    # this happens when somewhere else a branch got committed ??? local commits without update should not end in this situation !
                    revision = self.sandbox_revision

                if message is "auto_message":
                    message = self.auto_message_prefix + "creating branch " + branch + " (" + branch_to_url + ") from " + self.relative_branch_root_url + "@" + revision
                self.do_copy(self.relative_branch_root_url, revision, branch_to_url, message, verbose)
                return revision

    ###############################################################
    def do_copy(self, branch_from_url, branch_from_revision, branch_to_url, message, verbose):
        self.tools.process("Copying " + branch_from_url + "@" + branch_from_revision + " to " + branch_to_url)
        command = 'svn copy -r ' + branch_from_revision + ' ' + branch_from_url + ' ' + branch_to_url
        if message:
            command = command + " -m \'" + message + "\'"
        elif self.cfg_editor != "":
            command = "SVN_EDITOR=" + self.cfg_editor + " " + command
            
        try:
            self.tools.run_external_command_no_print(command, verbose)
            if not self.is_repository_url_existing(branch_to_url):
                raise SitExceptionAbort("Failed to copy " + branch_from_url + "@" + branch_from_revision + " to " + branch_to_url)
        except ToolException as e:
            raise SitExceptionAbort("svn copy failed\n" + str(e))
        
    ###############################################################
    def select_branch_by_name(self, branch, branch_type, verbose):
        branch_types = self.branch_types
        if branch_type:
            branch_types = [branch_type]

        # wildcard support => * at end / beginning needs escaping in shell => put under '...' or \*
        branch = re.sub(r'^\*', '.*', branch)
        branch = re.sub(r'([^.])\*', '\g<1>.*', branch)

        branches = []
        for i_branch_type in branch_types:
            if i_branch_type == self.default_trunk_type:
                command = 'svn ls ' + self.project_path + '/' + '| grep trunk/'
            else:
                command = 'svn ls ' + self.project_path + '/' + i_branch_type

            for branch_full_path in self.tools.run_external_command_and_get_results(command, verbose):
                p = re.compile(r'^([^/]+)/$')
                m = p.match(branch_full_path)
                if m:
                    branch_name = str(m.group(1))

                    p = re.compile('^' + branch + '$')
                    m = p.match(branch_name)
                    if m:
                        branches.append(i_branch_type + '/' + branch_name)
                    else:
                        p = re.compile('^' + os.environ['USER'] + '.' + branch + '$')
                        m = p.match(branch_name)
                        if m:
                            branches.append(i_branch_type + '/' + branch_name)
  
        if len(branches)>1:
            try:
                full_branch = self.tools.select_from_list("Which branch to you mean ?", branches)
            except ToolException as e:
                raise SitExceptionAbort("Aborting due selection error.\n" + str(e))
        elif len(branches)==0:
            return None
        else:
            full_branch = branches[0]

        branch_selected = self.split_branch_merged(full_branch)
            
        return self.get_branch_repository_url_merged(full_branch), branch_selected

    ###############################################################
    def sit_checkout(self, parameters):
        if(parameters['debug']):
            self.show()

        revision = "HEAD"
        
        if not parameters['ignore_modified_sandbox']:
            if self.is_sandbox_modified(parameters['verbose']):
                raise SitExceptionAbort("Aborting operation. There are uncommitted changes in sandbox.")

        branch_repository_url, branch_selected = self.select_branch_by_name(parameters['branch'], parameters['branch_type'], parameters['verbose'])

        if branch_repository_url:
            self.do_checkout(branch_repository_url, revision, parameters['verbose'])
            #if self.is_repository_url_existing(branch_repository_url):
        else:
            raise SitExceptionAbort("Aborting operation. Could not match branch name to any branch.")

        
    ###############################################################
    def do_checkout(self, branch_url, revision, verbose):
        self.tools.process("Checking out " + branch_url + "@" + revision)
        self.tools.run_external_command('svn switch ' + branch_url + '@' + revision + ' ' + self.get_relative_path_to_root(), verbose)

    ###############################################################
    def pathfile_to_abs_pathfile(self, pathfile):
        pathfile_resolved = abspath(self.sandbox_actual_path + '/' + pathfile)
        return pathfile_resolved
    
    ###############################################################
    def is_pathfile_existing(self, pathfile):
        return path.exists(pathfile)

    ###############################################################
    # check if pathfile matches sandbox_root_path
    def is_pathfile_within_sandbox_root_path(self, pathfile):
        p = re.compile('^(' + self.sandbox_root_path + ')(.*)')
        m = p.match(pathfile)
        if m:
            return True
        else:
            return False

    ###############################################################
    def decode_pathfile(self, pathfile):
        pathfile_decoded = self.pathfile_to_abs_pathfile(pathfile)
        if self.is_pathfile_within_sandbox_root_path(pathfile_decoded):
            return pathfile_decoded
        else:
            raise SitExceptionDecode("Path/File not within in repository/sandbox area <" + pathfile_decoded + ">")

    ###############################################################
    def decode_pathfile_relative_to_sandbox_root_path(self, pathfile):
        pathfile_decoded = self.pathfile_to_abs_pathfile(pathfile)
        p = re.compile("^(" + self.sandbox_root_path + ")(.*)$")
        m = p.match(pathfile_decoded)
        if m:
            p2  = re.compile("^([/]+)([^/].+)$") # remove leading '/'
            m2 = p2.match(m.group(2))
            if m2:
                return m2.group(2)
            else:
                return m.group(2)
        else:
            raise SitExceptionDecode("Path/File not within in repository/sandbox area <" + pathfile_decoded + "> at sandbox root <" + self.sandbox_root_path + ">")

    ###############################################################
    def decode_pathfile_absolute_to_sandbox_root_path(self, pathfile):
        p = re.compile("^(" + self.sandbox_root_path + ")(.+)$")
        m = p.match(pathfile)
        if m:
            p2  = re.compile("^([/]+)([^/].+)$")
            m2 = p2.match(m.group(2))
            if m2:
                return m2.group(2)
            else:
                return m.group(2)
        else:
            raise SitExceptionDecode("Path/File not within in repository/sandbox area <" + pathfile + "> at sandbox root <" + self.sandbox_root_path + ">")

    ###############################################################
    # split pathfile into basepath and remaining subpath
    # returns basepath,subpath
    def split_pathfile(self, pathfile):
        p1_str = "^(" + self.sandbox_root_path + ")(.*)$"
        p2_str = "^(\^/(|.+/)(" + '|'.join(self.branch_types_no_trunk) + ')/' + '([^/]+))(.*)$'
        p3_str = "^(\^/(|.+/)(" + '|'.join(self.trunk_names) + '))(.*)$'
        
        p1 = re.compile(p1_str)
        p2 = re.compile(p2_str)
        p3 = re.compile(p3_str)
        
        m1 = p1.match(pathfile)
        m2 = p2.match(pathfile)
        m3 = p3.match(pathfile)

        d = []
        if m1:
            d = [m1.group(1), m1.group(2)]
        elif m2:
            d = [m2.group(1), m2.group(5)]
        elif m3:
            d = [m3.group(1), m3.group(4)]
        else:
            raise SitExceptionDecode("Path/File not within in repository or sandbox area <" + pathfile + "> !~ <" + p1_str + "> or <" + p2_str + "> or <" + p3_str + ">")

        # if starting with '/' then remove the leading '/' between basepath and subpath !
        ps = re.compile("^/(.*)$")
        ms = ps.match(d[1])
        if ms:
            return d[0], ms.group(1)
        else:
            return d[0], d[1]
        
    ###############################################################
    def get_repository_pathfile_revision(self, repository_branch_url_pathfile, revision_backwards_from_head, verbose):
        revision_decoded = ''.join(self.tools.run_external_command_and_get_results('svn log -q -l ' + str(revision_backwards_from_head + 1) + ' ' + repository_branch_url_pathfile + ' | grep ^r | tail -n1', verbose))
        p = re.compile(r'^r(\d+) ')
        m = p.match(revision_decoded)
        if m:
            return str(m.group(1))
        else:
            raise SitExceptionDecode("Could not find revision <head-" + str(revision_backwards_from_head) + '> for <' + repository_branch_url_pathfile + '>')

    ###############################################################
    def is_valid_svn_pathfile_revision(self, repository_branch_url_pathfile, revision, verbose):
        for res in self.tools.run_external_command_and_get_results('svn ls -r ' + revision + ' ' + repository_branch_url_pathfile, verbose):
            p = re.compile(r'^svn: E')
            m = p.match(res)
            if m:
                return False
        return True
        
    ###############################################################
    # Description:
    #   tbd
    # Parameters:
    #
    # Returns:
    #   returns data structure that contains:
    #
    #   data['path']       = <basepath>/<subpath>
    #   data['basepath']   = repository base path
    #   data['subpath']    = sub path below repository base path
    #   data['branch']     = <branch_type>/<branch_name> / <default_trunk_name> / sandbox
    #   data['revision']   = revision number / "sandbox"
    #   data['is_sandbox'] = True/False
    #
    def decode_to_branch_at_revision(self, branch, pathfile, verbose, debug):
        # branch: tags:branch_name@<revision_number|prev|head>
        # pathfile: /bla/

        data = {}

        if debug:
            self.tools.debug("<<<")
            self.tools.debug("branch:   " + branch)
            self.tools.debug("pathfile: " + pathfile)
            
        if branch == self.sandbox_branch_id:
            pathfile_decoded = self.decode_pathfile_relative_to_sandbox_root_path(pathfile)
            if pathfile_decoded == "":
                data['path'] = self.sandbox_root_path
            else:
                data['path'] = self.sandbox_root_path + "/" + pathfile_decoded
            data['basepath'] = self.sandbox_root_path
            data['subpath'] = pathfile_decoded
            data['branch'] = "sandbox"
            data['revision'] = "sandbox"
            data['is_sandbox'] = True

            if debug:
                self.tools.debug("=> sandbox")
                self.tools.debug("pathfile: " + pathfile)
        else:
            # tags:branch_name@<revision_number|prev|head>
            
            p = re.compile('(([^\:]+)\:)?' + '([^@]*)' + '(@(.+))?')
            m = p.match(branch)
            if m:
                branch_name = str(m.group(3))
           
                if branch_name == '.':
                    raise SitExceptionDecode("Unexpected branch name <" + branch_name + ">")

                if branch_name == '':
                    branch_name = self.branch_name

                if not m.group(2):
                    if str(m.group(3)) == '':
                        branch_type = self.branch_type
                    elif branch_name == 'trunk':
                        branch_type = 'trunk'
                    else:
                        branch_type = self.default_branch_type
                else:
                    p_type = re.compile('^(' + '|'.join(self.branch_types) + ')$')
                    m_type = p_type.match(m.group(2))
                    if m_type:
                        branch_type = str(m_type.group(1))
                    else:
                        raise SitExceptionDecode("Could not match branch type <" + m.group(2) + "> in types <" + '|'.join(self.branch_types) + ">")
           
                repository_branch_url = self.get_branch_repository_url(branch_name, branch_type)
                pathfile_decoded = self.decode_pathfile_relative_to_sandbox_root_path(pathfile)
                repository_branch_url_pathfile = repository_branch_url + '/' + pathfile_decoded
                
                if debug:
                    self.tools.debug("=> url")
                    self.tools.debug("branch_name: " + branch_name)
                    self.tools.debug("branch_type: " + branch_type)
                    self.tools.debug("repository_branch_url: " + repository_branch_url)
                    self.tools.debug("pathfile: " + pathfile)
                    self.tools.debug("pathfile_decoded: " + pathfile_decoded)
                    self.tools.debug("repository_branch_url_pathfile: " + repository_branch_url_pathfile)
                    
                # svn log file:///home/joachim/svn_test/repo/branches/test -q -l 10 | grep ^r  | awk '{print $1}' | grep -m2 . | tail -n1
                # FIXME: implement ^K for revision head-K
                if not m.group(5):
                    revision = self.get_repository_pathfile_revision(repository_branch_url_pathfile, 0, verbose)
                else:
                    revision_to_decode = m.group(5)
                    p_prev   = re.compile('^(prev|PREV)$')
                    p_head   = re.compile('^(head|HEAD)$')
                    p_number = re.compile('^(\d+)$')
                    p_prevnr = re.compile('^-(\d+)$')
                    m_prev   = p_prev.match(revision_to_decode)
                    m_head   = p_head.match(revision_to_decode)
                    m_number = p_number.match(revision_to_decode)
                    m_prevnr = p_prevnr.match(revision_to_decode)
           
                    revision = int(self.get_repository_pathfile_revision(repository_branch_url_pathfile, 0, verbose))
           
                    if m_prev:
                        revision = revision - 1
                    elif m_head:
                        # keep as is
                        revision = revision + 0
                    elif m_number:
                        # check revision exists for below !
                        revision = int(m_number.group(1))
                    elif m_prevnr:
                        revision =  revision - int(m_prevnr.group(1))
                    else:
                        raise SitExceptionDecode("Could not match revision information <" + revision_to_decode + ">")
           
                    revision = str(revision)
                    if not self.is_valid_svn_pathfile_revision(repository_branch_url_pathfile, revision, verbose):
                        raise SitExceptionDecode("Invalid revision <" + revision + "> for <" + repository_branch_url_pathfile + ">")

                data['basepath'], data['subpath'] = self.split_pathfile(repository_branch_url_pathfile)
                data['branch'] = self.get_branch_merged_name(branch_name, branch_type)
                data['revision'] = revision
                data['is_sandbox'] = False
                data['path'] = repository_branch_url_pathfile
            else:
                raise SitExceptionDecode("Could not match to be any branch specification <" + branch + ">")
                
        if debug:
            self.tools.debug("basepath:      " + data['basepath'])
            self.tools.debug("subpath:       " + data['subpath'])
            self.tools.debug("branch:        " + data['branch'])
            self.tools.debug("revision:      " + data['revision'])
            self.tools.debug("is sandbox:    " + str(data['is_sandbox']))
            self.tools.debug(">>>")
                
        return data
        
    ###############################################################
    def try_to_decode_branch_path(self, from_branch, from_path, to_branch, to_path, verbose, debug):
        if debug:
            self.tools.debug("DEF: try_to_decode_branch_path")
            self.tools.debug("from branch: " + from_branch)
            self.tools.debug("from path:   " + from_path)
            self.tools.debug("to branch:   " + to_branch)
            self.tools.debug("to path:     " + to_path)
            
        paths_try = {}
        try:
            try:
                # branch2 path
                path1_try = self.decode_to_branch_at_revision(from_branch, from_path, verbose, debug)
            except SitExceptionDecode as e:
                raise SitExceptionDecode("Could not decode path FROM <" + from_branch + "/" + from_path + "> because:\n  " + str(e))
            
            try:
                path2_try = self.decode_to_branch_at_revision(to_branch, to_path, verbose, debug)
            except SitExceptionDecode as e:
                raise SitExceptionDecode("Could not decode path TO <" + to_branch + "/" + to_path + "> because:\n  " + str(e))
        except SitExceptionDecode as e:
            raise SitExceptionDecode("Could not decode because:\n  " + str(e))
            return None
        else:
            paths_try['from.path']          = path1_try['path']
            paths_try['from.basepath']      = path1_try['basepath']
            paths_try['from.subpath']       = path1_try['subpath']
            paths_try['from.branch']        = path1_try['branch']
            paths_try['from.revision']      = path1_try['revision']
            paths_try['from.is_sandbox']    = path1_try['is_sandbox']

            paths_try['to.path']          = path2_try['path']
            paths_try['to.basepath']      = path2_try['basepath']
            paths_try['to.subpath']       = path2_try['subpath']
            paths_try['to.branch']        = path2_try['branch']
            paths_try['to.revision']      = path2_try['revision']
            paths_try['to.is_sandbox']    = path2_try['is_sandbox']
            
            return paths_try

    ###############################################################
    def get_svnbasepath(self, path):
        p = re.compile('^(.+)@(\d+)$')
        m = p.match(path)
        if m:
            return m.group(1)
        else:
            p = re.compile('^(.+)/$')
            m = p.match(path)
            if m:
                return m.group(1)
            else:
                return path

    ###############################################################
    def get_svnbaserevision(self, path):
        path_split = path.split('@')
        if len(path_split)>=2:
            return path_split[1]
        else:
            return ''

    ###############################################################
    def is_file_from_sandbox_folder(self, path):
        p = re.compile('^' + self.sandbox_root_path)
        m = p.match(path)
        if m:
            return True
        else:
            return False

    ###############################################################
    def get_link_if_path_or_file_is_symbolic(self, filepath, verbose):
        p = re.compile('^.+\s+symbolic link to\s+(.+)\s*$')
        link = None
        for line in self.tools.run_external_command_and_get_results('file ' + filepath, verbose):
            m = p.match(line)
            if m:
                link = m.group(1)
        return link

    ###############################################################
    def detect_folders(self, path, revision, verbose):
        data = []
        p = re.compile('^\^')
        m = p.match(path)

        try:
            if m:
                if revision != "":
                    revision = "-r " + revision + " "
                command = "svn ls --depth=infinity " + revision + path + " | grep /$ | sed 's,/$,,g' " # + ' || test $? = 1; }'
                for res in self.tools.run_external_command_and_get_results(command, verbose):
                    # self.tools.debug("CMD: " + command + " " + res)
                    data.append(res)
            else:
                path_to_use = path + "/"
                # FIXME: better use status + svn ls of actual path with revision ?! we have lots of overhead if there are many local files !
                # find . \( -not \( -wholename '*/.svn*' -o -wholename '*/repo*' \) -o -prune \) -type d -print

                find_prune = ""
                if self.cfg_find_exclude_dir:
                    find_prune = '\( -not \( -wholename \'' + '\' -o -wholename \''.join(self.cfg_find_exclude_dir) + '\' \) -o -prune \)'
                
                command = "find " + path_to_use + " " + find_prune + " -type d -print | grep -v \.svn | grep -v ^\.$ | sed 's," + path_to_use + ",,g' | { grep -v '^$'" + ' || test $? = 1; }'
                # command = "find " + path_to_use + " -type d | grep -v \.svn | grep -v ^\.$ | sed 's," + path_to_use + ",,g' | { grep -v '^$'" + ' || test $? = 1; }'
                
                #command = "find " + path + " -type d | grep -v \.svn | grep -v ^\.$ | sed 's," + path + ",,g' | grep -v '^$'"
                
                for res in self.tools.run_external_command_and_get_results(command, verbose):
                    data.append(res)
                    
        except ToolException as e:
            raise SitExceptionAbort("Folder detection failed:\n" + str(e))

        return data

    ###############################################################
    def is_single_file(self, path, revision, verbose):
        single_file = False
        try:
            if self.is_sandbox(path):
                folder = False
                p = re.compile('^.+\s+directory\s*$')
                for line in self.tools.run_external_command_and_get_results('file ' + path, verbose):
                    m = p.match(line)
                    if m:
                        folder = True
                if not folder:
                    single_file = True
            else:
                data = []
                items = 0
                if revision != "":
                    revision = "-r " + revision + " "
                    command = "svn ls " + revision + path
                for res in self.tools.run_external_command_and_get_results(command, verbose):
                    items = items + 1
                    data.append(res)
                if items == 1:
                    p = re.compile('/$')
                    m = p.match(data[0])
                    if m:
                        single_file = False
                    else:
                        single_file = True
                        
        except ToolException as e:
            raise SitExceptionAbort("Folder detection failed:\n" + str(e))
        
        return single_file

    ###############################################################
    def is_sandbox(self, path):
        p = re.compile('^\^')
        m = p.match(path)
        if m:
            return False
        else:
            return True

    ###############################################################        
    def decode_status_data(self, status_data):
        status_data_decoded = {}
        p = re.compile('^(M|A|D)(.*)\s+(' + '|'.join(base_paths) + ')(/\S+|)\s*$')
        m = p.match(status_data)
        if m:
            status_data_decoded['status'] = m_deleted.group(1)
            status_data_decoded['path'] = m_deleted.group(2)
            status_data_decoded['relative_path'] = m_deleted.group(3)
        else:
            raise SitExceptionAbort("Data decoding error in " + status_data)

    ###############################################################
    def invert_merge_status(self, status):
        p_m = re.compile('^M$')
        p_a = re.compile('^A$')
        p_d = re.compile('^D$')

        m_m = p_m.match(status)
        m_a = p_a.match(status)
        m_d = p_d.match(status)

        if   m_m:
            return "M"
        elif m_a:
            return "D"
        elif m_d:
            return "A"
        else:
            raise SitExceptionAbort("Could not invert status <" + status + ">")
                
    ###############################################################
    def forward_merge_status(self, status_from, status_to):
        p_m = re.compile('^M$')
        p_a = re.compile('^A$')
        p_d = re.compile('^D$')

        f_m = p_m.match(status_from)
        f_a = p_a.match(status_from)
        f_d = p_d.match(status_from)
        
        t_m = p_m.match(status_to)
        t_a = p_a.match(status_to)
        t_d = p_d.match(status_to)

        #####
        # from => to
        # A dded
        # R emoved
        # M odified
        ######
        #    A  R  M (= status for from is sandbox)
        # A  A  R  M
        # R  M_ R  R_
        # M  M_ R  M
        ######
        #   A  R  M  (= status for to is sandbox)
        # A A  R  M   
        # R A_ R  A_    
        # M A_ R  M   
        ######

        if   f_m and t_m:
            return "M"
        elif f_a and t_a:
            return "A"
        elif f_d and t_d:
            return "D"

        elif f_m and t_a:
            return "M"
        elif f_m and t_d:
            return "D"

        elif f_a and t_m:
            return "A"
        elif f_a and t_d:
            return "D"
        
        elif f_d and t_m:
            return "A"
        elif f_d and t_a:
            return "A"

        else:
            raise SitExceptionAbort("Could not merge status from <" + status_from + "> to <" + status_to + ">")

    ###############################################################
    def invert_merge_status_of_path(self, status_data):
        data = self.get_status_of_path_empty()
        
        for status_data_item in status_data['not_matched']:
            data['not_matched'].append(status_data_item)
        
        for status_data_item_id in status_data['matched'].keys():
            data['matched'][status_data_item_id] = self.invert_merge_status(status_data['matched'][status_data_item_id])

        return data
        
    ###############################################################
    def forward_merge_status_of_path(self, status_data_from, status_data_to):
        data = self.get_status_of_path_empty()
        
        for status_data_item in status_data_from['not_matched']:
            data['not_matched'].append(status_data_item)

        for status_data_item in status_data_to['not_matched']:
            data['not_matched'].append(status_data_item)

        status_data_to_seen = []
        for status_data_item_id in status_data_from['matched'].keys():
            if status_data_item_id in status_data_to['matched'].keys():
                status_data_to_seen.append(status_data_item_id)
                data['matched'][status_data_item_id] = self.forward_merge_status(status_data_from['matched'][status_data_item_id],
                                                                                 status_data_to['matched'][status_data_item_id])
            else:
                data['matched'][status_data_item_id] = status_data_from['matched'][status_data_item_id]
                      
        for status_data_item_id in status_data_to['matched'].keys():
            if status_data_item_id in status_data_to_seen:
                print("skipped seen already:" + str(status_data_item_id))
            elif status_data_item_id in status_data_from['matched'].keys():
                data['matched'][status_data_item_id] = self.forward_merge_status(status_data_to['matched'][status_data_item_id],
                                                                                 status_data_from['matched'][status_data_item_id])
            else:
                data['matched'][status_data_item_id] = self.invert_merge_status(status_data_to['matched'][status_data_item_id])

        return data
    
    ###############################################################
    def add_different_files_to_db(self, cmd, base_paths, from_sel, to_sel, verbose):
        try:
            for res in self.tools.run_external_command_and_get_results(cmd, verbose):
                if(parameters['debug']):
                    self.tools.debug("DIFF: " + res + "\n")
                    self.tools.debug('\n'.join(base_paths))
                p_modified = re.compile('^M(.*)\s+(' + '|'.join(base_paths) + ')/(\S+)\s*$')
                p_added    = re.compile('^A(.*)\s+(' + '|'.join(base_paths) + ')/(\S+)\s*$')
                p_deleted  = re.compile('^D(.*)\s+(' + '|'.join(base_paths) + ')/(\S+)\s*$')
                m_modified = p_modified.match(res)
                m_added    = p_added.match(res)
                m_deleted  = p_deleted.match(res)
                if m_modified:
                    db[from_sel + '.changed'].append(m_modified.group(3))
                    db[to_sel   + '.changed'].append(m_modified.group(3))
                elif m_added:
                    db[to_sel + '.changed'].append(m_added.group(3))
                elif m_deleted:
                    db[from_sel + '.changed'].append(m_deleted.group(3))
                else:
                    db['not_matched'].append(res)
        except ToolException as e:
            raise SitExceptionAbort("Could add different files to db:\n" + str(e))

    ###############################################################
    def get_status_of_path_empty(self):
        data = {}
        #data['matched'] = []
        data['matched'] = {}
        data['not_matched'] = []
        return data
        
    ###############################################################
    def get_status_of_path(self, cmd, base_paths, verbose, debug):
        data = self.get_status_of_path_empty()
        
        try:
            for res in self.tools.run_external_command_and_get_results(cmd, verbose):
                if(debug):
                    self.tools.debug("DIFF: " + res)
                #    self.tools.debug('\n'.join(base_paths))
                p_str = '^(M|A|D|!)(.*)\s+(' + '|'.join(base_paths) + ')/(\S+)\s*$'
                p = re.compile(p_str)
                # if(debug):
                #     self.tools.debug("DIFFSTR: " + p_str)
                m  = p.match(res)
                if m:
                    status = m.group(1)
                    file = m.group(4)
                    if status == "!":
                        status = "D"
                    data['matched'][file] = status
                    if debug:
                        self.tools.debug("Matched:   " + status + " <=> " + file)
                else:
                    data['not_matched'].append(res)
                    if debug:
                        self.tools.debug("Unmatched: " + res)
        except ToolException as e:
            raise SitExceptionAbort("Could add different files to data:\n" + str(e))
        return data

    ###############################################################
    def convert_to_compare_folder_name(self, is_sandbox, branch_path, revision):
        if is_sandbox:
            return branch_path
        else:
            if revision == "":
                return re.sub('/', '__', branch_path)
            else:
                return re.sub('/', '__', branch_path) + "@" + revision
    
    ###############################################################
    def create_compare_path(self, db, compare_path, prefix, verbose, debug):
        for filepath in db[prefix + '.changed']:

            if debug:
                self.tools.status("Processing " + filepath)
            
            is_folder = False
            for folder in db[prefix + '.folders']:
                if folder == filepath:
                    is_folder = True
            if is_folder is True:
                self.tools.run_external_command('mkdir -p ' + compare_path + "/" + filepath, verbose) 
            else:
                filepath_list = filepath.split('/')
                filepath_list.pop() # get direcory path
                filepath_path = '/'.join(filepath_list)
                compare_filepath = compare_path + filepath
                compare_filepath_path = compare_path + filepath_path
                if(debug):
                    self.tools.debug("filepath: <" + filepath + ">")
                    self.tools.debug("filepath_path: <" + filepath_path + ">")
                    self.tools.debug("compare_filepath: <" + compare_filepath + ">")
                    self.tools.debug("compare_filepath_path: <" + compare_filepath_path + ">")
                    
                self.tools.run_external_command('mkdir -p ' + compare_filepath_path, verbose)
                if db[prefix + '.is_sandbox']:
                    link = self.get_link_if_path_or_file_is_symbolic(db[prefix + '.basepath'] + "/" + filepath, verbose)
                    if link is None:
                        self.tools.run_external_command('cp -P ' + db[prefix + '.basepath'] + "/" + filepath + ' ' + compare_filepath, verbose)
                    else:
                        self.tools.run_external_command('echo "link ' + link + '" > ' + compare_filepath, verbose)
                else:
                    # links are cat by svn to: "link <link_path>"
                    self.tools.run_external_command('svn cat -r ' + db[prefix + '.revision'] + ' ' + db[prefix + ".basepath"] + "/" + filepath + ' > ' + compare_filepath, verbose)
    
    ###############################################################
    def sit_diff(self, parameters):
        if(parameters['debug']):
            self.show()

        if len(parameters['branch_branch_pathfile']) > 3:
            raise SitExceptionDecode("Too many arguments (branch_branch_pathfile).")
        
        paths = None
        trace = {}

        try:
            if len(parameters['branch_branch_pathfile'])==3:
            # branch@r branch2@r pathfile            
                
                try:
                    paths_try = self.try_to_decode_branch_path(parameters['branch_branch_pathfile'][0], parameters['branch_branch_pathfile'][2],
                                                               parameters['branch_branch_pathfile'][1], parameters['branch_branch_pathfile'][2],
                                                               parameters['verbose'],
                                                               parameters['debug'])
            
                except SitExceptionDecode as e:
                    raise SitExceptionDecode("Could not decode 3 arguments <branch branch2 path> because:  \n  " + str(e))
                else:
                    paths = paths_try
            
            elif len(parameters['branch_branch_pathfile'])==2:
                # branch branch2/pathfile
            
                try:
                    paths_try = self.try_to_decode_branch_path(self.sandbox_branch_id,    parameters['branch_branch_pathfile'][1],
                                                               parameters['branch_branch_pathfile'][0], parameters['branch_branch_pathfile'][1],
                                                               parameters['verbose'],
                                                               parameters['debug'])
                
                except SitExceptionDecode as e:
                    trace[0] = "Could not decode <branch2 path> because:\n  " + str(e)
                else:
                    paths = paths_try
                
                try:
                    paths_try = self.try_to_decode_branch_path(parameters['branch_branch_pathfile'][0], self.relative_path,
                                                               parameters['branch_branch_pathfile'][1], self.relative_path,
                                                               parameters['verbose'],
                                                               parameters['debug'])
                except SitExceptionDecode as e:
                    trace[1] = "Could not decode <branch branch2> because:\n  " + str(e)
                else:
                    paths = paths_try

                if not paths:
                    raise SitExceptionDecode("Could not decode 2 arguments because:\n  " + trace[0] + "\n and \n  " + trace[1])
                
            elif len(parameters['branch_branch_pathfile'])==1:
                # branch/pathfile / branch
            
                try:
                    paths_try = self.try_to_decode_branch_path(self.sandbox_branch_id,                    parameters['branch_branch_pathfile'][0],
                                                               self.branch_type + ":" + self.branch_name, parameters['branch_branch_pathfile'][0],
                                                               parameters['verbose'],
                                                               parameters['debug'])
                
                except SitExceptionDecode as e:
                    trace[0] = "Could not decode <pathfile> because:\n  " + str(e)
                else:
                    paths = paths_try
                
                try:
                    paths_try = self.try_to_decode_branch_path(self.sandbox_branch_id,                  self.relative_path,
                                                               parameters['branch_branch_pathfile'][0], self.relative_path,
                                                               parameters['verbose'],
                                                               parameters['debug'])
                except SitExceptionDecode as e:
                    trace[1] = "Could not decode <branch> because:\n  " + str(e)
                else:
                    paths = paths_try
                        
                if not paths:
                    raise SitExceptionDecode("Could not decode 1 arguments because:\n  " + trace[0] + "\n and \n  " + trace[1])
                    
            else:
                # sandbox to head same branch for all

                try:
                    paths_try = self.try_to_decode_branch_path(self.sandbox_branch_id                                                 , self.relative_path,
                                                               self.branch_type + ":" + self.branch_name + "@" + self.sandbox_revision, self.relative_path,
                                                               parameters['verbose'],
                                                               parameters['debug'])
            
                except SitExceptionDecode as e:
                    raise SitExceptionDecode("Could not decode 0 arguments because:\n  " + str(e))
                else:
                    paths = paths_try
        except SitExceptionDecode as e:
            raise SitExceptionAbort("Could not decode arguments because:\n  " + str(e))
        else: # if no expection we can continue with diff
            if not paths:
                raise SitExceptionInternalFatalError("Unexpected empty paths variable ?!")
            else:


                db = {}
                db = paths.copy()
                db['from.changed'] = []
                db['to.changed'] = []
                db['from.folders'] = []
                db['to.folders'] = []
                db['not_matched'] = []
                
                if(parameters['debug']):
                    self.tools.debug('DB: ' + str(db))
                
                if db['from.is_sandbox'] and db['to.is_sandbox']:
                    raise SitExceptionAbort("Unexpected/Unsupported from and to is from sandbox")

                # -------
                self.tools.process("Detecting folders")

                db['from.folders'] = self.detect_folders(db['from.path'], db['from.revision'], parameters['verbose'])
                self.tools.status("Detected " + str(len(db['from.folders'])) + " folders in from")
                
                db['to.folders'] = self.detect_folders(db['to.path'], db['to.revision'], parameters['verbose'])
                self.tools.status("Detected " + str(len(db['to.folders'])) + " folders in to")

                # -------
                db['from.single_file'] = self.is_single_file(db['from.path'], db['from.revision'], parameters['verbose'])
                db['to.single_file'] = self.is_single_file(db['to.path'], db['to.revision'], parameters['verbose'])
                
                # p = re.compile('^\^')
                # m = p.match(paths['path1'])
                # if m:
                #     command = "svn ls --depth=infinity " + paths['path1'] + " | sed 's,/$,,g' | grep /$" + ' || test $? = 1; }'
                # else:
                #     command = "find " + paths['path1'] + " -type d | grep -v \.svn | grep -v ^\.$ | sed 's," + paths['path1'] + ",,g' | { grep -v '^$'" + ' || test $? = 1; }'
                # for res in self.tools.run_external_command_and_get_results(command, parameters['verbose']):
                #     db['from.folders'].append(res)
                # 
                # self.tools.status("Detected " + str(len(db['from.folders'])) + " folders in from")
                #     
                # m = p.match(paths['path2'])
                # if m:
                #     command = "svn ls --depth=infinity " + paths['path2'] + " | grep /$ | sed 's,/$,,g'"
                # else:
                #     command = "find " + paths['path2'] + " -type d | grep -v \.svn | grep -v ^\.$ | sed 's," + paths['path2'] + ",,g' | grep -v '^$'"
                # for res in self.tools.run_external_command_and_get_results(command, parameters['verbose']):
                #     db['to.folders'].append(res)
                #
                # self.tools.status("Detected " + str(len(db['to.folders'])) + " folders in to")

                
                # if local file - it might not be up to date => so we need to grap it via find as follows:
                # find -type d | grep -v \.svn | grep -v ^\.$
                
                # if from repo
                # svn ls --depth=infinity ^/project/sub_project/sub_sub_project/sub_sub_sub_project/trunk | grep /$
                


                self.tools.process("Finding differences")

                # sandbox => detect differences to actual revision ? + differences from actual revision to target => what about reverts double changes ? ignore them ?
                # do we need to find folders shouldn't we be able to detect them when calculating diffs ? at least that should be faster !
                # FIXXME: we should detect type for all files/folders when we detect a change ?!

                # FIXXXME: single file paths are wrong ! we need repo path not sandbox paths !!!
                
                if db['from.is_sandbox']:
                    if db['from.single_file']:
                        db['from.svndiff_path_base'] = self.relative_branch_root_url
                        db['from.svndiff_path'] = self.relative_branch_root_url + "/" + self.decode_pathfile_absolute_to_sandbox_root_path(db['from.path']) + "@" + self.sandbox_revision
                    else:
                        db['from.svndiff_path_base'] = self.relative_branch_root_url
                        db['from.svndiff_path'] = self.relative_branch_root_url + "/" + db['from.subpath'] + "@" + self.sandbox_revision
                        # self.decode_pathfile_relative_to_sandbox_root_path(self.relative_path)
                else:
                    db['from.svndiff_path_base'] = db['from.path']
                    db['from.svndiff_path'] = db['from.path'] + "@" + db['from.revision']

                if db['to.is_sandbox']:
                    if db['to.single_file']:
                        db['to.svndiff_path_base'] = self.relative_branch_root_url
                        db['to.svndiff_path'] = self.relative_branch_root_url + "/" + self.decode_pathfile_absolute_to_sandbox_root_path(db['to.path']) + "@" + self.sandbox_revision 
                    else:
                        db['to.svndiff_path_base'] = self.relative_branch_root_url
                        db['to.svndiff_path'] = self.relative_branch_root_url + "/" + db['to.subpath'] + "@" + self.sandbox_revision
                        # self.decode_pathfile_relative_to_sandbox_root_path(self.relative_path)
                else:
                    db['to.svndiff_path_base'] = db['to.path']
                    db['to.svndiff_path'] = db['to.path'] + "@" + db['to.revision']

                if(parameters['debug']):
                    self.tools.debug("====")
                    self.tools.debug("Sandbox root:       " + self.sandbox_root_path)
                    self.tools.debug("")
                    self.tools.debug("From Single file:   " + str(db['from.single_file']))
                    self.tools.debug("From path:          " + db['from.path'])
                    self.tools.debug("From basepath:      " + db['from.basepath'])
                    self.tools.debug("From subpath:       " + db['from.subpath'])
                    self.tools.debug("From svn path:      " + db['from.svndiff_path'])
                    self.tools.debug("")
                    self.tools.debug("To Single file:     " + str(db['to.single_file']))
                    self.tools.debug("To path:            " + db['to.path'])
                    self.tools.debug("To basepath:        " + db['to.basepath'])
                    self.tools.debug("To subpath:         " + db['to.subpath'])
                    self.tools.debug("To svn path:        " + db['to.svndiff_path'])
                    self.tools.debug("====")

                # =====================
                # 3 Cases are possible:
                # =====================
                #
                #  branch_from@r?  ->  branch_to@r?
                #
                # =====================
                # OR:
                #
                #  sandbox                      
                #    |                      
                #    v                      
                #  branch_from@r?  ->  branch_to@r?
                #
                # =====================
                # OR:
                #
                #                        sandbox
                #                          ^
                #                          |
                #  branch_from@r?  ->  branch_to@r?
                #
                # =====================
                #
                # svn status returns status branch -> sandbox (e.g. A => added from branch to sandbox)
                #
                    
                svn_diff_data = self.get_status_of_path_empty()
                if db['from.svndiff_path'] != db['to.svndiff_path']:
                    from_svndiff_path_flat = re.sub("^\^", self.repository_root, db['from.svndiff_path_base'])
                    to_svndiff_path_flat = re.sub("^\^", self.repository_root, db['to.svndiff_path_base'])
                    if(parameters['debug']):
                        self.tools.debug("from_svndiff_path_flat: " + from_svndiff_path_flat)
                        self.tools.debug("to_svndiff_path_flat: " + to_svndiff_path_flat)
                    cmd = 'svn diff --ignore-properties --summarize ' + db['from.svndiff_path'] + ' ' + db['to.svndiff_path']
                    svn_diff_data = self.get_status_of_path(cmd, [from_svndiff_path_flat, to_svndiff_path_flat, db['from.basepath'], db['to.basepath']], parameters['verbose'], parameters['debug'])

                svn_local_diff_data_from = self.get_status_of_path_empty()
                if db['from.is_sandbox']:
                    cmd = "svn status -q " + db['from.path']
                    svn_local_diff_data_from = self.get_status_of_path(cmd, [db['from.basepath']], parameters['verbose'], parameters['debug'])
                    # svn_local_diff_data_from = self.invert_merge_status_of_path(svn_local_diff_data_from_inverted)
                    
                svn_local_diff_data_to = self.get_status_of_path_empty()
                if db['to.is_sandbox']:
                    cmd = "svn status -q " + db['to.path']
                    svn_local_diff_data_to = self.get_status_of_path(cmd, [db['to.basepath']], parameters['verbose'], parameters['debug'])

                if(parameters['debug']):
                    self.tools.debug("====")
                    self.tools.debug("svn_local_diff_data_from: " + str(svn_local_diff_data_from))
                    self.tools.debug("svn_diff_data:            " + str(svn_diff_data))
                    self.tools.debug("svn_local_diff_data_to:   " + str(svn_local_diff_data_to))
                
                svn_diff_data_merged_temp = self.forward_merge_status_of_path(svn_local_diff_data_from, svn_diff_data)
                svn_diff_data_merged      = self.forward_merge_status_of_path(svn_diff_data_merged_temp, svn_local_diff_data_to)

                if(parameters['debug']):
                    self.tools.debug(str(svn_diff_data_merged))

                for status_data_item in svn_diff_data_merged['not_matched']:
                    db['not_matched'].append(status_data_item)

                for status_data_item_id in svn_diff_data_merged['matched'].keys():
                    p_m = re.compile('^M$')
                    p_a = re.compile('^A$')
                    p_d = re.compile('^D$')

                    f_m = p_m.match(svn_diff_data_merged['matched'][status_data_item_id])
                    f_a = p_a.match(svn_diff_data_merged['matched'][status_data_item_id])
                    f_d = p_d.match(svn_diff_data_merged['matched'][status_data_item_id])

                    if f_m:
                        db['from.changed'].append(status_data_item_id)
                        db['to.changed'].append(status_data_item_id)
                    elif f_a:
                        db['from.changed'].append(status_data_item_id)
                    elif f_d:
                        db['to.changed'].append(status_data_item_id)
                    else:
                        raise SitExceptionAbort("Could not match status of " + status_data_item_id + ": <" + svn_diff_data_merged['matched'][status_data_item_id] + ">")

                # ------                    
                self.tools.status("Detected " + str(len(db['from.changed'])) + " changed elements in from")
                self.tools.status("Detected " + str(len(db['to.changed'])) + " changed elements in to")
                self.tools.status("Detected " + str(len(db['not_matched'])) + " not mached elements")
                                  
                if(parameters['debug']):
                    # self.tools.debug "\nModified:\n" + '\n'.join(modified)
                    # self.tools.debug "\nAdded:\n" + '\n'.join(added)
                    # self.tools.debug "\nDeleted:\n" + '\n'.join(deleted)
                    # self.tools.debug "\nUnmatched:\n" + '\n'.join(unmatched)

                    self.tools.debug("\nFrom Folders:\n" + '\n'.join(db['from.folders']))
                    self.tools.debug("\nTo Folders:\n" + '\n'.join(db['to.folders']))
                    
                    self.tools.debug("\nFrom:\n"      + '\n'.join(db['from.changed']))
                    self.tools.debug("\nTo:\n"        + '\n'.join(db['to.changed']))
                    self.tools.debug("\nUnmatched:\n" + '\n'.join(db['not_matched']))

                if (len(db['from.changed']) == 0) and (len(db['to.changed']) == 0):
                    self.tools.status("No changes detected between paths <" + db['from.path'] + "@" + db['from.revision'] + "> and <" + db['to.path'] + "@" + db['to.revision'] + ">.")
                else:
                    # ------------------
                    self.tools.process("Showing differences")
                    
                    datetime = time.strftime("%Y.%m.%d.%H_%M_%S")

                    compare_base_folder = parameters['diff_dir'] + '/sit.diff.' + datetime
                    compare_from_path = compare_base_folder + '/from:' + self.convert_to_compare_folder_name(paths['from.is_sandbox'], paths['from.branch'], paths['from.revision'])  + '/'
                    compare_to_path   = compare_base_folder + '/to:' + self.convert_to_compare_folder_name(paths['to.is_sandbox'], paths['to.branch'], paths['to.revision']) + '/'

                    self.tools.run_external_command('mkdir -p ' + compare_from_path, parameters['verbose'])
                    self.tools.run_external_command('mkdir -p ' + compare_to_path, parameters['verbose'])

                    diff_tool = self.cfg_difftool
                    if parameters['diff_tool'][0]:
                        diff_tool = parameters['diff_tool'][0]
                    
                    if diff_tool == "kdiff3":
                        if (len(db['from.changed']) == 0) or (len(db['to.changed']) == 0):
                            self.tools.run_external_command('touch ' + compare_from_path + ".sitdiff.ignoreme", parameters['verbose'])
                            self.tools.run_external_command('touch ' + compare_to_path + ".sitdiff.ignoreme", parameters['verbose'])

                    # ------------------
                    self.create_compare_path(db, compare_from_path, "from", parameters['verbose'], parameters['debug'])
                    self.create_compare_path(db, compare_to_path, "to", parameters['verbose'], parameters['debug'])
                    
                    # ------------------
                    if diff_tool == "diff":
                        self.tools.status("To Path Tree")
                        self.tools.run_external_command_ignore_status_and_print("find " + compare_to_path + " | sort", parameters['verbose'])
#                        self.tools.run_external_command_ignore_status_and_print("tree -n " + compare_to_path, parameters['verbose'])
                        self.tools.status("From Path Tree")
                        self.tools.run_external_command_ignore_status_and_print("find " + compare_from_path + " | sort", parameters['verbose'])
#                        self.tools.run_external_command_ignore_status_and_print("tree -n " + compare_from_path, parameters['verbose'])
                        self.tools.status("Differences")
                        command = diff_tool + ' -s -r ' + compare_to_path + ' ' + compare_from_path
                    else:
                        command = diff_tool + ' ' + compare_to_path + ' ' + compare_from_path
                    self.tools.run_external_command_ignore_status_and_print(command, parameters['verbose'])

                    # do not delete in case of debug !
                    if not parameters['debug']:
                        self.tools.run_external_command('rm -rf ' + compare_base_folder, parameters['verbose'])


    
    ###############################################################
    def sit_status(self, parameters):
        if(parameters['debug']):
            self.show()
        # print(path)
    
        if not self.is_equal_to_relative_path(parameters['path']):
            if not self.is_repository_url_existing(os.path.abspath(os.getcwd() + '/' + parameters['path']), parameters['verbose']):
                raise SitExceptionParseError("The given path <" + parameters['path'] + "> is not an svn path")

        db = self.get_status(parameters['path'], parameters['verbose'])
    
        if len(db['changed']):
            self.tools.status("Changed")
            for i in sorted (db['changed'].keys()):
                print("  %-10s %s" % (db['changed'][i], i))
    
        if len(db['untracked']):
            if len(db['untracked']):
                print("")
            self.tools.status("Untracked")
            for i in sorted (db['untracked'].keys()):
                print("  %-10s %s" % (db['untracked'][i], i))

    ###############################################################
    def get_status(self, path, verbose):
        command = 'svn status ' + path + ' 2>/dev/null'
        lines = self.tools.run_external_command_and_get_results(command, verbose)

        db = {}
        db['changed'] = {}
        db['untracked'] = {}
    
        for line in lines:

            # svn status:
            # 1234567 <version> <Name>
            # 1 ... A added
            #       D deleted
            #       M modified
            #       R replaced
            #       C conflict
            #       X from external source
            #       I ignored
            #       ? not version controlled
            #       ! missing object
            #       ~ specific type changed
            # 2 ... M property changed
            #       C conflict
            # 3 ... L locked object
            # 4 ... + add element including history 
            # 5 ... S from different branch
            # 6 ... K locked in this sandbox
            #       O locked by other user => only shown if --show_updated is added
            #       T locked in this sandbox but got stolen, locked in repo => only shown if --show_updated is added
            #       B locked in this sandbox but got stolen, not locked in repo => only shown if --show_updated is added
            # 7 ... * new version available in repo
            # <version> is shown if --show_updated or --verbose is used
    
            p = re.compile(r'^(\?)\s+(.+)$')
            m = p.match(line)
            if m:
                db['untracked'][str(m.group(2))] = str(m.group(1))
    
            # p = re.compile(r'^([^\?])\s+(.+)$')
            # m = p.match(line)
            # if m:
            #     db['changed'][str(m.group(2))] = str(m.group(1))

            p = re.compile(r'^(([^\?]| )([^\?]| )([^\?]| )([^\?]| )([^\?]| )([^\?]| )([^\?]| ))\s+(.+)$')
            m = p.match(line)
            if m:
                db['changed'][str(m.group(9))] = " " + str(m.group(1))

        return db
        
    ###############################################################
    def sit_update(self, parameters):
        if(parameters['debug']):
            self.show()
            
        pathfile = self.pathfile_to_abs_pathfile(parameters['path'])

        if self.is_pathfile_within_sandbox_root_path(pathfile):
            if not parameters['ignore_modified_sandbox']:
                if self.is_sandbox_modified(parameters['verbose']):
                    raise SitExceptionAbort("Aborting operation. There are uncommitted changes in sandbox.")
            self.do_update(parameters['verbose'])  
        else:
            raise SitExceptionAbort("Aborting operation. Path/file not within sandbox. <" + parameters['path'] + ">")

    ###############################################################
    def do_update(self, verbose):
        self.tools.process("Updating")
        self.tools.run_external_command('svn update ' + self.get_relative_path_to_root(), verbose) # self.sandbox_root_path)
        
    ###############################################################
    def sit_merge(self, parameters):
        if(parameters['debug']):
            self.show()

        if self.is_sandbox_modified(parameters['verbose']):
            db = self.get_status(self.sandbox_root_path, parameters['verbose'])
            self.tools.status("Changed not committed files detected:")
            for i in sorted (db['changed'].keys()):
                print("  %-10s %s" % (db['changed'][i], i))
                
        if not parameters['ignore_modified_sandbox']:
            if self.is_sandbox_modified(parameters['verbose']):
                raise SitExceptionAbort("Aborting operation. There are uncommitted changes in sandbox.")
                
        branch_repository_url, branch_selected = self.select_branch_by_name(parameters['branch'][0], parameters['branch_type'][0], parameters['verbose'])


        if not self.cfg_disable_update_before_merge:
            if not self.cfg_auto_update_before_merge:
                
                tbd = 1
                #try:
                #    revision = self.tools.select_from_list("What revision to branch from?", choice)
                #except ToolException as e:
                #    raise SitExceptionAbort("Aborting due selection error.\n" + str(e))
                    
            self.do_update(parameters['verbose'])
                
        self.do_merge(branch_repository_url, "", parameters['verbose'])

    ###############################################################
    def do_merge(self, path, revision, message, verbose=False):
        self.tools.process("Merging from " + path)
        command = "svn merge " + path + ' ' + revision + ' ' + self.get_relative_path_to_root()
        #self.tools.run_external_command(command, verbose) # does not work with interactive IO ! 
        try:
            self.tools.run_external_command_no_print(command, verbose)
        except ToolException as e:
            raise SitExceptionAbort("Detected issue during merge:\n" + str(e))
            
    ###############################################################
    def get_new_stash_branch_name(self, name):
        # ^/stashes/<user>.<stash_name>.<branch_type>.<branch_name>

        stash_base_path = self.project_path + '/' + self.default_stash_folder + "/"

        # find best match for unidentified name
        stashes = []
        stashes_id = []
        stashes_num_max_id = -1
        for res in self.tools.run_external_command_and_get_results('svn ls ' + stash_base_path):
            p = re.compile('^(' + os.environ['USER'] + self.default_stash_separator + '([^' + self.default_stash_separator + ']+)' + self.default_stash_separator + ".+)$")
            m = p.match(res)
            if m:
                stashes.append(m.group(1))
                stashes_id.append(m.group(2))
                p2 = re.compile('^(\d+)$')
                m2 = p2.match(m.group(2))
                if m2:
                    if int(m2.group(1)) > stashes_num_max_id:
                        stashes_num_max_id = int(m2.group(1))

        if name:
            p = re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')
            m = p.match(name)
            if m:
                name_selected = name
            else:
                raise SitExceptionDecode("Unsupported character found in stash name. Only alphanumeric or _ is allowed, and it must not start with a number: <" + name + ">")      
        else:
            raise SitExceptionSelect("No name for the stash is given.") 
            # name_selected = str(stashes_num_max_id + 1)
        stash_branch_name = stash_base_path + os.environ['USER'] + self.default_stash_separator + name_selected + self.default_stash_separator
        stash_branch_name = stash_branch_name + self.branch_type
        stash_branch_name = stash_branch_name + self.default_stash_separator
        stash_branch_name = stash_branch_name + self.branch_name
        stash_branch_name = stash_branch_name + self.default_stash_separator
        stash_branch_name = stash_branch_name + time.strftime("%Y.%m.%d.%H_%M_%S") 

        if name_selected in stashes_id:
            raise SitExceptionSelect("Stash name <" + name_selected + "> already exists")

        return stash_branch_name, name_selected

    ###############################################################
    def sit_stash_push(self, parameters):
        if(parameters['debug']):
            self.show()

        # FIXME: implement selection of path/files to stash !
        
        # do stash:
        if self.is_sandbox_modified(parameters['verbose']):
            stash_branch_url, name_selected = self.get_new_stash_branch_name(parameters['name'])
            
            # FIXME: add message ?
            commit_path = self.get_relative_path_to_root()
            branch_url = self.relative_branch_root_url

            if parameters['auto_message']:
                # FIXME: revision in name !?
                branch_message = "Stash Push (create branch): from <" + branch_url + '> to <'  + stash_branch_url + '> using stash reference name <' + name_selected + '>'
            else: # use svn edit command if none given
                branch_message = None
                
            try:
                branch_revision = self.do_branch("branch_name", stash_branch_url, branch_message, parameters['verbose'])
                self.do_checkout(stash_branch_url, 'HEAD', parameters['verbose'])
                commit_message = "Stash Push (commit all modifications): from <" + branch_url + "@" + branch_revision + '> to <'  + stash_branch_url + '> using stash reference name <' + name_selected + '>' 
                self.do_commit(commit_path, commit_message, parameters['verbose'])
                self.do_checkout(branch_url, branch_revision, parameters['verbose'])
            except SitException as e:
                # FIXME: implement cleanup, show history ?! show commands that were executed until this point ?!
                raise SitException("Detected exception\n" + str(e))
            else:
                self.tools.status("Created stash <" + name_selected + ">")
            #try:
            #    sit_branch()
            #    sit_checkout()
            #except:
            # revert state ?
            #else:
        else:
            raise SitExceptionAbort("Aborting operation. No modified files to stash found")

        # check if stash name is ok and not used - stash to branches ?! or add own stash folder ? would be better to do not mix up stuff
        # keep stashes in parallel to trunk/branches/etc. inside stashes we have the same structure branches/branch.stash.date.rev.user.name
        # cp branch/tag etc. to stash at correct version, add rev in name ???
        # switch
        # commit all/selected changed files ? Support subfolders ?
        # 
        # drop:
        # remove existing stash
        #
        # apply:
        # merge with stash branch PREV to HEAD

    ###############################################################
    def get_stash_branches(self, username, verbose):
        stash_base_path = self.project_path + '/' + self.default_stash_folder + "/"

        command = 'svn ls ' + stash_base_path
        stashes = {}
        
        for stash_branches in self.tools.run_external_command_and_get_results(command, verbose):

            p = re.compile('^' + username + self.default_stash_separator +
                           '([^' + self.default_stash_separator + ']+)' + self.default_stash_separator +
                           '([^' + self.default_stash_separator + ']+)' + self.default_stash_separator +
                           '([^' + self.default_stash_separator + ']+)' + self.default_stash_separator +
                           '([^' + self.default_stash_separator + ']+)' +
                           '/$')
            
            m = p.match(stash_branches)
            if m:
                datetime = m.group(4)
                branch_name = m.group(3)
                branch_type = m.group(2)
                stash_name = m.group(1)

                stash_url = stash_base_path + stash_branches
                stashes[datetime + "_" + stash_name] = {'stash_url':  stash_url, 'datetime': datetime, 'stash_name': stash_name, 'branch_name': branch_name, 'branch_type': branch_type}

        stashes_extended = {}
        identifier = 0
        for stash_id in sorted(stashes.keys(), reverse=True):
            data = stashes[stash_id]
            p2 = re.compile('^(\d+)\.(\d+)\.(\d+)\.(\d+)_(\d+)_(\d+)$')
            m2 = p2.match(stashes[stash_id]['datetime'])
            if m2:
                datetime_formatted = m2.group(4) + ':' + m2.group(5) + ':' + m2.group(6) + ' ' + m2.group(3) + '.' + m2.group(2) + '.' + m2.group(1)
            else:
                datetime_formatted = datetime

            data['id'] = identifier
            data['datetime_formatted'] = datetime_formatted
            
            stashes_extended[identifier] = data

            identifier = identifier + 1

        return stashes_extended
        
        
    ###############################################################
    def sit_stash_list(self, parameters):
        if(parameters['debug']):
            self.show()
            
        # list / show stashes:
        # difference in revisions ?
        # show list

        # FIXME: should we over simplify stashing ? just sort by date and number => number = sorted list => like in git ?
        # username should be selectable ! then we can move changes to other people if necessary
        # + add larger description to stash + name ?! => move to message ???

        # stashes/username.date.
        
        #if not branch:
        #    branch = self.branch_name
        #
        # branch_repository_url, branch_selected = self.select_branch_by_name(branch, branch_type, parameters['verbose'])

        stashes = self.get_stash_branches(parameters['username'][0], parameters['verbose'])

        for identifier in sorted(stashes.keys()):
            data = stashes[identifier]
            print('[' + str(data['id']) + '] ' + data['datetime_formatted'] + ' ' + data['stash_name'] + ' ' + data['branch_type'] + '/' + data['branch_name'] + ' ' + data['stash_url'])

            
    ###############################################################
    def sit_stash_drop(self, parameters):
        if(parameters['debug']):
            self.show()
       
        stashes = self.get_stash_branches(parameters['username'][0], parameters['verbose'])
        if not stashes:
            raise SitExceptionAbort("Aborting operation. No stashes to drop available.")
        
        if parameters['name']:
            p = re.compile('^(\d+)$')
            m = p.match(parameters['name'])
            if m:
                identifier = int(m.group(1))
                if identifier in stashes.keys():
                    data = stashes[identifier]
                    stash_url = data['stash_url']
                    self.do_remove_branch_stash(identifier, stash_url, parameters['auto_message'], parameters['verbose'])
                else:
                    raise SitExceptionAbort("Aborting operation. There is no stash to drop available with the identifier: <" + parameters['name'] + ">")
            else:
                stash_url = None
                for identifier in sorted(stashes.keys()):
                    data = stashes[identifier]
                    stash_name = data['stash_name']
                    
                    if stash_url is None: # loop until found
                        if parameters['name'] == stash_name: # apply if matches
                            stash_url = data['stash_url']
                            self.do_remove_branch_stash(identifier, stash_url, parameters['auto_message'], parameters['verbose'])
                            
                if stash_url is None: # if we do not find anything then error out
                    raise SitExceptionAbort("Aborting operation. There is no stash to drop found with the name: <" + parameters['name'] + ">")
        else:
            identifier = 0
            if stashes[identifier]:
                data = stashes[identifier]
                stash_url = data['stash_url']
                self.do_remove_branch_stash(identifier, stash_url, parameters['auto_message'], parameters['verbose'])
            else:
                raise SitExceptionAbort("Aborting operation. There is no stash to drop available")

    ###############################################################
    def do_remove_branch_stash(self, identifier, path, auto_message, verbose=False):
        if auto_message:
            remove_message = self.auto_message_prefix + "removing stash " + str(identifier) + " which is: " + path
        else:
            remove_message = None
        self.do_remove_branch(path, remove_message, verbose)

    ###############################################################
    def do_remove_branch(self, path, message, verbose):
        if message:
            command = "svn rm " + path + " -m \'" + message + "\'"
        else:
            command = "svn rm " + path
        self.tools.run_external_command(command, verbose)
        
    ###############################################################
    def sit_stash_apply(self, parameters):
        if(parameters['debug']):
            self.show()
        
        if not parameters['ignore_modified_sandbox']:
            if self.is_sandbox_modified(parameters['verbose']):
                raise SitExceptionAbort("Aborting operation. There are uncommitted changes in sandbox.")
       
        stashes = self.get_stash_branches(parameters['username'][0], parameters['verbose'])
        
        if parameters['name']:
            p = re.compile('^(\d+)$')
            m = p.match(parameters['name'])
            if m:
                identifier = int(m.group(1))
                if stashes[identifier]:
                    data = stashes[identifier]
                    stash_url = data['stash_url']
                    self.do_merge_stash(stash_url, parameters['verbose'])
                else:
                    raise SitExceptionAbort("Aborting operation. There is no stash to apply available with the identifier: <" + parameters['name'] + ">")
            else:
                stash_url = None
                for identifier in sorted(stashes.keys()):
                    data = stashes[identifier]
                    stash_name = data['stash_name']
                    
                    if stash_url is None: # do only if not found already
                        if parameters['name'] == stash_name: # if name matches
                            stash_url = data['stash_url']
                            self.do_merge_stash(stash_url, parameters['verbose'])
                if stash_url is None: # if none is found error out
                    raise SitExceptionAbort("Aborting operation. There is no stash to apply found with the name: <" + parameters['name'] + ">")
        else:
            identifier = 0
            if stashes[identifier]:
                data = stashes[identifier]
                stash_url = data['stash_url']
                self.do_merge_stash(stash_url, parameters['verbose'])
            else:
                raise SitExceptionAbort("Aborting operation. There is no stash to apply available")

    ###############################################################
    def do_merge_stash(self, stash_url, verbose):
        revision = self.do_get_head_revision(stash_url, verbose)
        revision_option = " -r " + str(int(revision)-1) + ":" + revision
        try:
            self.do_merge(stash_url, revision_option, verbose)
        except SitException as e:
            raise SitExceptionAbort("Merge failed\n" + str(e))
        else:
            #self.tools.process("Auto remove merge info")
            command = 'svn revert ' + self.get_relative_path_to_root()
            self.tools.run_external_command_no_print(command, verbose)

    ###############################################################
    def do_get_head_revision(self, path, verbose=False):
        revision = None
        command = "svn info --show-item last-changed-revision " + path
        for line in self.tools.run_external_command_and_get_results(command, verbose):
            if revision is None:
                p = re.compile('^(\d+)$')
                m = p.match(line)
                if m:
                    revision = str(m.group(1))
                else:
                    raise SitExceptionAbort("Aborting operation. Could not match result to number from <" + line + "> for command <" + command + ">")
            else:
                raise SitExceptionAbort("Aborting operation. Multiple results unexpected from <" + command + "> got <" + revision + " and <" + line + ">")
        return revision
                
###############################################################
# def sit_ignore(self, parameters):
# update ignores from common folder

###############################################################
# def sit_clone(self, parameters):
# clone / checkout repo

###############################################################
# def sit_find(self, parameters):
# find files
# svn list --depth infinity | grep ...        revision ?

###############################################################
# def sit_setup(self, parameters):
# setup common folder structure


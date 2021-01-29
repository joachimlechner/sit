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
    branch_type = "" 
    branch_name = ""
    branch_types = ['trunk', 'branches', 'tags', 'releases']
    default_branch_type = 'branches'
    trunk_names = ['trunk', 'master']
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
            p = re.compile('\^/(' + '|'.join(self.branch_types) + ')/([^/]+)')
            m = p.match(self.relative_url)
            if m:
                self.branch_type = str(m.group(1))
                self.branch_name = str(m.group(2))
            else:
                p = re.compile('\^/trunk(/|)')
                m = p.match(self.relative_url)
                if m:
                    self.branch_type = "trunk"
                    self.branch_name = "trunk"
                else:
                    raise SitExceptionParseError("Cannot match branch type/name in <" + self.relative_url + ">")

    ###############################################################
    def show(self):
        if self.sandbox_is_svn_path:
            print("Path:                   " + self.sandbox_actual_path) 
            print("Relative path:          " + self.relative_path)
            print("Relative URL:           " + self.relative_url)
            print("Relative Branch URL:    " + self.relative_branch_root_url)
            print("Repository URL:         " + self.repository_url)
            print("Repository Root:        " + self.repository_root)
            print("Repository Revision:    " + self.repository_revision)
            print("Working copy root path: " + self.sandbox_root_path)
            print("Sandbox Revision:       " + self.sandbox_revision)
            print("branch type:            " + self.branch_type)
            print("branch name:            " + self.branch_name)           
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
    def get_branch_repository_url(self, branch_name, branch_type):
        if branch_name in self.trunk_names:
            return '^/' + self.default_trunk_name
        else:
            return '^/' + branch_type + '/' + branch_name

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
    def is_repository_url_existing(self, repository_url):
       if ''.join(self.tools.run_external_command_and_get_results('{ svn info ' + repository_url + ' 2>/dev/null || test $? = 1; }')) == "":
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
        self.tools.run_external_command("svn add " + ' '.join(parameters['options']), parameters['verbose'])

    ###############################################################
    def sit_commit(self, parameters):
        self.do_commit(parameters['path'], ' '.join(parameters['message']), parameters['verbose'])
        
    ###############################################################
    def do_commit(self, path, message, verbose):
        if message:
            self.tools.run_external_command("svn commit " + path + " -m \'" + message + '\'', verbose)
        else:
            self.tools.run_external_command("svn commit " + path, verbose)

        
    ###############################################################
    def sit_reset(self, parameters):
        self.tools.run_external_command("svn revert -R " + parameters['path'], parameters['verbose'])

    ###############################################################
    def sit_branch(self, parameters):
        
        if not parameters['branch']:
            # list branches
            for i_branch_type in self.branch_types:
                print(i_branch_type + ':')
                if i_branch_type == "trunk":
                    command = 'svn ls ' + self.repository_root + '| grep trunk/'
                else:
                    command = 'svn ls ' + self.repository_root + '/' + i_branch_type

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
            # hence svn info shows the revsion from last update only
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
            else: # use svn edit command if none given
                branch_message = None
                
            self.do_branch(branch, branch_to, parameters['auto_message'], branch_message, parameters['verbose'])

    ###############################################################
    def do_branch(self, branch, branch_to_url, auto_message, message, verbose):
            if self.is_repository_url_existing(branch_to_url):
                raise SitExceptionAbort("Aborting operation. There is already a branch with the same name existing <" + branch_to_url + ">.")

            if self.repository_revision == self.sandbox_revision:
                if (message is None) and auto_message:
                    message = self.auto_message_prefix + "creating branch " + branch + " (" + branch_to_url + ") from " + self.relative_branch_root_url + "@" + self.repository_revision
                self.svn_copy(self.relative_branch_root_url, self.repository_revision, branch_to_url, message, verbose)
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

                if (message is None) and auto_message:
                    message = self.auto_message_prefix + "creating branch " + branch + " (" + branch_to_url + ") from " + self.relative_branch_root_url + "@" + revision
                self.svn_copy(self.relative_branch_root_url, revision, branch_to_url, message, verbose)
                return revision
            
    ###############################################################
    def svn_copy(self, branch_from_url, branch_from_revision, branch_to_url, message, verbose):
        if message:
            command = 'svn copy -r ' + branch_from_revision + ' ' + branch_from_url + ' ' + branch_to_url + " -m \'" + message + "\'"
        else:
            command = 'svn copy -r ' + branch_from_revision + ' ' + branch_from_url + ' ' + branch_to_url
        self.tools.run_external_command(command, verbose)
        
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
                command = 'svn ls ' + self.repository_root + '| grep trunk/'
            else:
                command = 'svn ls ' + self.repository_root + '/' + i_branch_type

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
        p = re.compile('^(' + self.sandbox_root_path + ')(.*)')
        m = p.match(pathfile_decoded)
        if m:
            return m.group(2)
        else:
            raise SitExceptionDecode("Path/File not within in repository/sandbox area <" + pathfile_decoded + "> at sandbox root <" + self.sandbox_root_path + ">")

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
    def decode_to_branch_at_revision(self, branch, pathfile, verbose, debug):
        # tags:branch_name@<revision_number|prev|head>

        if branch == self.sandbox_branch_id:
            pathfile_decoded = self.decode_pathfile_relative_to_sandbox_root_path(pathfile)
            return self.sandbox_root_path + "/" + pathfile_decoded
        else:
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
                  
                return repository_branch_url_pathfile + '@' + revision
            else:
                raise SitExceptionDecode("Could not match to be any branch specification <" + branch + ">")

        
    ###############################################################
    def try_to_decode_branch_path(self, from_branch, from_path, to_branch, to_path, verbose, debug):
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
            paths_try['path1'] = path1_try
            paths_try['path2'] = path2_try
            return paths_try

    def get_svnbasepath(self, path):
        p = re.compile('^(.+)/@(\d+)$')
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

    def get_svnbaserevision(self, path):
        path_split = path.split('@')
        if len(path_split)>=2:
            return path_split[1]
        else:
            return ''

    def is_file_from_sandbox_folder(self, path):
        p = re.compile('^' + self.sandbox_root_path)
        m = p.match(path)
        if m:
            return True
        else:
            return False

    ###############################################################
    def sit_diff(self, parameters):

        if len(parameters['branch_branch_pathfile']) > 3:
            raise SitExceptionDecode("Too many arguments (branch_branch_pathfile).")
        
        paths = None
        trace = {}

        try:
            if len(parameters['branch_branch_pathfile'])==3:
            # branch branch2 pathfile            
                
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
                    paths_try = self.try_to_decode_branch_path(self.sandbox_branch_id,    self.relative_path,
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
                    paths_try = self.try_to_decode_branch_path(self.sandbox_branch_id,                    self.relative_path,
                                                               self.branch_type + ":" + self.branch_name, self.relative_path,
                                                               parameters['verbose'],
                                                               parameters['debug'])
            
                except SitExceptionDecode as e:
                    raise SitExceptionDecode("Could not decode 0 arguments because:\n  " + str(e))
                else:
                    paths = paths_try
        except SitExceptionDecode as e:
            raise SitExceptionAbort("Could not decode arguments because:\n  " + str(e))
        else:
            if not paths:
                raise SitExceptionInternalFatalError("Unexpected empty paths variable ?!")
            else:
                if(parameters['debug']):
                    print(paths['path1'])
                    print(paths['path2'])

                repository_from_path = self.get_svnbasepath(paths['path1'])
                repository_from_revision = self.get_svnbaserevision(paths['path1'])
                repository_to_path = self.get_svnbasepath(paths['path2'])
                repository_to_revision = self.get_svnbaserevision(paths['path2'])

                db = {}
                db['from'] = []
                db['to'] = []
                db['not_matched'] = []

                for res in self.tools.run_external_command_and_get_results('svn diff --ignore-properties --summarize ' + paths['path1'] + ' ' + paths['path2'], parameters['verbose']):
                    p_modified = re.compile('^M(.*)\s+(' + repository_from_path + '|' + repository_to_path + ')/(\S+)$')
                    p_added    = re.compile('^A(.*)\s+(' + repository_from_path + '|' + repository_to_path + ')/(\S+)$')
                    p_deleted  = re.compile('^D(.*)\s+(' + repository_from_path + '|' + repository_to_path + ')/(\S+)$')
                    m_modified = p_modified.match(res)
                    m_added    = p_added.match(res)
                    m_deleted  = p_deleted.match(res)
                    if m_modified:
                        db['from'].append(m_modified.group(3))
                        db['to'].append(m_modified.group(3))
                    elif m_added:
                        db['to'].append(m_added.group(3))
                    elif m_deleted:
                        db['from'].append(m_deleted.group(3))
                    else:
                        db['not_matched'].append(res)

                if(parameters['debug']):
                    # print "\nModified:\n" + '\n'.join(modified)
                    # print "\nAdded:\n" + '\n'.join(added)
                    # print "\nDeleted:\n" + '\n'.join(deleted)
                    # print "\nUnmatched:\n" + '\n'.join(unmatched)
                    
                    print("\nFrom:\n" + '\n'.join(db['from']))
                    print("\nTo:\n" + '\n'.join(db['to']))
                    print("\nUnmatched:\n" + '\n'.join(db['not_matched']))
                    #print repository_from_path
                    #print repository_to_path

                datetime = time.strftime("%Y.%m.%d.%H_%M_%S")

                compare_base_folder = parameters['diff_dir'] + '/sit.diff.' + datetime 
                compare_from_path = compare_base_folder + '/from/'
                compare_to_path   = compare_base_folder + '/to/'

                self.tools.run_external_command('mkdir -p ' + compare_from_path, parameters['verbose'])
                self.tools.run_external_command('mkdir -p ' + compare_to_path, parameters['verbose'])
                if parameters['diff_tool'] == "kdiff3":
                    self.tools.run_external_command('touch ' + compare_from_path + "/.sitdiff.ignoreme", parameters['verbose'])
                    self.tools.run_external_command('touch ' + compare_to_path + "/.sitdiff.ignoreme", parameters['verbose'])

                for filepath in db['from']:
                    filepath_list = filepath.split('/')
                    filepath_list.pop()
                    filepath_path = '/'.join(filepath_list)
                    compare_filepath = compare_from_path + '/' + filepath
                    compare_filepath_path = compare_from_path + '/' + filepath_path
                    self.tools.run_external_command('mkdir -p ' + compare_filepath_path, parameters['verbose'])
                    if self.is_file_from_sandbox_folder(repository_from_path):
                        self.tools.run_external_command('cat ' + repository_from_path + '/' + filepath + ' > ' + compare_filepath, parameters['verbose'])
                    else:
                        self.tools.run_external_command('svn cat -r ' + repository_from_revision + ' ' + repository_from_path + '/' + filepath + ' > ' + compare_filepath, parameters['verbose'])

                for filepath in db['to']:
                    filepath_list = filepath.split('/')
                    filepath_list.pop()
                    filepath_path = '/'.join(filepath_list)
                    compare_filepath = compare_to_path + '/' + filepath
                    compare_filepath_path = compare_to_path + '/' + filepath_path
                    self.tools.run_external_command('mkdir -p ' + compare_filepath_path, parameters['verbose'])
                    if self.is_file_from_sandbox_folder(repository_to_path):
                        self.tools.run_external_command('cat ' + repository_to_path + '/' + filepath + ' > ' + compare_filepath, parameters['verbose'])
                    else:
                        self.tools.run_external_command('svn cat -r ' + repository_to_revision + ' ' + repository_to_path + '/' + filepath + ' > ' + compare_filepath, parameters['verbose'])

                command = '{ ' + parameters['diff_tool'][0] + ' ' + compare_from_path + ' ' + compare_to_path + ' || test $? = 1; }'
                self.tools.run_external_command(command, parameters['verbose'])

                # do not delete in case of debug !
                if not parameters['debug']:
                    self.tools.run_external_command('rm -rf ' + compare_base_folder, parameters['verbose'])
    
    ###############################################################
    def sit_status(self, parameters):
        # print(path)
    
        if not self.is_equal_to_relative_path(parameters['path']):
            if not self.is_repository_url_existing(os.path.abspath(os.getcwd() + parameters['path'])):
                raise SitExceptionParseError("The given path <" + parameters['path'] + "> is not an svn path")

        command = 'svn status ' + parameters['path'] + ' 2>/dev/null'
        lines = self.tools.run_external_command_and_get_results(command, parameters['verbose'])
        
        untracked = {}
        changed = {}
    
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
                untracked[str(m.group(2))] = str(m.group(1))
    
            p = re.compile(r'^([^\?])\s+(.+)$')
            m = p.match(line)
            if m:
                changed[str(m.group(2))] = str(m.group(1))
    
        if len(changed):
            print("Changed")
            for i in sorted (changed.keys()):
                print("  %-10s %s" % (changed[i], i))
    
        if len(untracked):
            if len(changed):
                print("")
            print("Untracked")
            for i in sorted (untracked.keys()):
                print("  %-10s %s" % (untracked[i], i))


    ###############################################################
    def sit_update(self, parameters):
        pathfile = self.pathfile_to_abs_pathfile(parameters['path'])

        if self.is_pathfile_within_sandbox_root_path(pathfile):
            if not parameters['ignore_modified_sandbox']:
                if self.is_sandbox_modified(parameters['verbose']):
                    raise SitExceptionAbort("Aborting operation. There are uncommitted changes in sandbox.")
                  
            self.tools.run_external_command('svn update ' + self.get_relative_path_to_root(), parameters['verbose']) # self.sandbox_root_path)
        else:
            raise SitExceptionAbort("Aborting operation. Path/file not within sandbox. <" + parameters['path'] + ">")

    ###############################################################
    def sit_merge(self, parameters):
        if not parameters['ignore_modified_sandbox']:
            if self.is_sandbox_modified(parameters['verbose']):
                raise SitExceptionAbort("Aborting operation. There are uncommitted changes in sandbox.")
        
        branch_repository_url, branch_selected = self.select_branch_by_name(parameters['branch'][0], parameters['branch_type'][0], parameters['verbose'])

        # FIXXME: make revision selectable ???
        
        self.tools.run_external_command('svn merge ' + branch_repository_url, parameters['verbose'])

    ###############################################################
    def do_merge(self, path, message, verbose=False):
        if message:
            command = "svn merge " + path + " -m \'" + message + "\'"
        else:
            command = "svn merge " + path
        self.tools.run_external_command(command, verbose)
        
    ###############################################################
    def get_new_stash_branch_name(self, name):
        # ^/stashes/<user>.<stash_name>.<branch_type>.<branch_name>

        stash_base_path = "^/" + self.default_stash_folder + "/"

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

        # FIXME: implement selection of path/files to stash !
        
        # do stash:
        if self.is_sandbox_modified(parameters['verbose']):
            stash_branch_url, name_selected = self.get_new_stash_branch_name(parameters['name'])
            
            # FIXME: add message ?
            commit_path = self.get_relative_path_to_root()
            branch_url = self.relative_branch_root_url
            branch_message = "Stash Push (create branch): from <" + branch_url + '> to <'  + stash_branch_url + '> using stash reference name <' + name_selected + '>'
            # FIXME: revision in name !?

            try:
                branch_revision = self.do_branch("branch_name", stash_branch_url, parameters['auto_message'], branch_message, parameters['verbose'])
                self.do_checkout(stash_branch_url, 'HEAD', parameters['verbose'])
                commit_message = "Stash Push (commit all modifications): from <" + branch_url + "@" + branch_revision + '> to <'  + stash_branch_url + '> using stash reference name <' + name_selected + '>' 
                self.do_commit(commit_path, commit_message, parameters['verbose'])
                self.do_checkout(branch_url, branch_revision, parameters['verbose'])
            except SitException as e:
                # FIXXME: implement cleanup, show history ?! show commands that were executed until this point ?!
                raise SitException("Detected exception\n" + str(e))
            else:
                self.tools.info("Created stash <" + name_selected + ">")
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
        stash_base_path = "^/" + self.default_stash_folder + "/"

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
            remove_message = auto_message_prefix + "removing stash " + str(identifier) + " which is: " + path
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
                    self.do_merge_stash(stash_url, parameters['auto_message'], parameters['verbose'])
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
                            self.do_merge_stash(stash_url, parameters['auto_message'], parameters['verbose'])
                if stash_url is None: # if none is found error out
                    raise SitExceptionAbort("Aborting operation. There is no stash to apply found with the name: <" + parameters['name'] + ">")
        else:
            identifier = 0
            if stashes[identifier]:
                data = stashes[identifier]
                stash_url = data['stash_url']
                self.do_merge_stash(stash_url, parameters['auto_message'], parameters['verbose'])
            else:
                raise SitExceptionAbort("Aborting operation. There is no stash to apply available")

    ###############################################################
    def do_merge_stash(self, stash_url, auto_message, verbose):
        revision = self.do_get_head_revsion(stash_url, verbose)
        path = stash_url + " -r " + str(int(revision)-1) + ":" + revision + " " + self.relative_path 
        if auto_message:
            merge_message = self.auto_message_prefix + "applying stash " + identifier + " which is <" + stash_url + "> at path <" + path + ">"
        else:
            merge_message = None
        self.do_merge(path, merge_message, verbose)

    ###############################################################
    def do_get_head_revsion(self, path, verbose=False):
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

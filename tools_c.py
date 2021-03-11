# Description: SIT - Svn with gIT extensions, tools
# Author:      Joachim Lechner
# Licence:     GNU GENERAL PUBLIC LICENSE, Version 2, June 1991
# Source:      https://github.com/joachimlechner/sit

import subprocess
import re
import os
#from os import path
#import os.path
#from os.path import abspath
#from os import path

import sys
if sys.version_info[0] == 3:
    import inquirer
    
###############################################################
class tools_c:

    tools_debug = False
    
    # def __init__(self):

    ###############################################################
    def show(self, message):
        sys.stdout.flush()
        print(message)
        sys.stdout.flush()
        
    ###############################################################
    def info(self, message):
        sys.stdout.flush()
        print("INFO: " + message)
        sys.stdout.flush()
        
    ###############################################################
    def process(self, message):
        sys.stdout.flush()
        print("> " + message + " ...")
        sys.stdout.flush()

    ###############################################################
    def status(self, message):
        sys.stdout.flush()
        print("> " + message + ":")
        sys.stdout.flush()
        
    ###############################################################
    def error(self, message):
        sys.stdout.flush()
        print("ERROR: " + message)
        sys.stdout.flush()
        
    ###############################################################
    def debug(self, message):
        print("DEBUG: " + message)
        sys.stdout.flush()
        
    ###############################################################
    def is_pathfile_existing(self, pathfile):
        return path.exists(pathfile)

    ###############################################################
    def run_external_command(self, command, verbose=False):
        return self.do_run_external_command(command, verbose, False, True, True)

    def run_external_command_no_print(self, command, verbose=False):
        return self.do_run_external_command(command, verbose, False, False, False)

    def run_external_command_ignore_status_and_print(self, command, verbose=False):
        return self.do_run_external_command(command, verbose, True, True, True)
    
    def do_run_external_command(self, command, verbose=False, ignore_exit_code=False, print_line=False, get_results=False):
        sys.stdout.flush()
        if verbose:
            self.info("Executing command: <" + command + ">")
        try:
            if get_results is False:
                sp = subprocess.Popen(command, shell=True)
                exit_code = sp.wait()

            else:
                sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                results = []
                for line_item in sp.stdout:
                    line = line_item.decode("utf-8").rstrip()
                    results.append(line)
                    if print_line is True:
                        print(line)
                        sys.stdout.flush()
                exit_code = sp.wait()
        except subprocess.CalledProcessError as e:
            raise ToolException(e.output)
        except OSError as e:
            raise ToolException(e.output)
        except KeyboardInterrupt:
            raise ToolException("User abort.")
        except BaseException as e:
            raise ToolException("Error during execution:\n " + str(e))

        if ignore_exit_code is False:
            if exit_code != 0:
                #print("\n<\n")
                if get_results is False:
                    raise ToolException("Command <" + command + "> failed with exit code <" + str(exit_code) + ">")
                else:
                    raise ToolException("Command <" + command + "> failed with exit code <" + str(exit_code) + "> and message: \n" + '\n'.join(results) + "\n")
        
        return exit_code

            
    ###############################################################
    def run_external_command_and_get_results(self, command, verbose=False):
        if verbose:
            self.info("Executing command: <" + command + ">")
        try:
            sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            results = []
            for line_item in sp.stdout:
                line = line_item.decode("utf-8").rstrip()
                results.append(line)
            exit_code = sp.wait()
        except subprocess.CalledProcessError as e:
            raise ToolException(e.output)
        except OSError as e:
            raise ToolException(e.output)
        except KeyboardInterrupt:
            raise ToolException("User abort.")
        except BaseException as e:
            raise ToolException("Error during execution:\n " + str(e))
        
        if exit_code != 0:
            raise ToolException("Command <" + command + "> failed")
        
        return results
    
    ###############################################################
    def select_from_list(self, select_message, selections):
        if sys.version_info[0] == 3:
            questions = [
                inquirer.List(
                    "selected",
                    message=select_message,
                    choices=selections,
                ),
            ]
            answers = inquirer.prompt(questions)
            result = answers['selected']
        else:
            print(select_message)
            position = -1
            for selection in selections:
                position = position + 1
                if position>0:
                    print("\n")
                print(" [" + str(position) + "] " + selection)
            num = -1
            while (num < 0) or (num > position):
                if sys.version_info[0] == 3:
                    num_str = input("Select by entering the number (0-" + str(position) + ") or abort with 'q': ")
                else:
                    num_str = raw_input("Select by entering the number (0-" + str(position) + ") or abort with 'q': ")

                if num_str is "":
                    num = 0
                else:
                    p1 = re.compile(r'^q$')
                    m1 = p1.match("" + num_str)
                    if m1:
                        raise ToolException("User abort.")
                
                    p = re.compile(r'^(\d+)$')
                    m = p.match(num_str)
                    if m:
                        num = int(str(m.group(0)))
                        if (num < 0) or (num > position):
                            print("Invalid selection only valid between 0 to " + str(position) + " or 'q' for abort.\n")
                            num = -1
                    else:
                        print("Invalid selection only valid between 0 to " + str(position) + " or 'q' for abort.\n")
                        num = -1
            result = selections[position]
            print("Selected: [" + str(num) + "] " + result + "\n")
        return result
    
    ###############################################################
    # def does_path_exist(self, path):
    #     if os.path.isdir(path):
    #         return True
    #     else:
    #         return False

    def does_file_exist(self, file):
        if os.path.isfile(file):
            return True
        else:
            return False

    ###############################################################
    def read_file(self, filename, line_comment_regex, max_nr_lines):
        # Using readline() 
        file_handle = open(filename, 'r')

        line_nr = 0
        data = []

        while True:
            line_nr += 1

            if(line_nr > max_nr_lines):
                raise ToolException("Max number of lines <" + max_nr_lines + "> reached when reading from <" + filename + ">")
            
            # Get next line from file 
            line = file_handle.readline()

            # if line is empty 
            # end of file is reached 
            if not line:
                break

            line_strip = line.strip()

            if line_comment_regex:
                p1 = re.compile('^(.*)' + line_comment_regex)
                m1 = p1.match(line_strip)
                if m1:
                    line_strip = m1.group(1)
                
            p2 = re.compile('^\s*$')
            m2 = p2.match(line_strip)
            if not m2:
                data.append(line_strip);
                
                if(self.tools_debug):
                    print("read_file: " + filename + "@" + line_nr + ": " + line_strip)

        file_handle.close()

        return data
    
##########################################
##########################################
##########################################
class ToolException(Exception):
    name = "ToolException"
    message = ""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        if self.message:
            return self.name + ': ' + self.message
        else:
            return self.name + ' has been raised'


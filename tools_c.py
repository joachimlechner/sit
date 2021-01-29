# Description: SIT - Svn with gIT extensions, tools
# Author:      Joachim Lechner
# Licence:     GNU GENERAL PUBLIC LICENSE, Version 2, June 1991
# Source:      https://github.com/joachimlechner/sit

import subprocess

from os import path
import re

import sys
if sys.version_info[0] == 3:
    import inquirer
    
###############################################################
class tools_c:

    # def __init__(self):
        
    ###############################################################
    def info(self, message):
        print("INFO: " + message)

    ###############################################################
    def error(self, message):
        print("ERROR: " + message)

    ###############################################################
    def debug(self, message):
        print("DEBUG: " + message)

    ###############################################################
    def is_pathfile_existing(self, pathfile):
        return path.exists(pathfile)

    ###############################################################
    def run_external_command(self, command, verbose=False):
        if verbose:
            self.info("Executing command: <" + command + ">")
        try:
            sp = subprocess.Popen(command, shell=True)
            return_value = sp.wait()
        except subprocess.CalledProcessError as e:
            raise ToolException(e.output)
        except KeyboardInterrupt:
            raise ToolException("User abort.")
        
        if return_value != 0:
            raise ToolException("Command <" + command + "> failed")
        
        return return_value


    ###############################################################
    def run_external_command_and_get_results(self, command, verbose=False):
        if verbose:
            self.info("Executing command: <" + command + ">")
        try:
            sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            results = []
            for line_item in sp.stdout: #.readlines():
                #line = line_item.decode("utf-8").rstrip() # orginally this was used - failed with pathnames ?!
                #line = line_item.rstrip()
                #line = line_item.decode("utf-16").rstrip()
                # FIXME: what to use here ?!
                line = line_item.decode("ISO-8859-1").rstrip()
                results.append(line)
            return_value = sp.wait()
        except subprocess.CalledProcessError as e:
            raise ToolException(e.output)
        except KeyboardInterrupt:
            raise ToolException("User abort.")
        
        if return_value != 0:
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


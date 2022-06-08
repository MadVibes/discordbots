# Logger library to make code a bit neater and i'm lazy
#
#   Logging Level table:
#       0 - ERROR
#       1 - WARN
#       2 - LOG
#       3 - DEBUG
#
########################################################################################################
from datetime import datetime

class Logger:


    def __init__(self, logging_level, log_file, log_file_dir):
        self.level = logging_level
        self.log_file = (log_file == 'True')
        self.log_file_dir = log_file_dir


    # Static
    ####################################################################################################
    @staticmethod
    def timestamp():
        return datetime.now().strftime("[%S:%M:%H %d/%m/%Y]")


    @staticmethod
    def get_prefix(level):

        prefix = ""

        if(level == 0):
            prefix = '[ERROR]'
        elif (level == 1):
            prefix = '[ WARN]'
        elif (level == 2):
            prefix = '[  LOG]'
        elif (level == 3):
            prefix = '[DEBUG]'
        else:
            prefix = '[ -' + str(level) + '- ]'

        return prefix


    @staticmethod
    def _write(content, level, file):

        prefix = Logger.get_prefix(level)

        output = Logger.timestamp() + prefix + ' ' + content
        print(output)
        Logger.write_file(output, file)


    @staticmethod
    def write_file(content, log):
        with open(log, 'a') as f:
            f.write(content + "\n")


    @staticmethod
    def create_custom_prefix(custom_prefix, custom_prefix_size):
        c_prefix = '['
        for i in range(custom_prefix_size):
            if i< len(custom_prefix):
                c_prefix += custom_prefix[i]
            else:
                c_prefix += ' '
        c_prefix += ']'
        return c_prefix

    # Instance
    ####################################################################################################
    def write(self, content, level):

        # handle non string/int content
        if type(content) is not (str or int): content = str(content)

        prefix = Logger.get_prefix(level)

        # Add custom prefix
        # These attributes have to be populated by the instantiator
        if hasattr(self, 'custom_prefix') and hasattr(self, 'custom_prefix_size'):
            if self.custom_prefix_size > 0:
                prefix = Logger.create_custom_prefix(self.custom_prefix, self.custom_prefix_size) + prefix


        if (level <= self.level):
            output = Logger.timestamp() + prefix + ' ' + content
            print(output)

            if self.log_file:
                Logger.write_file(output, self.log_file_dir)


    def error(self, content):
        self.write(content, 0)


    def warn(self, content):
        self.write(content, 1)


    def log(self, content):
        self.write(content, 2)


    def debug(self, content):
        self.write(content, 3)


    ####################################################################################################

########################################################################################################
#   Copyright (C) 2022  Liam Coombs, Sam Tipper
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

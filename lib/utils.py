# Lib of generic functions to make life easier
#
########################################################################################################
from time import sleep
import threading, os


class Utils:


    @staticmethod
    def emoji_int_to_string_list(integer: int):
        """Convert ing to list of string form. e,g 23 returns ['two', 'three']"""
        list = []
        for num in str(integer):
            list.append(Utils.emoji_int_to_string(num))
        return list


    @staticmethod
    def emoji_int_to_string(char):
        """Convert single int to string form. e.g 2 returns 'two', 3 returns 'three'"""
        if char == '0':
            return '0️⃣'
        elif char == '1':
            return '1️⃣'
        elif char == '2':
            return '2️⃣'
        elif char == '3':
            return '3️⃣'
        elif char == '4':
            return '4️⃣'
        elif char == '5':
            return '5️⃣'
        elif char == '6':
            return '6️⃣'
        elif char == '7':
            return '7️⃣'
        elif char == '8':
            return '8️⃣'
        elif char == '9':
            return '9️⃣'
        elif char == '-':
            return '➖'


    @staticmethod
    def future_call(seconds: float, func_to_call, func_args=None):
        """Call a function on a different thread in X seconds"""
        def future_call(*args):
            if len(args) < 2:
                print('FATAL ERROR: INSUFFICIENT ARGS IN MULTITHREADED FUTURE_CALL UTIL METHOD')
                os._exit(1)
            sleep(float(args[0]))
            if len(args) > 2:
                args[1](2)
            else:
                args[1]()
        if func_args is None:
            thread = threading.Thread(target=future_call, args=(seconds, func_to_call))
        else:
            thread = threading.Thread(target=future_call, args=(seconds, func_to_call, func_args))

        thread.start()


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

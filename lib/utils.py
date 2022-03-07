# Lib of generic functions to make life easier
#
########################################################################################################

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

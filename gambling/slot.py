import random


class Slot_Machine:


  def __init__(self):
    self.slot_machine = [[0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0],]

    self.conversions = {2: 0.3, 3: 3, 4: 20, 5: 100}

  def spin(self):
    current_machine = self.slot_machine
    for row in range(len(current_machine)):
      for index, elem in enumerate(current_machine[row]):
        current_machine[row][index] = random.randint(1, 8)
    return current_machine


  def check_win(self, current_machine):
    wins = {}
    for row in range(len(current_machine)):
      multiplier = 0
      number = current_machine[row][0]
      for index, elem in enumerate(current_machine[row]):
        if current_machine[row][index] == number:
          multiplier += 1
        else:
          break
          
      if multiplier > 1:
        wins.update({row: self.conversions.get(multiplier)})
    return wins
    
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

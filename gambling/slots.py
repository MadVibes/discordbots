import random


class Slot:
  def __init__(self):
    self.slot_machine = [[0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0],]

  def spin(self):
    current_machine = self.slot_machine
    for row in range(len(current_machine)):
      for index, elem in enumerate(current_machine[row]):
        current_machine[row][index] = random.randint(2, 7)
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
          
      if multiplier > 2:
        wins.update({row: multiplier})
    return wins
    
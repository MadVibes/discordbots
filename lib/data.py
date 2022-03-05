# Data
# This handles storing data. This abstracts the process so it can be dia via DB or a JSON file 
####################################################################################################
import json
import os, sys

sys.path.insert(0, '../')
from lib.logger import Logger

class Database:
    
    def __init__(self, logger, output_file, init_schema):
        self.logger = logger
        self.output = output_file
        self.data = {}

        # Create file if it does not exist
        if not os.path.exists(self.output):
            with open(self.output, 'w') as file:
                json.dump(init_schema, file)

    @staticmethod
    def _write_file(target, data):
        with open(target, 'w') as output_file:
            json.dump(data, output_file)

    def write(self, data):
        Database._write_file(self.output, data)

    @staticmethod
    def _read_file(target):
        with open(target, 'r') as input_file:
            return json.load(input_file)

    def read(self):
        return Database._read_file(self.output)


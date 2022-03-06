# Simple lib to handle running a web server to allow HTTP requests
#
########################################################################################################
import sys
import threading
import http.server
import socket
from json import loads, dumps
from functools import partial
from datetime import datetime
import configparser
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, '../')
from lib.logger import Logger

class Handler(BaseHTTPRequestHandler):

    def __init__(self, logger, actions, service, config, start_time, *args, **kwargs):
        self.start_time = start_time
        self.actions = actions
        self.logger = logger
        self.service = service
        self.config = config
        super().__init__(*args, **kwargs)

    # POST
    ####################################################################################################
    def do_POST(self):
        try:
            self.handle_POST()
        except Exception as e:
            self.logger.error('Failed to handle POST request: %s' % e)
            self.write_response(500, '')

    def handle_POST(self):
        if self.path == '/bounce':
            content = { 
                    'request': 'Accepted',
                    'timestamp': str(datetime.now()),
                    'request_body': self.read_json_body()
                }
            self.write_response(200, dumps(content))

        elif self.path == '/action':
            # Check if valid secret
            if not self.auth():
                self.write_response(401, '')
            else:
                self.handle_POST_action()
        
        else:
            self.write_response(404, '')
        
        self.logger.debug('Request: POST %s' % self.path)

    def handle_POST_action(self):
        try:
            self.logger.log('Web action received')
            action_json = self.read_json_body()
            
            # Check for missing fields
            if 'action' not in action_json or 'parameters' not in action_json :
                content = { 
                        'request': 'Rejected',
                        'timestamp': str(datetime.now()),
                        'error': 'Invalid request, \'action\' and \'parameters\' are required fields'
                    }
                self.write_response(400, dumps(content))
                return None

            self.logger.log(f"Processing action '{str(action_json['action'])}'")
            response = {}
            try: 
                response = self.actions[action_json['action']](self.service, action_json['parameters'])
                content = { 
                    'request': 'Accepted',
                    'timestamp': str(datetime.now()),
                    'response': response
                }
            except Exception as e:
                content = { 
                    'request': 'Failed',
                    'timestamp': str(datetime.now()),
                    'response': str(e)
                }
            self.write_response(200, dumps(content))
        except Exception as e:
            raise e # Rethrow, maybe add logging here?

    # GET
    ####################################################################################################
    def do_GET(self):
        try:
            self.handle_GET()
        except Exception as e:
            self.logger.error('Failed to handle GET request: %s' % e)
            self.write_response(500, '')

    def handle_GET(self):
        if self.path == '/health':
            content = { 
                    'uptime': str(datetime.now() - self.start_time)
                }
            self.write_response(200, dumps(content))
        else:
            self.write_response(404, '')
        
        self.logger.debug('Request: GET %s' % self.path)
    ####################################################################################################

    def write_response(self, status_code, content):
        response = content.encode('utf-8')

        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def read_json_body(self):
        try:
            length = int(self.headers['Content-Length'] )
            if length == 0:
                return None
            return loads(self.rfile.read(length).decode('utf-8'))
        except Exception as e:
            self.logger.warn('Failed to parse JSON body')
            self.logger.debug('JSON body parse exception: %s' % e)
            return ''

    def log_request(self, message):
        """ Do nothing """
        pass

    def auth(self):
        secret = self.headers.get('Authorization')
        return secret in self.config['COMMS_ACCEPTED_SECRETS'];

class Web_Server:

    def __init__(self, logger, actions, service, config):
        self.actions = actions
        self.logger = logger
        self.service = service
        self.config = config
        self.url = self.config['COMMS_IP']
        self.port = int(self.config['COMMS_PORT'])

        h = partial(Handler, logger, actions, service, config, datetime.now())

        # Create server
        try:
            server = http.server.ThreadingHTTPServer((self.url, self.port), h)
            self.thread = threading.Thread(target = server.serve_forever)
            self.thread.daemon = True
        except Exception as e:
            self.logger.error('Failed to create Web Server instance. Disabling...')
            self.logger.debug(e)


    def start(self):
        try:
            self.thread.start()
            self.logger.log('Web Server started ({host}:{port})'.format( host=self.url, port=self.port))
        except Exception as e:
            self.logger.error('Failed to start Web Server instance. Disabling...')
            self.logger.debug(e)

########################################################################################################
#   Copyright (C) 2022  Liam Coombs
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

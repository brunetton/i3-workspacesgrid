#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''
Usage:
    {self_filename} start-server
    {self_filename} print-i3-conf
    {self_filename} --help

Start a local (http) server that listen to commands (via GET urls).
See print-i3-conf option for correct urls list.

Options:
    start            Start
    print-i3-conf    Print the lines to add to your i3 conf file
'''

from http.server import BaseHTTPRequestHandler, HTTPServer
from configparser import RawConfigParser
import os
import re
import subprocess
import sys

from docopt import docopt
import i3ipc


CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'i3-workspacesgrid.ini')
I3_CONFIG_FILE = "~/.config/i3/config"


def coords_to_id(row, col):
    ''' Get workspace id ([1-n]) from coords ([0-n], [0-n])
    '''
    return row * state['grid_width'] + col + 1


def id_to_coords(id):
    ''' Get coords ([0-n], [0-n]) from id ([1-n])
    '''
    return int((id - 1) / state['grid_width']), (id - 1) % state['grid_width']


def get_id_on_direction(direction):
    ''' Get coords ([0-n], [0-n]) for workspace in grid in given direction.
    Return current id if move is impossible (for example trying to get to the right of the last row, without loop option)
    Params:
        - direction: one of ['up', 'down', 'left', 'right']

    >>> get_id_on_direction('right')
    7
    '''
    assert direction in ['up', 'down', 'left', 'right']
    current_row, current_col = id_to_coords(state['current_ws_id'])
    new_id = None
    if direction == 'up':
        if not (current_row - 1 < 0 and not conf.getboolean('main', 'loop')):
            new_row = (current_row - 1) % state['grid_height']
            new_id = coords_to_id(new_row, current_col)
    elif direction == 'down':
        if not (current_row + 1 > state['grid_height'] - 1 and not conf.getboolean('main', 'loop')):
            new_row = (current_row + 1) % state['grid_height']
            new_id = coords_to_id(new_row, current_col)
    elif direction == 'left':
        if not (current_col - 1 < 0 and not conf.getboolean('main', 'loop')):
            new_col = (current_col - 1) % state['grid_width']
            new_id = coords_to_id(current_row, new_col)
    elif direction == 'right':
        if not (current_col + 1 > state['grid_width'] - 1 and not conf.getboolean('main', 'loop')):
            new_col = (current_col + 1) % state['grid_width']
            new_id = coords_to_id(current_row, new_col)
    if new_id is None:
        # no change
        new_id = state['current_ws_id']
    return new_id


def display_workspace(id, direct_jump=False):
    ''' Goto given workspace id.
        direct_jump: is this move a "direct" move ? ie, [1-10] workspace, directly adressed via shortkey
        This param is set to avoid "bounce" phenomena on grid edges.
    '''
    if direct_jump:
        if id == state['current_ws_id'] and conf.getboolean('main', 'jump-back'):
            # jump back to where we came
            id = state['last_ws_id']
            print("jump back to workspace {}".format(id))
        else:
            # normal jump
            state['last_ws_id'] = state['current_ws_id']
    print("jump to workspace {}".format(id))
    i3.command("workspace {}".format(id))
    state['current_ws_id'] = id


def move_container_to(id):
    print("move focused containter to workspace {}".format(id))
    i3.command("move container to workspace {}".format(id))
    if conf.getboolean('main', 'follow-container-on-move'):
        state['last_ws_id'] = state['current_ws_id']
        display_workspace(id)


def try_to_run(command, shouldnt_be_empty=False):
    try:
        cmnd_output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as exc:             # subprocess returned non 0 output code
        raise Exception("Status : FAIL", exc.returncode, exc.output)
    if shouldnt_be_empty and not cmnd_output:
        raise Exception("Error: last command returned empty string. This shouldn't happen. Command was:\n{}".format(command))
    return cmnd_output.decode("utf-8")


class myHandler(BaseHTTPRequestHandler):
    """Class to handle incoming requests
    """

    def do_GET(self):
        command = self.path[1:]  # "/something" => "something"
        if command in ['up', 'down', 'left', 'right']:
            new_id = get_id_on_direction(command)
            display_workspace(new_id, direct_jump=False)
        elif command[0:5] == 'jump/':
            new_id = command[5:]
            assert new_id
            display_workspace(int(new_id), direct_jump=True)
        elif command in ['send/up', 'send/down', 'send/left', 'send/right']:
            direction = command[5:]
            new_id = get_id_on_direction(direction.lower())
            move_container_to(new_id)
        elif command[0:5] == 'send/':
            new_id = command[5:]
            assert new_id
            move_container_to(int(new_id))
        else:
            print('Unknown command: "{}". See --help message and readme for more informations.'.format(command))
        return


## Initialisation
# ini file parse
global conf
conf = RawConfigParser()
conf.read(CONFIG_FILE)
# args parse
args = docopt(__doc__.format(self_filename=os.path.basename(__file__)))
# global vars
global state
state = {
    'grid_width': conf.getint('main', 'width'),
    'grid_height': conf.getint('main', 'height'),
}
if state['grid_width'] < 1 or state['grid_height'] < 1:
    sys.exit("Error: grid dimentions must be > 0")
# i3ipc init
i3 = i3ipc.Connection()
# init some state variables
current_ws = i3.get_tree().find_focused().workspace()
state['current_ws_id'] = int(current_ws.name)
state['last_ws_id'] = state['current_ws_id']

## Did user asked to print lines to add to i3 conf ?
if args['print-i3-conf']:
    cut_here = "✂ ✂ ✂ ✂ cut here ✂ ✂ ✂ ✂\n\n"
    print("In order to use i3-workspacesgrid, you'll need to:\n")
    print("- 1: **Comment** this lines into your config file:\n")
    for command in [
            "cat {} | sed -n -r '/bindsym \$mod\+([^ ]+) workspace ([0-9]+)\s*/p'",
            "cat {} | sed -n -r '/bindsym \$mod\+([^ ]+) move.+workspace ([0-9]+)\s*/p'"
        ]:
        command = command.format(I3_CONFIG_FILE)
        print(try_to_run(command, shouldnt_be_empty=True))
    print("- 2: **Add** this lines into your config file:\n")
    print(cut_here)
    print("## i3-workspacesgrid config")
    print("# Direct acces to desktops")
    command = "cat {} | sed -n -r 's|(\s*#\s*)?bindsym \$mod\+([^ ]+) workspace ([0-9]+)\s*|bindsym \$mod\+\\2 exec curl http://localhost:{}/jump/\\3|p'"
    command = command.format(I3_CONFIG_FILE, conf.getint('server', 'port'))
    print(try_to_run(command, shouldnt_be_empty=True))
    print("# Direct sending containers to workspaces")
    command = "cat {} | sed -n -r 's|(\s*#\s*)?bindsym \$mod\+([^ ]+) move.+workspace ([0-9]+)\s*|bindsym \$mod\+\\2 exec curl http://localhost:{}/send/\\3|p'"
    command = command.format(I3_CONFIG_FILE, conf.getint('server', 'port'))
    print(try_to_run(command, shouldnt_be_empty=True))
    # New commands
    base_url = "http://localhost:{}".format(conf.getint('server', 'port'))
    lines = ["# Moving througth workspaces"]
    directions = ['Up', 'Down', 'Left', 'Right']
    lines.append("\n".join(["bindsym $mod+Ctrl+{} exec curl {}/{}".format(direction, base_url, direction.lower()) for direction in directions]))
    lines.append("# Sending containers to workspaces")
    lines.append("\n".join(["bindsym $mod+Ctrl+Shift+{} exec curl {}/send/{}".format(direction, base_url, direction.lower()) for direction in directions]))
    print("\n".join(lines))
    print("\n" + cut_here)
    print("Note: you can replace curl command with any equivalent command of your choice.\n")
    print("You may also want to add this line to automatically run server each time you start i3:")
    print("exec --no-startup-id {} start-server".format(os.path.realpath(__file__)))
    print("(or exec --no-startup-id xterm -hold -e '{} start-server' to monitor output)".format(os.path.realpath(__file__)))
    print("\nDon't forget to reload i3 conf !\n")
    sys.exit()

## User asked to run server; so run server
if args['start-server']:
    server_port = conf.getint('server', 'port')
    server = HTTPServer(('', server_port), myHandler)
    print('Listening on {} ...'.format(server_port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('^C received, shutting down the web server.')
        server.socket.close()

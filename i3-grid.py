#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Usage:
    {self_filename} up
    {self_filename} down
    {self_filename} left
    {self_filename} right
    {self_filename} sendUp
    {self_filename} sendDown
    {self_filename} sendLeft
    {self_filename} sendRight
    {self_filename} print-i3-conf
    {self_filename} --help

Options:
    print-i3-conf    Print the lines to add to your i3 conf file
'''

from ConfigParser import RawConfigParser
import os
import re
import sys

from docopt import docopt
import i3ipc


CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'i3-workspacesgrid.ini')

def coords_to_id(row, col):
    ''' Get workspace id ([1-n]) from coords ([0-n], [0-n])
    '''
    return row * grid_width + col + 1

def id_to_coords(id):
    ''' Get coords ([0-n], [0-n]) from id ([1-n])
    '''
    return int((id - 1) / grid_width), (id - 1) % grid_width

def get_id_on_direction(direction):
    ''' Get coords ([0-n], [0-n]) for workspace in grid in given direction.
    Return current id if move is impossible (for example trying to get to the right of the last row, without loop option)
    Params:
        - direction: one of ['up', 'down', 'left', 'right']

    >>> get_id_on_direction('right')
    7
    '''
    assert direction in ['up', 'down', 'left', 'right']
    current_row, current_col = current_ws_coords
    new_id = None
    if direction == 'up':
        if not (current_row - 1 < 0 and not conf.getboolean('main', 'loop')):
            new_row = (current_row - 1) % grid_height
            new_id = coords_to_id(new_row, current_col)
    elif direction == 'down':
        if not (current_row + 1 > grid_height - 1 and not conf.getboolean('main', 'loop')):
            new_row = (current_row + 1) % grid_height
            new_id = coords_to_id(new_row, current_col)
    elif direction == 'left':
        if not (current_col - 1 < 0 and not conf.getboolean('main', 'loop')):
            new_col = (current_col - 1) % grid_width
            new_id = coords_to_id(current_row, new_col)
    elif direction == 'right':
        if not (current_col + 1 > grid_width - 1 and not conf.getboolean('main', 'loop')):
            new_col = (current_col + 1) % grid_width
            new_id = coords_to_id(current_row, new_col)
    if new_id is None:
        # no change
        new_id = current_ws_id
    return new_id

def display_workspace(id):
    print "displaying workspace {}".format(id)
    i3.command("workspace {}".format(id))

def move_container_to(id):
    print "move focused containter to workspace {}".format(id)
    i3.command("move container to workspace {}".format(id))
    if conf.getboolean('main', 'follow-container-on-move'):
        display_workspace(id)


## Initialisation
# ini file parse
global conf
conf = RawConfigParser()
conf.read(CONFIG_FILE)
global grid_width
grid_width = conf.getint('main', 'width')
global grid_height
grid_height = conf.getint('main', 'height')
if grid_width < 1 or grid_height < 1:
    sys.exit("Error: grid dimentions must be > 0")
# args parse
args = docopt(__doc__.format(self_filename=os.path.basename(__file__)))
# i3ipc init
i3 = i3ipc.Connection()
# init some globals
current_ws = i3.get_tree().find_focused().workspace()
global current_ws_id
current_ws_id = int(current_ws.name)
global current_ws_coords
current_ws_coords = id_to_coords(current_ws_id)

## Did user asked to print lines to add to i3 conf ?
if args['print-i3-conf']:
    command_path = os.path.realpath(__file__)
    cut_here = "✂ ✂ ✂ ✂ cut here ✂ ✂ ✂ ✂\n\n"
    lines = ["## i3-workspacesgrid config", "# Moving througth workspaces"]
    directions = ['Up', 'Down', 'Left', 'Right']
    lines.append("\n".join(["bindsym $mod+Ctrl+{} exec {} {}".format(direction, command_path, direction.lower()) for direction in directions]))
    lines.append("# Moving containers to workspaces")
    lines.append("\n".join(["bindsym $mod+Ctrl+Shift+{} exec {} send{}".format(direction, command_path, direction) for direction in directions]))
    print "Append this lines to your i3 conf file (usually ~/.config/i3/config):\n\n\n" + cut_here + "\n".join(lines)
    print "\n" + cut_here + "Don't forget to reload i3 conf !"
    sys.exit()

## Do the job
for command in ['up', 'down', 'left', 'right', 'sendUp', 'sendDown', 'sendLeft', 'sendRight']:
    if args[command]:
        # this command have been passed as program param
        re_match = re.search('send(.*)', command)  # is this command begins with "send" ?
        if re_match:
            # this command begins with "send"
            direction = re_match.group(1)
            new_id = get_id_on_direction(direction.lower())
            move_container_to(new_id)
        else:
            new_id = get_id_on_direction(command)
            print "moving to {}".format(new_id)
            display_workspace(new_id)

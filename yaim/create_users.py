from __future__ import print_function

import subprocess
import sys

def create_users(users_file):
    cmd = 'newusers'
    cmd_call = [cmd, users_file]
    print('Creating new users from file "{0}"'.format(users_file))
    subprocess.call(cmd_call)
    

if len(sys.argv) > 1:
    group_file = sys.argv[1]
    print("Using file {0} as input".format(group_file))
    create_users(group_file)
else:
    print("Error: no users file specified", file=sys.stderr)

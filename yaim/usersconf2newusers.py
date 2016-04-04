# /bin/env python
# converts a YAIM users.conf (see https://twiki.cern.ch/twiki/bin/view/LCG/YaimGuide400#User_configuration_in_YAIM)
# to a group file and a user file
from __future__ import print_function
import re

from collections import namedtuple
Group = namedtuple('Group', ['name', 'gid'])

Account = namedtuple(
    'Account', ['uid', 'name', 'groups', 'vo', 'flag', 'gid', 'shell'])


def parse_line(line):
    '''
        Parses lines from users.conf:
        UID:LOGIN:GID1[,GID2,...]:GROUP1[,GROUP2,...]:VO:FLAG:
    '''
    line = line.rstrip('\n')
    items = line.split(':')

    groups = []
    for name, gid in zip(items[3].split(','), items[2].split(',')):
        groups.append(Group(name, gid))

    result = Account(
        uid=items[0],
        name=items[1],
        groups=groups,
        vo=items[4],
        flag=items[5],
        gid=groups[0].gid,
        shell='/bin/bash',
    )

    return result


def get_unique_groups(accounts):
    results = {}
    for acc in accounts:
        for group in acc.groups:
            results[group.name] = group
    return results


def create_group_file(groups):
    '''
        creates a group file to be used as
        cat groups.file | awk -F':' {groupadd $1 -g $2}
    '''
    with open('groups.file', 'w') as f:
        for name, group in groups.items():
            print('{0}:{1}'.format(name, group.gid), file=f)


def create_users_file(accounts):
    '''
        to be used with the newusers command
        Format: 
            name:passwd:uid:gid:gecos:dir:shell
    '''
    n_accounts = len(accounts)
    with open('users.file', 'w') as f:
        for i, account in enumerate(accounts):
            line = '{name}:x:{uid}:{gid}:mapped user for group {vo}:'
            line += '/home/{name}:{shell}'
            line = line.format(
                name=account.name,
                uid=account.uid,
                gid=account.gid,
                vo=account.vo,
                shell=account.shell,
            )
            line_end = "\n"
            # avoid new line at the end of the file or 'newusers' will fail
            if i == n_accounts - 1:
                line_end = ""
            print(line, file=f, end=line_end)

if __name__ == '__main__':
    import sys

    input_file = sys.argv[1]

    accounts = []
    add_account = accounts.append
    with open(input_file) as f:
        for line in f:
            acc = parse_line(line)
            add_account(acc)

    groups = get_unique_groups(accounts)
    create_group_file(groups)
    create_users_file(accounts)

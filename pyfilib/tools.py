# -*- coding: utf-8 -*-
#    pyfi: easy wireless access point fabricator
#    Copyright (C) 2017  Ismael Lugo

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, re

ipv4_regex = ''.join(['(?P<octet_%s>\d{1,3})\.' % n for n in [1, 2, 3]])
ipv4_regex += '(?P<octet_i>\d{1,3})(-(?P<octet_e>\d{1,3}))?'
ipv4_regex = re.compile(ipv4_regex)
macaddr_regex = re.compile(':'.join(['([a-zA-Z0-9]{2})' for n in range(6)]))


# Console colors
colors = {
    'white':  '\033[0m',
    'red':    '\033[31m',
    'green':  '\033[32m',
    'orange': '\033[33m',
    'blue':   '\033[34m',
    'purple': '\033[35m',
    'cyan':   '\033[36m',
    'gray':   '\033[37m',

    # Alias color name
    'w': '\033[0m',
    'r': '\033[31m',
    'g': '\033[32m',
    'o': '\033[33m',
    'b': '\033[34m',
    'p': '\033[35m',
    'c': '\033[36m',
    'gr': '\033[37m'}


def printer(char, color, text, std=sys.stdout):
    std.write('{}[{}] {}{}\n'.format(colors[color], char, text, colors['w']))

error    = lambda text: printer('!', 'red',    text, std=sys.stderr)
critical = lambda text: (error(text), exit(1))
warning  = lambda text: printer('*', 'orange', text, std=sys.stderr)
info     = lambda text: printer('-', 'white',  text)
sucess   = lambda text: printer('+', 'green',  text)
debug    = lambda text: printer('~', 'gray',   text)


def check_ipv4(ipaddr):
    result = ipv4_regex.match(ipaddr)
    if not result:
        return False

    octets = result.groupdict()
    for octet_name in octets:
        octet = octets[octet_name]
        if octet is None:
            continue
        octet = int(octet)
        if octet > 255:
            return False
        octets[octet_name] = octet

    if octets['octet_e'] and octets['octet_e'] <= octets['octet_i']:
        return False
    return True


def check_macaddr(macaddr):
    return macaddr_regex.match(macaddr) is not None


def current_args(obj, attr_keys):
    def funcwrap(func):
        def argswrap(*args, **kwargs):
            for keyname, attr in attr_keys.items():
                if keyname in kwargs:
                    continue
                try:
                    args[attr[0]]
                except IndexError:
                    pass
                else:
                    continue
                kwargs[keyname] = getattr(obj, attr[1])
                #print kwargs
            if len(args) == 0:
                return func(**kwargs)
            else:
                return func(*args, **kwargs)
        return argswrap
    return funcwrap
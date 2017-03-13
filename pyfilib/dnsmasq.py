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

from . import environ
from . import macaddr
from . import tools


@tools.current_args(environ, {
    'wlan_interface': (0, 'wlan_interface'),
    'dnsmasq_conf':   (1, 'dnsmasq_conf'  ),
    '_macaddr':       (2, 'macaddr'       ),
    'init_ip':        (3, 'init_ip'       ),
    'end_ip':         (4, 'end_ip'        )})
def generate_conf(wlan_interface, dnsmasq_conf, _macaddr, init_ip, end_ip):
    if dnsmasq_conf:
        return file(dnsmasq_conf, 'r').read()

    _text = []
    write = lambda text: _text.append(text)
    #write('log-queries')
    #write('log-dhcp')
    #write('')
    write('bind-interfaces')
    write('interface=' + wlan_interface)
    if _macaddr:
        _macaddr = macaddr.macs(_macaddr)  # lint:ok
        if len(_macaddr.allowmacs) > 0:
            write('dhcp-range=set:allow,%s,%s' % (init_ip, end_ip))
            for mac in _macaddr.allowmacs:
                write('dhcp-mac=set:allow,' + mac)
            write('dhcp-ignore=tag:!allow')

        elif len(_macaddr.denymacs) > 0:
            write('dhcp-range=%s,%s' % (init_ip, end_ip))
            write('dhcp-range=set:deny,10.0.0.1,10.0.0.255')
            for mac in _macaddr.denymacs:
                write('dhcp-mac=set:deny,' + mac)
            write('dhcp-ignore=tag:deny')
        else:
            write('dhcp-range=%s,%s' % (init_ip, end_ip))
    else:
        write('dhcp-range=%s,%s' % (init_ip, end_ip))
    return '\n'.join(_text)
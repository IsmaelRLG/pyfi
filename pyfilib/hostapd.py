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
from . import tools


@tools.current_args(environ, {
    'wlan_interface': (0, 'wlan_interface'),
    'hostapd_conf':   (1, 'hostapd_conf'  ),
    'ssid':           (2, 'ssid'          ),
    'password':       (3, 'password'      ),
    'auth_method':    (4, 'auth_method'   )})
def generate_conf(wlan_interface, hostapd_conf, ssid, password, auth_method):
    if hostapd_conf:
        return file(hostapd_conf, 'r').read()

    text = []
    join = lambda var, value: var + '=' + value
    write = lambda _text: text.append(_text)
    write(join('interface',       wlan_interface))
    write(join('driver',         'nl80211'))
    write(join('ssid',           ssid))
    write(join('hw_mode',        'g'))
    write(join('channel',        '6'))

    if auth_method in ('wpa', 'wpa2'):
        if len(password) < 8:
            tools.critical('Very short password, must be at least 8 characters')
        write(join('wpa',                '1' if auth_method == 'wpa' else '2'))
        write(join('wpa_key_mgmt',       'WPA-PSK'                           ))
        write(join('wpa_pairwise',       'CCMP'                              ))
        write(join('wpa_group_rekey',    '600'                               ))
        write(join('wpa_gmk_rekey',      '86400'                             ))
        write(join('wpa_passphrase',      password                           ))

    elif auth_method == 'wep':
        pass  # future...

    return '\n'.join(text)

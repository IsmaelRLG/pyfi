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

wlan_interface = None
dest_interface = None

# File management
###################################
import os
import sys
import humanfriendly
from tempfile import mkdtemp
from six.moves import configparser
from . import tools

home_path = os.environ['HOME']
conf_dir = os.path.join(home_path, '.config')
proj_name = 'pyfi'
conf_name = proj_name + '.conf'
conf_path = os.path.join(conf_dir, conf_name)
temp = mkdtemp(prefix=proj_name)

wlan_interface = 'auto'
dest_interface = None
dnsmasq_conf = None
hostapd_conf = None
ssid = proj_name
password = None
auth_method = 'free'
limit_users = None
macaddr = os.path.join('pyfi-macs.cfg')
ip_range = '192.168.150.100-150'
init_ip = None
end_ip = None


def load_vars():
    if os.path.isdir(conf_path):
        tools.critical("Config is a directory: '%s'" % conf_path)

    if sys.version_info[0:2] >= (3, 2):
        cfg_kwargs = {'inline_comment_prefixes': (';',)}
    else:
        cfg_kwargs = {}

    config = configparser.ConfigParser(**cfg_kwargs)
    config.read(conf_path)
    def_section = proj_name

    #if os.path.exists(conf_path) and file(conf_path, 'r').read().strip() != ''\
        #and not config.has_section(def_section):
        #tools.warning('Config without the main section: ' + def_section)
    global wlan_interface, dest_interface
    global dnsmasq_conf, hostapd_conf
    global ssid, password, auth_method
    global limit_users, macaddr, init_ip, end_ip

    def get(option, default, method='get', postget=None):
        if not config.has_section(def_section):
            return default
        if config.has_option(def_section, option):
            try:
                data = getattr(config, method)(def_section, option)
                if data == '':
                    return default
                return postget(data) if postget else data
            except Exception as err:
                #tools.warning('exception: ' + repr(err))
                pass
        return default

    def check_file(path):
        path = humanfriendly.parse_path(path)

        if not os.path.exists(path):
            tools.critical("No such file or directory: '%s'" % path)
        elif os.path.isdir(path):
            tools.critical("Config is a directory: '%s'" % path)
        return path

    wlan_interface = get('wlan_interface', wlan_interface)
    dest_interface = get('dest_interface', dest_interface)

    dnsmasq_conf = get('dnsmasq_conf', None, postget=check_file)
    if  config.has_section(def_section)                and \
        config.has_option(def_section, 'hostapd_conf') and\
        config.get(def_section, 'hostapd_conf') != '':
        hostapd_conf = check_file(config.get(def_section, 'hostapd_conf'))
    else:
        hostapd_conf = None
        ssid = get('ssid', ssid)
        password = get('password', password)
        auth_method = get('auth_method', auth_method)
        limit_users = get('limit_users', None, method='getint')
        macaddr = get('macaddr', macaddr, postget=check_file)

        def process_ip(ipaddr):
            if isinstance(ipaddr, tuple):
                ipaddr = ip_range
            if not tools.check_ipv4(ipaddr):
                tools.critical("Invalid ip address: '%s'" % ipaddr)
            reipv4 = tools.ipv4_regex.match(ipaddr).groupdict()
            ipaddr = '{octet_1}.{octet_2}.{octet_3}.'
            if not reipv4['octet_e']:
                if not limit_users:
                    reipv4['octet_e'] = '255'
                elif (reipv4['octet_i'] + limit_users) > 255:
                    reipv4['octet_e'] = '255'
                else:
                    reipv4['octet_e'] = str(reipv4['octet_i'] + limit_users)

                if not tools.check_ipv4((ipaddr + '{octet_i}-{octet_e}').format(**reipv4)):
                    tools.critical("Invalid IP address: '%s'" % ipaddr)
            return (
                (ipaddr + '{octet_i}').format(**reipv4),
                (ipaddr + '{octet_e}').format(**reipv4))

        init_ip, end_ip = get('ipaddr', process_ip(ip_range), postget=process_ip)



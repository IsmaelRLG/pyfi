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
from . import dnsmasq
from . import hostapd
from . import tools
import subprocess, logging, random, shutil, time, os, re


def cmd(command, capture=True, logerr=True):
    if capture is True:
        logging.info('sh cmd: ' + command)
        out_f = os.path.join(environ.temp, environ.proj_name + '-cmd.out')
        err_f = os.path.join(environ.temp, environ.proj_name + '-cmd.err')
        with open(out_f, 'w') as out_fp:
            with open(err_f, 'w') as err_fp:
                subprocess.call(command.split(), stdout=out_fp, stderr=err_fp)

        out = open(out_f, 'r').read().splitlines()
        err = open(err_f, 'r').read().splitlines()
        if len(err) > 0 and logerr:
            [logging.error('sh err: ' + l) for l in err]
        if len(out) > 0:
            [logging.debug('sh out: ' + l) for l in err]
        if len(out) + len(err) == 0:
            logging.debug('sh out: No data output')
        os.remove(out_f)
        os.remove(err_f)
        return {'out': out, 'err': err}
    else:
        os.system(command)


def detect_itfs():
    itfs = {}
    regex = re.compile('[0-9]{1,}: (?P<interface>.+): .+ mtu [0-9]{1,} '
        'qdisc .+ state (?P<state>(UNKNOWN|UP)) mode .+', re.IGNORECASE)
    for line in cmd('ip link show')['out']:
        matched = regex.match(line)
        if matched is not None:
            itfs[matched.group('interface')] = matched.group('state')
    return itfs


def get_iwconf():
    iwtf_name = None
    iwtfs = []
    for line in cmd('iwconfig', logerr=False)['out']:
        genl = line
        line = line.lower()
        if not line.startswith(' '):
            iwtf_name = genl.split()[0]

        if line.find('mode:managed') != -1:
            iwtfs.append(iwtf_name)
            iwtf_name = None
    return iwtfs


def check_pid(pid=0, filename=None):
    if filename:
        if not os.path.exists(filename) or not os.path.isfile(filename):
            return False
        with open(filename, 'r') as fp:
            pid = fp.read()
        if not pid.isdigit():
            return False
        else:
            pid = int(pid)

    if pid <= 0:
        return False

    import errno
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.EPERM:
            return True
        else:
            return False
    else:
        return False


def kill(pid=0, filename=None):
    if filename:
        if not os.path.exists(filename) or not os.path.isfile(filename):
            return False
        with open(filename, 'r') as fp:
            pid = fp.read()
        if not pid.isdigit():
            return False
        else:
            pid = int(pid)

    try:
        from signal import SIGTERM
        while 1:
            os.kill(pid, SIGTERM)
            time.sleep(1)
    except OSError, err:
        err = str(err)
        if err.find("No such process") > 0 and filename:
            print('matado D:')
            os.remove(filename)


def run():
    if os.getuid() != 0:
        tools.critical('root only!')

    if environ.wlan_interface == 'auto':
        itfs = get_iwconf()
        if len(itfs) == 0:
            tools.error('No wireless interfaces were found.')
            tools.error('You need to plug in a wifi device or install drivers.')
            exit(1)
        environ.wlan_interface = random.choice(itfs)
    logging.info('wireless device selected: ' + environ.wlan_interface)

    if environ.dest_interface == 'auto':
        itfs = detect_itfs()
        if len(itfs) == 0:
            tools.error('No dest interfaces were found.')
            tools.critical('You need to plug in a device or install drivers.')
        environ.dest_interface = random.choice(itfs.keys())
        logging.info('device selected to forward: ' + environ.dest_interface)

    if environ.dest_interface and environ.dest_interface == environ.wlan_interface:
        tools.critical('WTF? dest == wlan!')

    nmcli_version = cmd('nmcli -v')['out'].pop()
    if nmcli_version.find('0.8.') != -1:
        cmd('nmcli nm wifi off')
    elif re.match('(0\.[9]\.|1\.[0-9]\.).+', nmcli_version):
        cmd('nmcli r wifi off')
    else:
        tools.critical('Unknown network manager version!')

    rfkill_err = cmd('rfkill unblock wlan')['err']
    if rfkill_err:
        tools.critical(rfkill_err)

    cmd('ifconfig %(interface)s %(gateway)s' % {
        'interface': environ.wlan_interface,
        'gateway':   environ.init_ip})

    dnsmasq_pidfile = os.path.join(environ.temp, 'dnsmasq.pid')
    if not environ.dnsmasq_conf:
        dnsmasq_conf = os.path.join(environ.temp, 'dnsmasq.conf')
        with file(dnsmasq_conf, 'w') as conf:
            conf.write(dnsmasq.generate_conf())
        environ.dnsmasq_conf = dnsmasq_conf

    cmd('dnsmasq --pid-file={pidfile} --conf-file={filename}'.format(
        pidfile=dnsmasq_pidfile, filename=environ.dnsmasq_conf))
    cmd('sysctl net.ipv4.ip_forward=1')

    # Forwarding!
    if environ.dest_interface:
        iptables_rule = 'iptables -t nat -A POSTROUTING -o {dest} -j MASQUERADE'
        cmd(iptables_rule.format(dest=environ.dest_interface))
        tools.info('forwarding to: ' + environ.dest_interface)

    if not environ.hostapd_conf:
        hostapd_conf = os.path.join(environ.temp, 'hostapd.conf')
        with file(hostapd_conf, 'w') as conf:
            conf.write(hostapd.generate_conf())
        environ.hostapd_conf = hostapd_conf

    tools.info('SSID:     ' + environ.ssid)
    if environ.password:
        tools.info('Password: ' + environ.password)

    tools.info("WI-FI AP running, press [CTRL+C] for exit")

    try:
        cmd('hostapd ' + environ.hostapd_conf, capture=False)
    except KeyboardInterrupt:
        pass
    finally:
        iptables_rule = 'iptables -D POSTROUTING -t nat -o {dest} -j MASQUERADE'
        cmd(iptables_rule.format(dest=environ.dest_interface))
        cmd('sysctl net.ipv4.ip_forward=0')
        if check_pid(filename=dnsmasq_pidfile):
            kill(filename=dnsmasq_pidfile)
        #cmd('service dnsmasq stop')
        shutil.rmtree(environ.temp)

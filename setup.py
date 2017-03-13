#!/usr/bin/env python
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

import subprocess
import sys
import os
import platform

# if nix then run installer
if platform.system() != "Linux":
    print("[!] Sorry this installer is not designed for any other system other than Linux.")
    sys.exit(1)
requires = os.path.join(os.path.dirname(__file__), 'requirements.txt')
requires = file(requires, 'r').read().splitlines()


def pyfi_setup():
    installer = False
    install_dep = True
    if os.getuid() != 0:
        print("Are you root? Please execute as root")
        sys.exit(1)

    try:
        if sys.argv[1] == "install":
            installer = True
        if '--no-depends' in sys.argv:
            sys.argv.remove('--no-depends')
            install_dep = False

    except IndexError:
        print("** Pyfi installer")
        print("** Copyright (C) 2017  Ismael Lugo")
        print("\nTo install: python %s install" % __file__)

    if installer is True:

        if install_dep:
            depends = ['hostapd', 'dnsmasq', 'rfkill']
            # Debian based system
            if os.path.isfile("/etc/apt/sources.list"):
                depends.append('python-setuptools')
                command = "apt-get --force-yes -y install "

            # Arch based system
            elif os.path.isfile("/etc/pacman.conf"):
                depends.append('‎python2-setuptools')
                command = "pacman -S --noconfirm --needed "

            # fedora >= 22
            elif os.path.isfile("/etc/dnf/dnf.conf"):
                depends.append('‎python-setuptools')
                command = "dnf -y install "
            else:
                print("[!] You're not running a Debian, Fedora or Arch variant")
                print("[!] Please install %s manually" % ', '.join(depends))
                sys.exit(1)
            subprocess.Popen(command + ' '.join(depends), shell=True).wait()

        try:
            import setuptools
        except ImportError:
            print('[!] Please first install python setuptools')
            sys.exit(1)

        setuptools.setup(
            name='pyfi',
            version=__import__('pyfilib').__version__,
            description="easy wireless access point fabricator",
            url='https://github.com/IsmaelRLG/pyfi',
            author='Ismael Lugo',
            author_email='ismaelrlgv@gmail.com',
            packages=['pyfilib'],
            requires=requires,
            scripts=['bin/pyfi'],

            classifiers=[
                "Development Status :: 4 - Beta",
                'Environment :: Console',
                'Intended Audience :: Developers',
                'Intended Audience :: System Administrators',
                'License :: OSI Approved :: MIT License',
                'Natural Language :: English',
                'Operating System :: POSIX :: Linux',
                'Programming Language :: Python :: 2',
                'Programming Language :: Python :: 2.6',
                'Programming Language :: Python :: 2.7',
                'Programming Language :: Python :: 3',
                'Programming Language :: Python :: 3.4',

                'Topic :: Communications',
                'Topic :: Scientific/Engineering :: Human Machine Interfaces',
                'Topic :: System :: Systems Administration',
                'Topic :: Terminals',
                'Topic :: Utilities'])


if __name__ == '__main__':
    pyfi_setup()

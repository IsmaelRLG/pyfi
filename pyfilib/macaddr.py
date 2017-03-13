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

import re, os
from . import tools


class MacError(ValueError):
    def __init__(self, text, data, nline):
        self.string = text + ('"%s" in line #%s' % (data, nline))
        self.data = data
        self.nline = nline

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.string)

    def __str__(self):
        return self.string


class macs:
    re_line = re.compile('(?P<macaddr>.{17}) (?P<act>allow|deny)$', 2)

    def __init__(self, file_path):
        self.file_path = file_path
        self.denymacs = []
        self.allowmacs = []
        self.read()

    def add_mac(self, act, macaddr):
        if act == 'allow':
            if macaddr in self.denymacs:
                MacError('Ambiguous action for mac address: ' + macaddr)
            if macaddr in self.allowmacs:
                tools.warning('Mac address %s already added in allowed macs' % macaddr)
            self.allowmacs.append(macaddr)

        if act == 'deny':
            if macaddr in self.allowmacs:
                MacError('Ambiguous action for mac address: ' + macaddr)
            if macaddr in self.denymacs:
                tools.warning('Mac address %s already added in deny macs' % macaddr)
            self.denymacs.append(macaddr)

    def del_mac(self, act, macaddr):
        if act == 'allow':
            if not macaddr in self.allowmacs:
                return tools.warning('Mac address %s not added' % macaddr)
            self.allowmacs.remove(macaddr)

        if act == 'deny':
            if not macaddr in self.denymacs:
                return tools.warning('Mac address %s not added' % macaddr)
            self.denymacs.remove(macaddr)

    def _read(self, path):
        if not os.path.exists(path):
            return

        with file(path, 'r') as fp:
            read = fp.read()
        nline = 0
        for line in read.splitlines():
            genesis_line = line
            nline += 1
            line = line.strip()
            if '#' in line:
                line = line.split('#', 1)[0]
            if line == '':
                continue
            result = self.re_line.match(line.lower())
            if not result:
                raise MacError('Bad segment', genesis_line, nline)

            macaddr, act = result.group('macaddr', 'act')
            if not tools.check_macaddr(macaddr):
                raise MacError('Bad mac address', macaddr, nline)
            self.add_mac(act, macaddr)

    def read(self):
        self._read(self.file_path)

    def _save(self, path):
        with file(path, 'w') as fp:
            fp.write('# [ Allow zone ]\n')
            for macaddr in self.allowmacs:
                fp.write('%s allow\n' % macaddr)

            fp.write('\n# [ Deny zone ]\n')
            for macaddr in self.denymacs:
                fp.write('%s deny\n' % macaddr)

    def save(self):
        tools.info('Mac config saved in "%s"' % self.file_path)
        self._save(self.file_path)
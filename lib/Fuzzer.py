#-------------------------------------------------------------------------------
# Copyright (c) 2012-2013 by European Organization for Nuclear Research (CERN)
# Author: Justin Salmon <jsalmon@cern.ch>
#-------------------------------------------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

import os
import random
import sys

from XrdImposter.MessageHelper import MessageHelper
from XrdImposter.Utils import get_struct


class Fuzzer(object):
    """Take a valid network packet and fuzz the crap out of it

    Fuzzing strategies:

        - Random bytes
        - Exhaustive (recursive)
        - Fuzz vectors (known "dangerous" values"
    """

    def __init__(self, context):
        self.mh = MessageHelper(context)

    def fuzz(self, valid_packet):
        """Generate fuzzed packets"""
        i = 0
        self.valid_packet = self.mh.unpack_request(valid_packet)[0]

        # Just do a static number of permutations for now.
        while i < 1000:
            print '[i]', i
            yield self.permute(self.valid_packet)
            i += 1

    def permute(self, packet):
        """Return a fuzzed packet"""
        if packet.type == 'handshake':
            packet_struct = get_struct('ClientInitHandShake')
        else:
            packet_struct = get_struct('ClientRequestHdr')
            packet_struct += get_struct('Client' + packet.type[4:].title() + 'Request')

        if packet.type == 'kXR_read':
            packet_struct += get_struct('read_args')

        # Remove 'type' field that we inserted for convenience
        vars = packet._asdict()
        del vars['type']

        for field in packet_struct:
            if field['fuzzable']:
                vars[field['name']] = self.mutate(vars[field['name']], field['type'])

        return self.mh.build_message(packet_struct, vars)

    def mutate(self, field, type):
        if type == 'H':
            return random.randint(0, 65535)
        elif type == 'l':
            return random.randint(-2147483648 + 1, 2147483647)
        elif type == 'q':
            return random.randint(-sys.maxint + 1, sys.maxint)
        elif type in ('s', 'c'):
            return os.urandom(len(field))
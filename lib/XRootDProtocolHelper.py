#-------------------------------------------------------------------------------
# Copyright (c) 2011-2012 by European Organization for Nuclear Research (CERN)
# Author: Lukasz Janyst <ljanyst@cern.ch>
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

import struct

class XRootDProtocolHelper:
    
    @property
    def clientHandshakeRequest(self):
        return struct.pack('>lllll', 0, 0, 0, 4, 2012)
    
    def serverHandshakeResponse(self):
        pass
    
    def createRequest(self, request):
        pass
    
    def createResponse(self, request):
        pass
    
    def unpackHandshakeResponse(self, response):
        return struct.unpack('>BBHlll', response)
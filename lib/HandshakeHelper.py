#-------------------------------------------------------------------------------
# Copyright (c) 2011-2012 by European Organization for Nuclear Research (CERN)
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

import struct

class HandshakeHelper:
  """Class to aid making initial xrootd handshakes.
  
  The format of the handshake is well defined and unchanging, so
  it can be safely hard-coded here.
  
  """
    
  @property
  def request(self):
    """Return a packed representation of a client handshake request."""
    return struct.pack('>lllll', 0, 0, 0, 4, 2012)
  
  @property
  def response(self):
    """Return a packed representation of a server handshake response."""
    return struct.pack('>ccHlll', '\0', '\0', 0, 8, 663, 1)
  
  def unpack_response(self, response):
    """Return an unpacked tuple representation of a server handshake 
    response."""
    return struct.unpack('>ccHlll', response)
  
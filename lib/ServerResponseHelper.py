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

import sys
import struct

import XProtocol
import HandshakeHelper

from Utils import format_length

class ServerResponseHelperException(Exception):
  """General Exception raised by ServerResponseHelper."""
    
  def __init__(self, desc):
    """Construct an exception.
        
    @param desc: description of an error
    """
    self.desc = desc

  def __str__(self):
    """Return textual representation of an error."""
    return str(self.desc)
      
class ServerResponseHelper:
  
  def __init__(self, context):
    self.sock = context['socket']
    self.clientadd = context['address']
    self.clientnum = context['number']
  
  def handshake(self):
    handshake = HandshakeHelper.HandshakeHelper()
    
    request = handshake.unpack_request(self.sock.recv(20))
    self.sock.send(handshake.response)
    
    format = '>HHl10cBcl'
    print struct.unpack(format, self.sock.recv(format_length(format)))
  
  
  
  
  
  
  
  
  
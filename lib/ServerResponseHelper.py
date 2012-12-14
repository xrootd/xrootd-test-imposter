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
import MessageHelper
import LoginHelper
import AuthHelper

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
    self.context = context
    self.sock = context['socket']
    self.clientadd = context['address']
    self.clientnum = context['number']
    self.seclib = context['seclib']
    
    self.mh = MessageHelper.MessageHelper(context)
  
  def handshake(self):
    handshake = HandshakeHelper.HandshakeHelper(self.context)
    
    request_raw = self.mh.receive_request(handshake.request_format)
    request = handshake.unpack_request(request_raw)
    print 'handshake request:\t', request
    self.mh.send_response(handshake.response)

  def login(self):
    login = LoginHelper.LoginHelper(self.context)
  
    request_raw = self.mh.receive_request(login.request_format)
    request = login.unpack_request(request_raw)
    print 'login request:\t', request
    self.mh.send_response(login.response(request[0]))
  
  
  
  
  
  
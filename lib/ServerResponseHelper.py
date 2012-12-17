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

from Utils import format_length, struct_format

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
    
  def protocol(self):
    request_struct = self.mh.get_struct('ClientProtocolRequest')
    request_raw = self.mh.receive_request(struct_format(request_struct))
    request = self.mh.unpack_request(request_raw)
    print 'protocol request:\t', request
    
    response_struct = self.mh.get_struct('ServerResponseHeader') + \
                      self.mh.get_struct('ServerResponseBody_Protocol')
    params = {'streamid': request[0],
              'status'  : XProtocol.XResponseType.kXR_ok,
              'dlen'    : 8,
              'pval'    : XProtocol.kXR_PROTOCOLVERSION,
              'flags'   : XProtocol.kXR_isServer}
    
    self.mh.send_response(self.mh.build_message(response_struct, params))
    
  def login(self):
    login = LoginHelper.LoginHelper(self.context)
  
    request_raw = self.mh.receive_request(login.request_format)
    request = self.mh.unpack_request(request_raw)
    print 'login request:\t\t', request
    self.mh.send_response(login.response(request[0]))
  
  def auth(self):
    auth = AuthHelper.AuthHelper(self.context)
    
    request_raw = self.mh.receive_request(auth.request_format)
    request = auth.unpack_request(request_raw)
    print 'auth request:\t\t', request
    auth.authenticate(request[-1])
  
  
  
  
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

from Utils import *

      
class ServerResponseHelper:
  
  def __init__(self, context):
    self.context = context    
    self.mh = MessageHelper.MessageHelper(context)
    
  def do_full_handshake(self, verify_auth=False):
    """"""
    for request in self.receive():
      
      if request.type == 'handshake':
        print request
        self.send(self.handshake() 
                  + self.protocol(streamid=request.streamid))
      
      elif request.type == 'kXR_login':
        print request
        self.send(self.login(streamid=request.streamid))
        
      elif request.type == 'kXR_auth':
        print request
        if verify_auth:
          response = self.auth(streamid=request.streamid, cred=request.cred)
        else: 
          response = self.auth(streamid=request.streamid)
        
        self.send(response)
        break
    
  
  def send(self, response):
    """Send a packed xrootd response."""
    self.mh.send_message(response)
  
  def receive(self):
    """"""
    while True:
      request = self.unpack(self.mh.receive_message())
      if request:
        yield request
      else: break
    
  def unpack(self, request_raw):
    """"""
    return self.mh.unpack_request(request_raw)
  
  def handshake(self, **kwargs):
    """"""
    handshake = HandshakeHelper.HandshakeHelper(self.context)
    return handshake.build_response(**kwargs)
    
  def protocol(self, streamid=None, status=None, dlen=None, pval=None, 
               flags=None):
    """"""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Protocol')
    params = {'streamid': streamid  if streamid else 0,
              'status'  : status    if status   else XProtocol.XResponseType.kXR_ok,
              'dlen'    : dlen      if dlen     else 8,
              'pval'    : pval      if pval     else XProtocol.kXR_PROTOCOLVERSION,
              'flags'   : flags     if flags    else XProtocol.kXR_isServer}
    
    return self.mh.build_message(response_struct, params)
    
  def login(self, **kwargs):
    """"""
    login = LoginHelper.LoginHelper(self.context)
    return login.build_response(**kwargs)
  
  def auth(self, **kwargs):
    """"""
    auth = AuthHelper.AuthHelper(self.context)
    return auth.build_response(**kwargs)
  
  def stat(self, streamid=None, status=None, dlen=None, data=None, id=None,
           size=None, flags=None, modtime=None):
    """"""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Buffer')
                      
    if data:
      pass
    else:
      data = (x for x in (id, size, flags, modtime) if x is not None)
      data = ' '.join([str(param) for param in data])
    
    params = {'streamid': streamid  if streamid else 0,
              'status'  : status    if status   else XProtocol.XResponseType.kXR_ok,
              'dlen'    : dlen      if dlen     else len(data),
              'data'    : data}
    
    return self.mh.build_message(response_struct, params)
    
  def close(self):
    self.context['socket'].close()
  
  
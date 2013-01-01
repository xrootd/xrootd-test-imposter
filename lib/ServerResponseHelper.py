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
    
  def send(self, response):
    """Send a packed xrootd response."""
    self.mh.send_message(response)
  
  def receive(self):
    """Receive a packed xrootd request."""
    while True:
      request = self.unpack(self.mh.receive_message())
      if request:
        yield request
      else: break
    
  def unpack(self, request_raw):
    """Return an unpacked named tuple representation of a client request."""
    return self.mh.unpack_request(request_raw)
    
  def do_full_handshake(self, verify_auth=False):
    """Perform handshake/protocol/login/auth sequence with default values.
    
    If verify_auth is true, the credentials supplied by the client in the
    kXR_auth request will be properly authenticated, otherwise they will not
    be checked."""    
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
          contparams = self.auth(request.cred)
          if contparams:
            response = self.kXR_authmore(streamid=request.streamid, 
                                         data=contparams)
          else:
            response = self.kXR_ok(streamid=request.streamid)
        else: 
          response = self.kXR_ok(streamid=request.streamid)
        
        self.send(response)
        if not contparams: break
  
  def handshake(self, **kwargs):
    """Return a packed representation of a handshake response. The default 
    response values can be individually modified by the optional kwargs."""    
    handshake = HandshakeHelper.HandshakeHelper(self.context)
    return handshake.build_response(**kwargs)
    
  def protocol(self, streamid=None, status=None, dlen=None, pval=None, 
               flags=None):
    """Return a packed representation of a kXR_protocol response.""" 
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Protocol')
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else XProtocol.XResponseType.kXR_ok,
     'dlen'    : dlen      if dlen     else 8,
     'pval'    : pval      if pval     else XProtocol.kXR_PROTOCOLVERSION,
     'flags'   : flags     if flags    else XProtocol.kXR_isServer}
    
    return self.mh.build_message(response_struct, params)
    
  def login(self, **kwargs):
    """Return a packed representation of a kXR_login response. The default 
    response values can be individually modified by the optional kwargs.""" 
    login = LoginHelper.LoginHelper(self.context)
    return login.build_response(**kwargs)
  
  def auth(self, cred):
    """""" 
    auth_helper = AuthHelper.AuthHelper(self.context)
    return auth_helper.auth(cred)
  
  def stat(self, streamid=None, status=None, dlen=None, data=None, id=None,
           size=None, flags=None, modtime=None):
    """Return a packed representation of a kXR_stat response.""" 
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Stat')
                      
    if data: pass
    else:
      data = (x for x in (id, size, flags, modtime) if x is not None)
      data = ' '.join([str(param) for param in data])
    
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else XProtocol.XResponseType.kXR_ok,
     'dlen'    : dlen      if dlen     else len(data),
     'data'    : data}
    
    return self.mh.build_message(response_struct, params)
  
  def kXR_attn(self):
    pass
  
  def kXR_authmore(self, streamid=None, status=None, dlen=None, data=None):
    """"""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Authmore')                     
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else XProtocol.XResponseType.kXR_authmore,
     'dlen'    : dlen      if dlen     else len(data),
     'data'    : data}
    return self.mh.build_message(response_struct, params)

  def kXR_error(self):
    pass

  def kXR_ok(self, streamid=None):
    """Return a packed kXR_ok response with default values."""
    response_struct = get_struct('ServerResponseHeader')
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : XProtocol.XResponseType.kXR_ok,
     'dlen'    : 0}
    return self.mh.build_message(response_struct, params)
  
  def KXR_oksofar(self):
    pass
  
  def kXR_redirect(self):
    pass
  
  def kXR_wait(self):
    pass
  
  def kXR_waitresp(self):
    pass
    
  def close(self):
    """Close this server socket"""
    self.context['socket'].close()
  
  
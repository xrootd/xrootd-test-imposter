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
import socket

import XProtocol
import MessageHelper
import HandshakeHelper
import LoginHelper
import AuthHelper


class ClientRequestHelper:
  """Class to aid sending/receiving client xrootd messages."""
    
  def __init__(self, context):
    """Constructor: Store context variables."""
    self.context = context
    self.sock = context['socket']
    self.streamid = context['streamid']
    self.seclib = context['seclib']
    
    self.mh = MessageHelper.MessageHelper(context)
    
  def _do_request(self, requestid, request_struct, params):
    """Return an unpacked representation of a response to the given
    request."""
    request = self.mh.build_request(request_struct, params) 
    response_raw = self.mh.send_request(requestid, request)
    return self.mh.unpack_response(response_raw, requestid)
  
  def handshake(self):
    """Perform initial handshake."""
    handshake = HandshakeHelper.HandshakeHelper(self.context)
    
    response_raw = self.mh.send_request('handshake', handshake.request)
    response = handshake.unpack_response(response_raw)
    print 'handshake response:\t', response
    
  def kXR_login(self, username, admin):
    """Perform login sequence."""
    login = LoginHelper.LoginHelper(self.context, username, admin)

    response_raw = self.mh.send_request(login.requestid, login.request)
    response = login.unpack_response(response_raw)
    print 'login response:\t\t', response
    
    if response[1]['auth']:
      self.kXR_auth(response[1]['message'])
      
  def kXR_auth(self, response):
    auth = AuthHelper.AuthHelper(self.context, response)
    
    response_raw  = self.mh.send_request(auth.requestid, auth.request)
    response      = auth.unpack_response(response_raw)
    print 'auth response:\t\t', response
    
  def kXR_protocol(self):
    request_struct = self.mh.get_struct('ClientProtocolRequest')
    requestid = 'kXR_protocol'
    
    params = {'streamid'  : self.streamid,
              'requestid' : self.mh.get_requestid(requestid),
              'clientpv'  : XProtocol.XLoginVersion.kXR_ver003, 
              'reserved'  : (12 * "\0"),
              'dlen'      : 0}
    
    response = self._do_request(requestid, request_struct, params)
    print 'protocol response:\t', response
    
  def kXR_ping(self):
    request_struct = self.mh.get_struct('ClientPingRequest')
    requestid = 'kXR_ping'
    
    params = {'streamid'  : self.streamid,
              'requestid' : self.mh.get_requestid(requestid),
              'reserved'  : (16 * "\0"),
              'dlen'      : 0}
    
    response = self._do_request(requestid, request_struct, params)
    print 'ping response:\t\t', response
    
  def kXR_query(self):
    pass
  
  def kXR_chmod(self):
    pass
  
  def kXR_close(self):
    pass
  
  def kXR_dirlist(self):
    pass
  
  def kXR_getfile(self):
    pass
  
  def kXR_mkdir(self):
    pass
  
  def kXR_mv(self):
    pass
  
  def kXR_open(self):
    pass
  
  def kXR_putfile(self):
    pass
  
  def kXR_read(self):
    pass
  
  def kXR_rm(self):
    pass
  
  def kXR_rmdir(self):
    pass
  
  def kXR_sync(self):
    pass
  
  def kXR_stat(self, path):
    request_struct = self.mh.get_struct('ClientStatRequest')
    requestid = 'kXR_stat'
    
    params = {'streamid'  : self.streamid,
              'requestid' : self.mh.get_requestid(requestid),
              'options'   : '0',
              'reserved'  : (11 * "\0"),
              'fhandle'   : (4  * "\0"),
              'dlen'      : len(path),
              'path'      : list(path)}
    
    response = self._do_request(requestid, request_struct, params)
    print 'stat response:\t\t', response
  
  def kXR_set(self):
    pass
  
  def kXR_write(self):
    pass
  
  def kXR_admin(self):
    pass
  
  def kXR_prepare(self):
    pass
  
  def kXR_statx(self):
    pass
  
  def kXR_endsess(self):
    pass
  
  def kXR_bind(self):
    pass
  
  def kXR_readv(self):
    pass
  
  def kXR_verifyw(self):
    pass
  
  def kXR_locate(self):
    pass
  
  def kXR_truncate(self):
    pass


          
          
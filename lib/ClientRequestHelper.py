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
import HandshakeHelper
import LoginHelper
import AuthHelper
from Utils import flatten


class ClientRequestHelperException(Exception):
    """General Exception raised by ClientRequestHelper."""
    
    def __init__(self, desc):
        """Construct an exception.
        
        @param desc: description of an error
        """
        self.desc = desc

    def __str__(self):
        """Return textual representation of an error."""
        return str(self.desc)


class ClientRequestHelper:
  """Class to aid sending/receiving client xrootd messages."""
    
  def __init__(self, context):
    """Constructor: Store context variables."""
    self.sock = context['socket']
    self.streamid = context['streamid']
    self.seclib = context['seclib']
  
  def handshake(self):
    """Perform initial handshake."""
    handshake = HandshakeHelper.HandshakeHelper()
    
    response_raw = self._send_request('handshake', handshake.request)
    response = handshake.unpack_response(response_raw)
    print 'handshake response:\t', response
    
  def kXR_login(self, username, admin):
    """Perform login sequence."""
    login = LoginHelper.LoginHelper(self.streamid, username, admin)

    response_raw = self._send_request(login.requestid, login.request)
    response = login.unpack_response(response_raw)
    print 'login response:\t\t', response
    
    if response['auth']:
      self.kXR_auth(response['message'])
      
  def kXR_auth(self, response):
    auth = AuthHelper.AuthHelper(response, self.seclib, 
                                 self.streamid, self.sock)
    
    response_raw  = self._send_request(auth.requestid, auth.request)
    response      = auth.unpack_response(response_raw)
    print 'auth response:\t\t', response
    
  def kXR_protocol(self):
    request_struct = self._get_struct('ClientProtocolRequest')
    requestid = 'kXR_protocol'
    
    params = {'requestid' : self._get_requestid(requestid),
              'clientpv'  : XProtocol.XLoginVersion.kXR_ver003, 
              'reserved'  : (12 * "\0"),
              'dlen'      : 0}
    
    response = self._do_request(requestid, request_struct, params)
    print 'protocol response:\t', response
    
  def kXR_ping(self):
    request_struct = self._get_struct('ClientPingRequest')
    requestid = 'kXR_ping'
    
    params = {'requestid' : self._get_requestid(requestid),
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
    request_struct = self._get_struct('ClientStatRequest')
    requestid = 'kXR_stat'
    
    params = {'requestid' : self._get_requestid(requestid),
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
  
  #-----------------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------------

  def _do_request(self, requestid, request_struct, params):
    """Return an unpacked representation of a response to the given
    request."""
    request       = self._build_request(request_struct, params) 
    response_raw  = self._send_request(requestid, request)
    return          self._unpack_response(response_raw, requestid)

  def _build_request(self, request_struct, params):
    """Return a packed representation of the given params mapped onto
    the given request struct."""
    params.update({'streamid': self.streamid})
    
    if not len(params) == len(request_struct):
      print "[!] Error building request: wrong number of parameters"
      sys.exit(1)
      
    request = tuple()
    format = '>'
    
    for member in request_struct:
      request += (params[member['name']],)
      if member.has_key('size'):
        if member['size'] == 'dlen':
          format += str(params[member['size']]) + member['type']
        else:
          format += str(member['size']) + member['type']
      else: 
        format += member['type']

    return struct.pack(format, *tuple(flatten(request)))
    
  def _send_request(self, requestid, request):
    """Send a packed request and return a packed response."""
    try:
      self.sock.send(request)
    except socket.error, e:
      raise ClientRequestHelperException('Error sending %s request: %s' 
                                         % (requestid, e))
    
    try:  
      response = self.sock.recv(4096)
    except socket.error, e:
      raise ClientRequestHelperException('Error receiving %s response: %s' 
                                         % (requestid, e))
    return response    
  
  def _unpack_response(self, response, requestid):
    """Return an unpacked tuple representation of a server response."""
    header_struct = self._get_struct('ServerResponseHeader')
    format = '>'
    
    for member in header_struct:
      format += member['type']
    
    dlen = struct.unpack(format + ('s' * (len(response) - 8)), response)[2]
    
    try:
      body_struct = self._get_struct('ServerResponseBody_' 
                                      + requestid[4:].title())
    except: body_struct = list()
    
    for member in body_struct:
      if member.has_key('size'):
        format += str(member['size']) + member['type']
      else: 
        format += member['type']
        
    if not body_struct:
      format += (str(dlen) + 's')
    
    response = struct.unpack(format, response)
    return self._get_responseid(response[1]), response
    
  def _get_struct(self, name):
    """Return a representation of a struct as a list of dicts."""
    if hasattr(XProtocol, name):
        return getattr(XProtocol, name)
    else:
      raise ClientRequestHelperException("[!] XProtocol struct not found:", 
                                         name)
    
  def _get_requestid(self, requestid):
    """Return the integer request ID associated with the given string 
    request ID.""" 
    if hasattr(XProtocol.XRequestTypes, requestid):
      return getattr(XProtocol.XRequestTypes, requestid)
    else:
      print "[!] Unknown request ID:", requestid
      sys.exit(1)
      
  def _get_responseid(self, responseid):
    """Return the string response ID associated with the given integer
    response ID."""
    try:
      respid = XProtocol.XResponseType.reverse_mapping[responseid]
    except KeyError, e:
      print "[!] Unknown response ID:", responseid
      sys.exit(1) 
      
    return respid
          
          
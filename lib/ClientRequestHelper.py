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
    """Constructor: Store context variables and perform initial 
    handshake.
    """
    self.sock = context['socket']
    self.streamid = context['streamid']
    # Do the handshake
    self.handshake()
  
  def handshake(self):
    """Perform initial handshake."""
    handshake = HandshakeHelper.HandshakeHelper()
    
    try:
      response_raw = self._send_request(handshake.request)
    except ClientRequestHelperException, e:
      print "[!] Error during handshake:", e
      sys.exit(1)
      
    response = handshake._unpack_response(response_raw)
    print 'handshake response:\t', response
    
  def kXR_login(self, username, admin):
    """Perform login sequence, including protocol request."""
    login = LoginHelper.LoginHelper(self.streamid, username, admin)
    
    self.kXR_protocol()
    
    try:
      response_raw = self._send_request(login.request)
    except ClientRequestHelperException, e:
      print "[!] Error during login:", e
      sys.exit(1)
      
    response = login._unpack_response(response_raw)
    print 'login response:\t\t', response
    
    if response['auth']:
      self.kXR_auth(response['response'])
      
  def kXR_auth(self, response):
    auth = AuthHelper.AuthHelper(response, self.streamid, self.sock)
    
    try:
      response_raw = self._send_request(auth.request)
    except ClientRequestHelperException, e:
      print "[!] Error during authentication:", e
      sys.exit(1)
      
    response = auth._unpack_response(response_raw)
    print 'auth response:\t\t', response
    
  def kXR_protocol(self):
    request_struct = self._get_struct('ClientProtocolRequest')
    requestid = 'kXR_protocol'
    
    params = {'requestid' : self._get_requestid(requestid),
              'clientpv'  : XProtocol.XLoginVersion.kXR_ver003, 
              'reserved'  : (12 * "\0"),
              'dlen'      : 0}
    request = self._build_request(request_struct, params) 
    
    try:
      response_raw = self._send_request(request)
    except ClientRequestHelperException, e:
      print "[!] Error during protocol request:", e
      sys.exit(1)
      
    response = self._unpack_response(response_raw, requestid)
    print 'protocol response:\t', response
    
    

  def _build_request(self, request_struct, params):
    params.update({'streamid': self.streamid})
    
    if not len(params) == len(request_struct):
      print "[!] Error building request: wrong number of parameters"
      sys.exit(1)
      
    request = tuple()
    format = '>'
    
    for member in request_struct:
      request += (params[member['name']],)
      if member.has_key('size'):
        format += str(member['size']) + member['type']
      else: 
        format += member['type']
      
    return struct.pack(format, *request)
    
  def _send_request(self, request):
    """Send a packed request and return a packed response."""
    try:
      self.sock.send(request)
    except socket.error, e:
      raise ClientRequestHelperException('Error sending request: %s' % e)
    
    try:  
      response = self.sock.recv(4096)
    except socket.error, e:
      raise ClientRequestHelperException('Error receiving response: %s' % e)
    
    return response    
  
  def _unpack_response(self, response, requestid):
    header_struct = self._get_struct('ServerResponseHeader')
    body_struct = self._get_struct('ServerResponseBody_' 
                                      + requestid[4:].title())
    
    response_struct = header_struct + body_struct
    format = '>'
    
    for member in response_struct:
      if member.has_key('size'):
        format += str(member['size']) + member['type']
      else: 
        format += member['type']
    
    return struct.unpack(format, response)
    
  def _get_struct(self, name):
    """Return a representation of a struct as a list of dicts."""
    if hasattr(XProtocol, name):
        return getattr(XProtocol, name)
    else:
      print "[!] XProtocol struct not found:", name
      sys.exit(1) 
            
    return struct['properties']['public']
    
  def _get_requestid(self, requestid):
    """Return the integer request ID associated with the given 
    string request ID.

    For example, passing "kXR_ping" will return 3011.

    """ 
    if hasattr(XProtocol.XRequestTypes, requestid):
      return getattr(XProtocol.XRequestTypes, requestid)
    else:
      print "[!] Unknown request ID:", requestid
      sys.exit(1)
          
          
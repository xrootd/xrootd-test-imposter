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

class XProtocolHelperError(Exception):
  pass

class XProtocolHelper:
    
  def __init__(self, context):
    self.sock = context['socket']
    self.streamid = context['streamid']
    self.handshake()
  
  def handshake(self):
    handshake = HandshakeHelper.HandshakeHelper()
    
    try:
      self.sock.send(handshake.request)
      response_raw = self.sock.recv(1024)
    except socket.error, e:
      print "[!] Error during handshake:", e
      sys.exit(1)
      
    response = handshake.unpack_response(response_raw)
    print response
    
  def login(self, vars):
    pass
  
  def send_request(self, request):
    self.sock.send(request)
    response = self.sock.recv(1024)
    return self.unpack_response(response)
      
  def create_request(self, requestvars):
    request = tuple()
    fmt = '>'
    
    # Unpack variables
    try:
      reqtype = requestvars['type']
      requestid = requestvars['requestid']
      params = requestvars['params']
    except KeyError, e:
      print "[!] Request missing necessary value:", e
      sys.exit(1)
        
    # Get the correct request struct
    request_struct = self.get_struct(reqtype)
    # Get integer request ID
    requestid = self.get_requestid(requestid)
    
    # Tuple-ify struct with real values
    for member in request_struct:
      if member['name'] == 'streamid':
        # Fill in stream ID
        request += (int(self.streamid),)
        fmt += 'H'
      if member['name'] == 'requestid':
        #Fill in request ID
        request += (requestid,)
        fmt += 'H'
      if member['name'] == 'reserved':
        # Fill in reserved area
        size = int(member['size'])
        request += size * ('\0',)
        fmt += size * 'c'
      if member['name'] == 'dlen':
        request += (0,)
        fmt += 'l'

    return struct.pack(fmt, *request)
                          
  def unpack_response(self, response):
    print len(response)
    return struct.unpack('>ccHl' + ('c' * (len(response) - 8)), response)
  
  def create_response(self, request):
    pass
    
  def get_struct(self, name):
    """Return a representation of a struct as a list of dicts."""
    if hasattr(XProtocol, name):
        return getattr(XProtocol, name)
    else:
      print "[!] XProtocol struct not found:", name
      sys.exit(1) 
            
    return struct['properties']['public']
    
  def get_requestid(self, requestid):
    """Return the integer request ID associated with the given 
    string request ID.

    For example, passing "kXR_ping" will return 3011.

    """ 
    if hasattr(XProtocol.XRequestTypes, requestid):
      return getattr(XProtocol.XRequestTypes, requestid)
    else:
      print "[!] Unknown request ID:", requestid
      sys.exit(1)
          
          
          
          
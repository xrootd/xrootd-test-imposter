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

from collections import namedtuple
from Utils import flatten, struct_format, format_length, get_requestid, \
                  get_responseid, get_struct

import XProtocol


class MessageHelper:
  
  def __init__(self, context):
    self.sock = context['socket']

  def build_message(self, message_struct, params):
    """Return a packed representation of the given params mapped onto
    the given message struct."""    
    if not len(params) == len(message_struct):
      print "[!] Error building message: wrong number of parameters"
      sys.exit(1)
      
    message = tuple()
    format = '>'
    
    for member in message_struct:
      message += (params[member['name']],)
      if member.has_key('size'):
        if member['size'] == 'dlen':
          if member.has_key('offset'):
            format += str(params[member['size']] - member['offset']) \
                      + member['type']
          else:
            format += str(params[member['size']]) + member['type']
        else:
          format += str(member['size']) + member['type']
      else: 
        format += member['type']
    
    message = tuple(flatten(message))
    return struct.pack(format, *message)
    
  def send_message(self, message):
    """Send a packed binary message."""
    try:
      self.sock.send(message)
    except socket.error, e:
      print 'Error sending message: %s' % e
      sys.exit(1)
  
  def receive_message(self):
    """"""
    try:  
      message = self.sock.recv(4096)
    except socket.error, e:
      print 'Error receiving message: %s' % e
      sys.exit(1)
    return message   
  
  def unpack_response(self, response_raw, request_raw):
    """Return an unpacked named tuple representation of a server response."""    
    # Unpack the request that generated this response for reference
    request = self.unpack_request(request_raw)
    requestid = get_requestid(request.type)
    
    # Unpack the response header to find the status and data length
    header_struct = get_struct('ServerResponseHeader')
    format = '>' 
    for member in header_struct:
      format += member['type']
    header = struct.unpack(format + (str(len(response_raw) - 8) + 's'), 
                           response_raw)
    streamid = header[0]
    status = header[1]
    dlen = header[2]

    # Check if this is a handshake response
    if requestid == XProtocol.XRequestTypes.handshake:
      body_struct = get_struct('ServerInitHandShake')
    # Check if this is more than a simple kXR_ok response
    elif status != XProtocol.XResponseType.kXR_ok:
      body_struct = get_struct('ServerResponseBody_' \
                               + get_responseid(status)[4:].title())
    else:
      body_struct = get_struct('ServerResponseBody_' \
                               + request.type[4:].title())
      
    if not body_struct: body_struct = list()
    
    # Build complete format string
    format = '>'
    response_struct = header_struct + body_struct
    for member in response_struct:
      if member.has_key('size'):
        if member['size'] == 'dlen':
          if member.has_key('offset'):
            format += str(dlen - member['offset']) + member['type']
          else:       
            format += str(dlen) + member['type']
        else:
          format += str(member['size']) + member['type']
      else: 
        format += member['type']
    
    if len(body_struct) == 0 and dlen > 0:
      format += (str(dlen) + 's')
    
    # Unpack to regular tuple
    response_tuple = struct.unpack(format, response_raw)  
    # Convert to named tuple
    response = namedtuple('response', 
                          ' '.join([m['name'] for m in response_struct]))
    return response(*response_tuple)
  
  def unpack_request(self, request_raw):
    """Return an unpacked named tuple representation of a client request."""
    if not len(request_raw): return
    
    # Unpack the header to find the request ID
    format = '>HH' + (str(len(request_raw) - 4) + 's')
    header = struct.unpack(format, request_raw)  
    streamid = header[0]
    requestid = header[1]
    
    # Check if this is a handshake request
    if requestid == XProtocol.XRequestTypes.handshake:
      request_struct = get_struct('ClientInitHandShake')
    else:
      request_type = XProtocol.XRequestTypes.reverse_mapping[requestid]
      request_struct = get_struct('Client' + request_type[4:].title() 
                                     + 'Request')
      
    # Check if another request is being piggybacked
    if len(request_raw) > format_length(struct_format(request_struct)):
      format = struct_format(request_struct) + 'HH'
      requestid_2 = struct.unpack(format + str(len(request_raw) 
                                               - format_length(format)) + 's', 
                                  request_raw)[-2]
      request_type_2 = XProtocol.XRequestTypes.reverse_mapping[requestid_2]
      request_struct += get_struct('Client' + request_type_2[4:].title()  
                                   + 'Request')
  
    # Build the complete format string
    format = '>'
    for member in request_struct:
      if member.has_key('size'):
        if member['size'] == 'dlen':
          format += str(len(request_raw) - format_length(format)) \
                    + member['type']
        else:
          format += str(member['size']) + member['type']
      else: 
        format += member['type']
    
    # Unpack to a regular tuple
    request_tuple = struct.unpack(format, request_raw)
    
    # Convert to named tuple
    request_struct.insert(0, {'name': 'type'})
    if requestid == XProtocol.XRequestTypes.handshake:
      type = 'handshake'
    else:
      type = get_requestid(requestid)
    
    request = namedtuple('request', 
                         ' '.join([m['name'] for m in request_struct]))
    return request(type, *request_tuple) 
      

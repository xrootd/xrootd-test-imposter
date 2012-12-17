import sys
import struct
import socket

import XProtocol
from Utils import flatten, format_length

class MessageHelperException(Exception):
  """General Exception raised by MessageHelper."""
    
  def __init__(self, desc):
    """Construct an exception.

    @param desc: description of an error
    """
    self.desc = desc

  def __str__(self):
    """Return textual representation of an error."""
    return str(self.desc)


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
    
  def send_request(self, requestid, request):
    """Send a packed request and return a packed response."""
    try:
      self.sock.send(request)
    except socket.error, e:
      print 'Error sending %s request: %s' % (requestid, e)
      sys.exit(1)
    try:  
      response = self.sock.recv(4096)
    except socket.error, e:
      print 'Error receiving %s response: %s' % (requestid, e)
      sys.exit(1)
    return response    
  
  def send_response(self, response):
    try:
      self.sock.send(response)
    except socket.error, e:
      print 'Error sending response: %s' % e
      sys.exit(1)
  
  def receive_request(self, format):
    try:
      request = self.sock.recv(format_length(format))
    except socket.error, e:
      print 'Error receiving request: %s' % e
      sys.exit(1)
      
    return request
  
  def unpack_response(self, response, requestid):
    """Return an unpacked tuple representation of a server response."""
    header_struct = self.get_struct('ServerResponseHeader')
    format = '>'
    
    for member in header_struct:
      format += member['type']
    
    dlen = struct.unpack(format + ('s' * (len(response) - 8))
                                      , response)[2]
    
    body_struct = self.get_struct('ServerResponseBody_' + requestid[4:].title())
    if not body_struct: body_struct = list()
    
    for member in body_struct:
      if member.has_key('size'):
        format += str(member['size']) + member['type']
      else: 
        format += member['type']
        
    if not body_struct:
      format += (str(dlen) + 's')
    
    response = struct.unpack(format, response)
    return self.get_responseid(response[1]), response
  
  def unpack_request(self, request_raw):
    format = '>HH'
    request_type = struct.unpack(format
                                 + (str(len(request_raw) 
                                    - format_length(format)) + 's'), 
                                 request_raw)[1]
    request_type = XProtocol.XRequestTypes.reverse_mapping[request_type]
    request_struct = self.get_struct('Client' + 
                                        request_type[4:].title() + 
                                        'Request')
    
    format = '>'
    for member in request_struct:
      if member.has_key('size'):
        format += str(member['size']) + member['type']
      else: 
        format += member['type']

    return struct.unpack(format, request_raw)
  
  def get_struct(self, name):
    """Return a representation of a struct as a list of dicts."""
    if hasattr(XProtocol, name):
        return getattr(XProtocol, name)
    
  def get_requestid(self, requestid):
    """Return the integer request ID associated with the given string
    request ID.""" 
    if hasattr(XProtocol.XRequestTypes, requestid):
      return getattr(XProtocol.XRequestTypes, requestid)
    else:
      print "[!] Unknown request ID:", requestid
      sys.exit(1)
      
  def get_responseid(self, responseid):
    """Return the string response ID associated with the given integer
    response ID."""
    try:
      respid = XProtocol.XResponseType.reverse_mapping[responseid]
    except KeyError, e:
      print "[!] Unknown response ID:", responseid
      sys.exit(1) 
      
    return respid

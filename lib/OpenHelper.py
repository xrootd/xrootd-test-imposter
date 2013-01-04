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

import MessageHelper

from collections import namedtuple
from XProtocol import XOpenRequestOption
from XProtocol import XOpenRequestMode
from Utils import get_struct, get_responseid, format_length

class OpenHelper:
  """Class to aid in dealing with kXR_open request/responses."""
  
  def __init__(self, context):
    self.context = context
    self.mh = MessageHelper.MessageHelper(context)
    
  def unpack_response(self, response_raw, request_raw):
    """Return an unpacked named tuple representation of a kXR_open response."""
    request = self.mh.unpack_request(request_raw)
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Open')
    
    # Remove members from the response struct if the option was not given in
    # the request.
    response_struct[:] = [m for m in response_struct 
                          if self.option_included(m, request, response_raw)]
    # Extract the data length
    dlen = struct.unpack('>HHl' + (str(len(response_raw) - 8) + 's'), 
                          response_raw)[2]
    
    # Build the full format string
    format = '>'
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
    
    # Unpack to tuple
    response_tuple = struct.unpack(format, response_raw)
    # Convert to named tuple
    response_struct.insert(0, {'name': 'type'})
    type = get_responseid(response_tuple[1])
    response = namedtuple('response', 
                          ' '.join([m['name'] for m in response_struct]))
    return response(type, *response_tuple)
  
  def option_included(self, member, request, response_raw):
    """Return whether or not the given member will be in the given packed
    response, based upon the options bitmask in the request, and the size of
    the response."""
    if request.options & XOpenRequestOption.kXR_retstat:
      if member['name'] in ('cpsize', 'cptype', 'data'):
        return True
    
    if request.options & XOpenRequestOption.kXR_compress:
      if member['name'] in ('cpsize', 'cptype'):
        if len(response_raw) > 12:
          return True
        else: return False
      elif member['name'] == 'data':
        return False
    
    if member['name'] in ('cpsize', 'cptype', 'data'):
      return False
    else: return True
  
  
          
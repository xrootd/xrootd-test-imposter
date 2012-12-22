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

from lib.ClientRequestHelper import ClientRequestHelper

class XRootDLogInClient:
  @classmethod
  def getDescription(cls):
    return { 'type': 'Active', 'hostname': 'localhost', 'port': 1094, 
             'clients': 1, 'seclib': 'libXrdSec.so' }

  def __call__(self, context):
    client = ClientRequestHelper(context)
    
    client.do_full_handshake()
    
#     handshake_request = client.handshake(fifth=2013)
#     client.send(handshake_request)
#     response_raw = client.receive()
#     response = client.unpack(response_raw, handshake_request)
#     
#     client.protocol()
#     client.login(username='default', admin=False)
#     client.ping()
    

    stat_request = client.kXR_stat(path="/tmp")
    client.send(stat_request)
    response_raw = client.receive()
    status, response = client.unpack(response_raw, stat_request)
    print "kXR_stat response:\t", status, response
    
    
    
    
    
    

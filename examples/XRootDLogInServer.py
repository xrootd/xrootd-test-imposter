#-------------------------------------------------------------------------------
# Copyright (c) 2011-2012 by European Organization for Nuclear Research (CERN)
# Author: Lukasz Janyst <ljanyst@cern.ch>
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

from lib.ServerResponseHelper import ServerResponseHelper

class XRootDLogInServer:
  @classmethod
  def getDescription( cls ):
    return { 'type': 'Passive', 'ip': '0.0.0.0', 'port': 1094, 'clients': 1, 
             'seclib': 'libXrdSec.so', 
             'sec.protocol': 'gsi' }

  def __call__( self, context ):
    server = ServerResponseHelper(context)
    
    server.do_full_handshake()
    
    for request in iter(server.get_request()):
      if request['type'] == 'stat':
        response = server.stat(id=0, size=0, flags=0, modtime=0)
        server.send(response)
    
#     server.protocol()
#     server.login()
#     server.auth()
#     server.stat()
    
    server.close()
    
    
    
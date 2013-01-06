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

from lib.ImposterServer import ImposterServer
from lib.XProtocol import XResponseType

class XRootDLogInServer:
  @classmethod
  def getDescription( cls ):
    return { 'type': 'Passive', 'ip': '0.0.0.0', 'port': 1094, 'clients': 1, 
             'seclib': 'libXrdSec.dylib', 'sec.protocol': 'unix' }

  def __call__( self, context ):
    server = ImposterServer(context)
    
    server.do_full_handshake(verify_auth=True)
    for request in server.receive():
      
      if request.type == 'kXR_stat':
        print request
        #response = server.kXR_stat(id=0, size=0, flags=0, modtime=0)
        #response = server.kXR_error(errmsg='foobar')
        #response = server.kXR_redirect(host='localhost')
        #response = server.kXR_wait(seconds=5, infomsg='foobar')
        #response = server.kXR_waitresp(seconds=5)
        response = server.kXR_attn_asynresp(rstatus=XResponseType.kXR_error, rdata='foobar')
        server.send(response)
        
#      if request.type == 'kXR_mkdir':
#        print request
#        response = server.kXR_stat(id=0, size=0, flags=0, modtime=0)
#        server.send(response)
    
    server.close()
    
    
    
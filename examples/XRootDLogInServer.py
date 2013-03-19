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

from XrdImposter.ImposterServer import ImposterServer
from XrdImposter.XProtocol import XResponseType

class XRootDLogInServer:
  @classmethod
  def getDescription( cls ):
    config = """
    xrootd.seclib /usr/lib64/libXrdSec.so
    sec.protocol gsi
    sec.protocol unix
    """

    return { 'type': 'Passive', 'ip': '0.0.0.0', 'port': 1095, 'clients': 1, 
             'config': config }

  def __call__( self, context ):
    server = ImposterServer(context)

    # The following line will to the equivalent of the rest of this method,
    # using sensible default values and optionally fully authenticating.
    #
    # server.do_full_handshake(verify_auth=True)
    for request in server.receive():

      if request.type == 'handshake':
        print request
        server.send(server.handshake())
        
      if request.type == 'kXR_protocol':
        print request
        server.send(server.kXR_protocol(streamid=request.streamid))

      elif request.type == 'kXR_login':
        print request
        server.send(server.kXR_login(streamid=request.streamid))

      elif request.type == 'kXR_auth':
        # Authenticate this request's credentials and potentially get
        # continuation (authmore) parameters
        contparams = server.authenticate(request.cred)
        if contparams:
          # Send an authmore if necessary
          response = server.kXR_authmore(streamid=request.streamid, 
                                       data=contparams)
        else:
          # We are done authenticating
          response = server.kXR_ok(streamid=request.streamid)

        server.send(response)
        # If we have contparams, there will be more auth-related requests 
        # to receive at this stage. Otherwise, we are done
        if not contparams: continue

      elif request.type == 'kXR_stat':
        print request
        server.send(server.kXR_stat())

    server.close()

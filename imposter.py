#!/usr/bin/env python
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

import getopt
import sys
import socket

from threading import Thread

#-------------------------------------------------------------------------------
def printHelp():
  print "Usage:"
  print "  imposter.py"
  print "    --scenario=ClassName name of the class defining the interaction scenario"
  print "    --libpath=path       path containing the interation definitions"
  print "    --help               print this help message"

#-------------------------------------------------------------------------------
class SocketHandler( Thread ):
  #-----------------------------------------------------------------------------
  def __init__( self, scenario, context ):
    Thread.__init__( self )
    self.scenario = scenario
    self.context  = context

  #-----------------------------------------------------------------------------
  def run( self ):
    self.scenario( self.context )

#-------------------------------------------------------------------------------
def runPassive( scenario ):

  #-----------------------------------------------------------------------------
  # Get the necessary information from the scenario description
  #-----------------------------------------------------------------------------
  desc = scenario.getDescription()

  try:
    listenIP   = desc['ip']
    listenPort = desc['port']
    numClients = desc['clients']
  except KeyError, err:
    print "[!] Info missing in scenario description:", err
    return 10

  #-----------------------------------------------------------------------------
  # Listen to the incoming connections
  #-----------------------------------------------------------------------------
  try:
    serverSocket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    serverSocket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
    serverSocket.bind( (listenIP, listenPort) )
    serverSocket.listen( 5 )
  except socket.error, e:
      print "[!] Socket error:", e
      return 11
      
  threads = []
  for i in range( numClients ):
    (clientSocket, address) = serverSocket.accept()
    context = {'socket': clientSocket, 'address': address, 'number': i}

    scObj = scenario()
    if not callable( scObj ):
      print "[!] The scenario is not callable"
      return 12

    ct = SocketHandler( scObj, context )
    threads.append( ct )
    ct.start()

  #-----------------------------------------------------------------------------
  # Join the running threads
  #-----------------------------------------------------------------------------
  for ct in threads:
    ct.join()

#-------------------------------------------------------------------------------
def runActive( scenario ):

  #-----------------------------------------------------------------------------
  # Get the necessary information from the scenario description
  #-----------------------------------------------------------------------------
  desc = scenario.getDescription()

  try:
    hostName   = desc['hostname']
    hostPort   = desc['port']
    numClients = desc['clients']
  except KeyError, err:
    print "[!] Info missing in scenario description:", err
    return 10

  #-----------------------------------------------------------------------------
  # Create the clients
  #-----------------------------------------------------------------------------
  threads = []
  for i in range( numClients ):
    try:
      clientSocket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
      clientSocket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
      clientSocket.connect( (hostName, hostPort) )
    except socket.error, err:
      print "[!] Socket error:", err
      return 11

    context = {'socket': clientSocket, 'streamid': i}

    scObj = scenario()
    if not callable( scObj ):
      print "[!] The scenario is not callable"
      return 12

    ct = SocketHandler( scObj, context )
    threads.append( ct )
    ct.start()

  #-----------------------------------------------------------------------------
  # Join the running threads
  #-----------------------------------------------------------------------------
  for ct in threads:
    ct.join()

#-------------------------------------------------------------------------------
def main():

  #-----------------------------------------------------------------------------
  # Parse the commandline
  #-----------------------------------------------------------------------------
  try:
    opts, args = getopt.getopt( sys.argv[1:], "",
                                ["help", "scenario=", "libpath="] )
  except getopt.GetoptError, err:
    print "[!] Unable to parse commandline:", err
    printHelp()
    return 2

  libPath   = None
  className = None
  for o, a in opts:
    if o == "--help":
      printHelp()
      sys.exit()
    elif o == "--libpath":
      libPath = a
    elif o == "--scenario":
      className = a
    else:
      assert False, "unhandled option"

  if not className:
    print "[!] No imposter scenario has been defined"
    return 3

  #-----------------------------------------------------------------------------
  # Load the module and see whether we need to act on passive or active
  # scenarios
  #-----------------------------------------------------------------------------
  if libPath:
    sys.path.append( libPath )

  try:
    scenarioModule = __import__( className )
  except ImportError, err:
    print "[!] Unable to load %s: %s" % (className, err)
    return 4

  #-----------------------------------------------------------------------------
  # Get the scenario and act accordingly
  #-----------------------------------------------------------------------------
  try:
    scenario = getattr( scenarioModule, className )
  except AttributeError, err:
    print "[!] Unable to load %s: %s" % (className, err)
    return 5

  if not hasattr( scenario, 'getDescription' ):
    print "[!] Unable to get scenario description: no getDescription attribute"
    return 6

  desc = scenario.getDescription()
  if not 'type' in desc.keys():
    print "[!] Scenario type is not defined"
    return 7

  if desc['type'] == 'Active':
    return runActive( scenario )
  elif desc['type'] == 'Passive':
    return runPassive( scenario )
  else:
    print "[!] Unknown type of scenario:", desc['type']
    return 8

#-------------------------------------------------------------------------------
if __name__ == "__main__":
  sys.exit( main() )

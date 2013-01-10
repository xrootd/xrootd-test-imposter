//------------------------------------------------------------------------------
// Copyright (c) 2011-2012 by European Organization for Nuclear Research (CERN)
// Author: Justin Salmon <jsalmon@cern.ch>
//------------------------------------------------------------------------------
// XRootD is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// XRootD is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with XRootD.  If not, see <http://www.gnu.org/licenses/>.
//------------------------------------------------------------------------------

#include <Python.h>
#include <string>
#include <iostream>
#include <fstream>
#include <sstream>
#include <stdio.h>
#include <dlfcn.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>

#include <XrdSec/XrdSecInterface.hh>
#include <XrdOuc/XrdOucEnv.hh>
#include <XrdOuc/XrdOucErrInfo.hh>
#include <XrdSys/XrdSysLogger.hh>


PyObject* AuthenticationError;

XrdSecProtocol *authProtocol;
XrdOucEnv *authEnv;
XrdSysLogger logger;
std::string protocolName;

const char *host = "localhost";
const char *config;
const char *authLibName;
void *libHandle;

int sock;
struct sockaddr_in *sockadd;

// Authentication function handles
typedef XrdSecProtocol *(*XrdSecGetProt_t)(const char *, const sockaddr &,
        const XrdSecParameters &, XrdOucErrInfo *);
typedef XrdSecService *(*XrdSecGetServ_t)(XrdSysLogger *, const char *);



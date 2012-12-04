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
#include <sstream>
#include <dlfcn.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>

#include "xrootd/XrdSec/XrdSecInterface.hh"
#include "xrootd/XrdOuc/XrdOucEnv.hh"
#include "xrootd/XrdOuc/XrdOucErrInfo.hh"

using namespace std;

//------------------------------------------------------------------------
// Get the authentication function handle
//------------------------------------------------------------------------
typedef XrdSecProtocol *(*XrdSecGetProt_t)(const char *, const sockaddr &,
		const XrdSecParameters &, XrdOucErrInfo *);

extern "C" {

static PyObject* get_credentials(PyObject *self, PyObject *args) {

	int sock;
	struct sockaddr_in *sockadd;
	const char* authBuffer;
	const char* authLibName;
	string protocolName;
	stringstream err;
	XrdSecCredentials *credentials = 0;
	XrdSecParameters *authParams;
	XrdSecProtocol *authProtocol;
	XrdOucEnv *authEnv;

	// Parse the python parameters
	if (!PyArg_ParseTuple(args, "ssi", &authBuffer, &authLibName, &sock))
		return NULL;

	// Create a sockaddr_in from the socket descriptor given
	socklen_t socklen = sizeof(struct sockaddr_in);
	sockadd = (sockaddr_in*) malloc(sizeof(struct sockaddr_in));
	getsockname(sock, (sockaddr*) sockadd, &socklen);
	size_t authBuffLen = strlen(authBuffer);

	// Prepare some variables
	authEnv = new XrdOucEnv();
	authEnv->Put("sockname", "");
	XrdOucErrInfo ei("", authEnv);
	authParams = new XrdSecParameters((char*) authBuffer, authBuffLen);

	//--------------------------------------------------------------------------
	// dlopen the library
	//--------------------------------------------------------------------------
	void *pSecLibHandle = ::dlopen(authLibName, RTLD_NOW);
	if (!pSecLibHandle) {
		err << "Unable to load the authentication library " << authLibName
				<< ": " << ::dlerror() << std::endl;
		PyErr_SetString(PyExc_IOError, err.str().c_str());
		return NULL;
	}

	//--------------------------------------------------------------------------
	// Get the authentication function handle
	//--------------------------------------------------------------------------
	XrdSecGetProt_t authHandler = (XrdSecGetProt_t) dlsym(pSecLibHandle,
			"XrdSecGetProtocol");
	if (!authHandler) {
		err << "Unable to get the XrdSecGetProtocol symbol from library "
				<< authLibName << ": " << ::dlerror() << endl;
		PyErr_SetString(PyExc_IOError, err.str().c_str());
		::dlclose(pSecLibHandle);
		pSecLibHandle = 0;
		return NULL;
	}

	//--------------------------------------------------------------------------
	// Loop over the possible protocols to find one that gives us valid
	// credentials
	//--------------------------------------------------------------------------
	while (1) {
		//------------------------------------------------------------------------
		// Get the protocol
		//------------------------------------------------------------------------
		authProtocol = (*authHandler)("localhost", *((sockaddr*) sockadd),
				*authParams, 0);
		if (!authProtocol) {
			err << "No protocols left to try" << endl;
			PyErr_SetString(PyExc_IOError, err.str().c_str());
			return NULL;
		}

		protocolName = authProtocol->Entity.prot;
		cout << "Trying to authenticate using " << protocolName.c_str() << endl;

		//------------------------------------------------------------------------
		// Get the credentials from the current protocol
		//------------------------------------------------------------------------
		credentials = authProtocol->getCredentials(0, &ei);
		if (!credentials) {
			cout << "Cannot get credentials for protocol "
					<< protocolName.c_str() << ": " << ei.getErrText() << endl;
			authProtocol->Delete();
			continue;
		} else
			break;
	}

	return Py_BuildValue("ssi", protocolName.c_str(),
						  credentials->buffer,
						  credentials->size);
}
}

static PyMethodDef SpamMethods[] = {
	{ "get_credentials", get_credentials, METH_VARARGS,
			"Get opaque credentials object." },
	{ NULL, NULL, 0, NULL } /* Sentinel */
};

PyMODINIT_FUNC initauthbind(void) {
	(void) Py_InitModule("authbind", SpamMethods);
}

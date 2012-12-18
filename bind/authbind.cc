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

#include "xrootd/XrdSec/XrdSecInterface.hh"
#include "xrootd/XrdOuc/XrdOucEnv.hh"
#include "xrootd/XrdOuc/XrdOucErrInfo.hh"
#include "xrootd/XrdSys/XrdSysLogger.hh"

using namespace std;

//------------------------------------------------------------------------------
// Get the authentication function handle
//------------------------------------------------------------------------------
typedef XrdSecProtocol *(*XrdSecGetProt_t)(const char *, const sockaddr &,
		const XrdSecParameters &, XrdOucErrInfo *);

typedef XrdSecService *(*XrdSecGetServ_t)(XrdSysLogger *, const char *);

extern "C" {
static PyObject* get_parms(PyObject *self, PyObject *args) {

	int i;
	const char *host = "localhost";
	const char *secConfig;
	const char *authLibName;
	const char *tempConfFile;
	stringstream err;

	XrdSysLogger logger;
	XrdSecService *securityService;

	// Parse the python parameters
	if (!PyArg_ParseTuple(args, "ss", &secConfig, &authLibName))
		return NULL;

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
	XrdSecGetServ_t authHandler = (XrdSecGetServ_t) dlsym(pSecLibHandle,
			"XrdSecgetService");
	if (!authHandler) {
		err << "Unable to get the XrdSecgetService symbol from library "
				<< authLibName << ": " << ::dlerror() << endl;
		PyErr_SetString(PyExc_IOError, err.str().c_str());
		::dlclose(pSecLibHandle);
		pSecLibHandle = 0;
		return NULL;
	}

	//--------------------------------------------------------------------------
	// Write the temporary config file
	//--------------------------------------------------------------------------
	tempConfFile = tmpnam(NULL);
	ofstream out(tempConfFile);
	out << secConfig;
	out.close();

	setenv("XRDINSTANCE", "imposter", 1);

	//----------------------------------------------------------------------
	// Get the security service object
	//----------------------------------------------------------------------
	securityService = (*authHandler)(&logger, tempConfFile);
	if (!securityService) {
		err << "Unable to create security service." << endl;
		PyErr_SetString(PyExc_IOError, err.str().c_str());
		return NULL;
	}

	const char *token = securityService->getParms(i, host);
	if (!token) {
		err << "No security token for " << host << endl;
		PyErr_SetString(PyExc_IOError, err.str().c_str());
		return NULL;
	}

	cout << "Sec token='" << token << "'" << endl;
	return Py_BuildValue("s", token);
}
}

extern "C" {
static PyObject* authenticate(PyObject *self, PyObject *args) {

	int sock;
	struct sockaddr_in *sockadd;
	PyByteArrayObject *creds;
	const char *authLibName;
	const char *confFile;
	const char *tempConfFile;
	string protocolName;
	stringstream err;

	XrdSecCredentials *credentials = 0;
	XrdSecParameters *authParams;
	XrdSecProtocol *authProtocol;
	XrdOucEnv *authEnv;
	XrdSysLogger logger;
	XrdSecService *securityService;

	// Parse the python parameters
	if (!PyArg_ParseTuple(args, "Ossi", &creds, &authLibName, &confFile, &sock))
		return NULL;

	//PyObject_Print((PyObject*) creds, stdout, 0);
	char* credsCopy;
	credsCopy = PyByteArray_AsString((PyObject*) creds);
	size_t credLen = strlen(credsCopy);

	// Prepare some variables
	authEnv = new XrdOucEnv();
	authEnv->Put("sockname", "");
	XrdOucErrInfo ei("", authEnv);
	credentials = new XrdSecCredentials((char*) credsCopy, credLen);

	// Create a sockaddr_in from the socket descriptor given
	socklen_t socklen = sizeof(struct sockaddr_in);
	sockadd = (sockaddr_in*) malloc(sizeof(struct sockaddr_in));
	getsockname(sock, (sockaddr*) sockadd, &socklen);

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
	XrdSecGetServ_t authHandler = (XrdSecGetServ_t) dlsym(pSecLibHandle,
			"XrdSecgetService");
	if (!authHandler) {
		err << "Unable to get the XrdSecgetService symbol from library "
				<< authLibName << ": " << ::dlerror() << endl;
		PyErr_SetString(PyExc_IOError, err.str().c_str());
		::dlclose(pSecLibHandle);
		pSecLibHandle = 0;
		return NULL;
	}

	//--------------------------------------------------------------------------
	// Write the temporary config file
	//--------------------------------------------------------------------------
	tempConfFile = tmpnam(NULL);
	ofstream out(tempConfFile);
	out << confFile;
	out.close();

	// Need to set XRDINSTANCE, as we are poking in through the shared lib and
	// don't actually have an xrootd instance
	setenv("XRDINSTANCE", "imposter", 1);

	//----------------------------------------------------------------------
	// Get the security service object
	//----------------------------------------------------------------------
	securityService = (*authHandler)(&logger, tempConfFile);
	if (!securityService) {
		cerr << "Unable to create security service." << endl;
		exit(1);
	}

	//----------------------------------------------------------------------
	// Get the protocol
	//----------------------------------------------------------------------
	authProtocol = securityService->getProtocol((const char *) "localhost",
			(const sockaddr &) sockadd, (const XrdSecCredentials *) credentials,
			&ei);
	if (!authProtocol) {
		err << "getProtocol error: " << ei.getErrText() << endl;
		PyErr_SetString(PyExc_IOError, err.str().c_str());
		return NULL;
	}

	//----------------------------------------------------------------------
	// Now authenticate the credentials
	//----------------------------------------------------------------------
	if (authProtocol->Authenticate(credentials, &authParams, &ei) < 0) {
		cout << "Authentication error: " << ei.getErrText() << endl;
		authProtocol->Delete();
	}
	cout << "authenticated successfully with " << credentials->buffer << endl;

	// Don't need to return anything
	return Py_BuildValue("");
}
}

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

	// Prepare some variables
	authEnv = new XrdOucEnv();
	authEnv->Put("sockname", "");
	XrdOucErrInfo ei("", authEnv);
	size_t authBuffLen = strlen(authBuffer);
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
		//----------------------------------------------------------------------
		// Get the protocol
		//----------------------------------------------------------------------
		authProtocol = (*authHandler)("localhost", *((sockaddr*) sockadd),
				*authParams, 0);
		if (!authProtocol) {
			err << "No protocols left to try" << endl;
			PyErr_SetString(PyExc_IOError, err.str().c_str());
			return NULL;
		}

		protocolName = authProtocol->Entity.prot;
		cout << "Trying to authenticate using " << protocolName.c_str() << endl;

		//----------------------------------------------------------------------
		// Get the credentials from the current protocol
		//----------------------------------------------------------------------
		credentials = authProtocol->getCredentials(0, &ei);
		if (!credentials) {
			cout << "Cannot get credentials for protocol "
					<< protocolName.c_str() << ": " << ei.getErrText() << endl;
			authProtocol->Delete();
			continue;
		} else
			break;
	}

	return Py_BuildValue("ssi", protocolName.c_str(), credentials->buffer,
			credentials->size);

}
}

static PyMethodDef AuthBindMethods[] = { { "get_credentials", get_credentials,
		METH_VARARGS, "Get opaque credentials object." }, { "authenticate",
		authenticate, METH_VARARGS,
		"Authenticate credentials provided by a client." }, { "get_parms",
		get_parms, METH_VARARGS, "Get a security token for a login response." },
		{ NULL, NULL, 0, NULL } /* Sentinel */
};

PyMODINIT_FUNC initauthbind(void) {
	(void) Py_InitModule("authbind", AuthBindMethods);
}

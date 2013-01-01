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

#include "authbind.hh"

using namespace std;


/**
 * Open a shared library using dlopen.
 *
 * @param libName name of the library to open.
 * @return handle to the open library on success, 0 on failure.
 */
void *openLibrary(const char* libName) {
    void *libHandle = ::dlopen(libName, RTLD_NOW);
    if (!libHandle) {
        err << "Unable to load library " << libName << ": "
                  << ::dlerror() << endl;
        PyErr_SetString(PyExc_IOError, err.str().c_str());
        return 0;
    }
    return libHandle;
}

/**
 * Create a temporary file in /tmp.
 *
 * @param data pointer to the char data to write to the file.
 * @return the filename of the newly created temporary file.
 */
const char *writeTempFile(const char* data) {
    const char *tempFileName = tmpnam(NULL);
    ofstream out(tempFileName);
    out << data; out.close();
    return tempFileName;
}

/**
 *
 */
void createSock(int sock) {
    // Create a sockaddr_in from the socket descriptor given
    socklen_t socklen = sizeof(struct sockaddr_in);
    sockadd = (sockaddr_in*) malloc(sizeof(struct sockaddr_in));
    getsockname(sock, (sockaddr*) sockadd, &socklen);
}


extern "C" {

/**
 *
 */
static PyObject* get_parms(PyObject *self, PyObject *args) {

    XrdSecService *securityService;

    // Parse the python parameters
    if (!PyArg_ParseTuple(args, "ss", &config, &authLibName))
        return NULL;

    // dlopen the library
    if (!(libHandle = openLibrary(authLibName))) {
        return NULL;
    }

    // Get the authentication function handle
    XrdSecGetServ_t authHandler = (XrdSecGetServ_t) dlsym(libHandle,
            "XrdSecgetService");
    if (!authHandler) {
        err << "Unable to get the XrdSecgetService symbol from library "
                << authLibName << ": " << ::dlerror() << endl;
        PyErr_SetString(PyExc_IOError, err.str().c_str());
        ::dlclose(libHandle);
        libHandle = 0;
        return NULL;
    }

    // Write the temporary config file
    const char *tempConfFile = writeTempFile(config);

    // Get the security service object
    securityService = (*authHandler)(&logger, tempConfFile);
    if (!securityService) {
        err << "Unable to create security service" << endl;
        PyErr_SetString(PyExc_IOError, err.str().c_str());
        return NULL;
    }

    // Get the security token
    int tokenSize;
    const char *token = securityService->getParms(tokenSize, host);
    if (!token) {
        err << "No security token for " << host << endl;
        PyErr_SetString(PyExc_IOError, err.str().c_str());
        return NULL;
    }

    return Py_BuildValue("s", token);
}


/**
 *
 */
static PyObject* authenticate(PyObject *self, PyObject *args) {

    const char *creds;
    int credsLen;

    XrdSecCredentials *credentials = 0;
    XrdSecParameters *authParams;
    XrdSecProtocol *authProtocol;
    XrdSecService *securityService;

    // Parse the python parameters
    if (!PyArg_ParseTuple(args, "z#ssi", &creds, &credsLen, &authLibName,
            &config, &sock))
        return NULL;

    // Prepare some variables
    authEnv = new XrdOucEnv();
    authEnv->Put("sockname", "");
    XrdOucErrInfo ei("", authEnv);
    credentials = new XrdSecCredentials((char*) creds, credsLen);
    createSock(sock);

    // dlopen the library
    if (!(libHandle = openLibrary(authLibName))) {
        return NULL;
    }

    // Get the authentication function handle
    XrdSecGetServ_t authHandler = (XrdSecGetServ_t) dlsym(libHandle,
            "XrdSecgetService");
    if (!authHandler) {
        err << "Unable to get the XrdSecgetService symbol from library "
                << authLibName << ": " << ::dlerror() << endl;
        PyErr_SetString(PyExc_IOError, err.str().c_str());
        ::dlclose(libHandle);
        libHandle = 0;
        return NULL;
    }

    // Write the temporary config file
    const char *tempConfFile = writeTempFile(config);

    // Get the security service object
    securityService = (*authHandler)(&logger, tempConfFile);
    if (!securityService) {
        err << "Unable to create security service" << endl;
        PyErr_SetString(PyExc_IOError, err.str().c_str());
        return NULL;
    }

    // Get the protocol
    authProtocol = securityService->getProtocol((const char *) host,
            (const sockaddr &) sockadd, (const XrdSecCredentials *) credentials,
            &ei);
    if (!authProtocol) {
        err << "getProtocol error: " << ei.getErrText() << endl;
        PyErr_SetString(PyExc_IOError, err.str().c_str());
        return NULL;
    }

    // Now authenticate the credentials
    if (authProtocol->Authenticate(credentials, &authParams, &ei) < 0) {
        authProtocol->Delete();
        err << "Authentication error: " << ei.getErrText() << endl;
        PyErr_SetString(PyExc_IOError, err.str().c_str());
        return NULL;
    }

    cout << "authenticated successfully with " << credentials->buffer << endl;
    // Don't need to return anything
    return Py_BuildValue("");
}


/**
 *
 */
static PyObject* get_credentials(PyObject *self, PyObject *args) {

    const char* authToken;
    int authTokenLen;

    const char *contCred;
    int contCredLen;

    XrdSecCredentials *credentials = 0;
    XrdSecParameters *authParams;

    // Parse the python parameters
    if (!PyArg_ParseTuple(args, "z#z#si", &authToken, &authTokenLen, &contCred,
            &contCredLen, &authLibName, &sock))
        return NULL;

    // Prepare some variables
    authEnv = new XrdOucEnv();
    authEnv->Put("sockname", "");
    XrdOucErrInfo ei("", authEnv);
    createSock(sock);

    if (authToken != NULL) {
        authParams = new XrdSecParameters((char*) authToken, authTokenLen);
    }

    // Check if this is an authmore call, i.e. we have continuation credentials
    if (authProtocol && (contCred != NULL)) {
        XrdSecParameters *secToken = new XrdSecParameters((char*) contCred,
                contCredLen);

        credentials = authProtocol->getCredentials(secToken, &ei);
        if (!credentials) {
            err << "Unable to get continuation credentials: " << ei.getErrText()
                    << endl;
            PyErr_SetString(PyExc_IOError, err.str().c_str());
            return NULL;
        }

        return Py_BuildValue("ss#", protocolName.c_str(), credentials->buffer,
                credentials->size);
    }

    // dlopen the library
    if (!(libHandle = openLibrary(authLibName))) {
        return NULL;
    }

    // Get the authentication function handle
    XrdSecGetProt_t authHandler = (XrdSecGetProt_t) dlsym(libHandle,
            "XrdSecGetProtocol");
    if (!authHandler) {
        err << "Unable to get the XrdSecGetProtocol symbol from library "
                << authLibName << ": " << ::dlerror() << endl;
        PyErr_SetString(PyExc_IOError, err.str().c_str());
        ::dlclose(libHandle);
        libHandle = 0;
        return NULL;
    }

    // Loop over the possible protocols to find one that gives us valid
    // credentials
    while (1) {
        // Get the protocol
        authProtocol = (*authHandler)(host, *((sockaddr*) sockadd), *authParams,
                0);
        if (!authProtocol) {
            err << "No protocols left to try" << endl;
            PyErr_SetString(PyExc_IOError, err.str().c_str());
            return NULL;
        }

        protocolName = authProtocol->Entity.prot;
        cout << "Trying to get credentials for protocol: "
                << protocolName.c_str() << endl;

        // Get the credentials from the current protocol
        credentials = authProtocol->getCredentials(0, &ei);
        if (!credentials) {
            cout << "Cannot get credentials for protocol "
                    << protocolName.c_str() << ": " << ei.getErrText() << endl;
            authProtocol->Delete();
            continue;
        } else
            break;
    }

    cout << "Successfully got credentials for protocol: "
            << protocolName.c_str() << endl;

    return Py_BuildValue("ss#", protocolName.c_str(), credentials->buffer,
            credentials->size);
}
}

static PyMethodDef AuthBindMethods[] = {
        { "get_credentials", get_credentials, METH_VARARGS,
          "Get opaque credentials objector continuation credentials." },
        { "authenticate", authenticate, METH_VARARGS,
          "Authenticate credentials provided by a client." },
        { "get_parms", get_parms, METH_VARARGS,
          "Get a security token for a login response." },
        { NULL, NULL, 0, NULL } /* Sentinel */
};

PyMODINIT_FUNC initauthbind(void) {
    (void) Py_InitModule("authbind", AuthBindMethods);

    // Set some environment vars
    setenv("XRDINSTANCE", "imposter", 1);
    setenv("XrdSecDEBUG", "1", 1);
}

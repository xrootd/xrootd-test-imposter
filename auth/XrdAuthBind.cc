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

#include "XrdAuthBind.hh"

using namespace std;

/**
 * Open a shared library using dlopen.
 *
 * @param libName name of the library to open.
 * @return handle to the open library on success, 0 on failure. On failure,
 *         PyErr_SetString will also be called, so the calling function can
 *         return NULL and propagate this error.
 */
void *openLibrary(const char* libName)
{
    std::stringstream err;
    void *libHandle = ::dlopen(libName, RTLD_NOW);
    if (!libHandle)
    {
        err << "Unable to load library " << libName << ": " << ::dlerror()
                << endl;
        PyErr_SetString(AuthenticationError, err.str().c_str());
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
const char *writeTempFile(const char* data)
{
    const char *tempFileName = tmpnam(NULL);
    ofstream out(tempFileName);
    out << data;
    out.close();
    return tempFileName;
}

/**
 * Fill a sockaddr_in struct from the socket descriptor given using
 * getsockname().
 *
 * @param sock the socket file descriptor to use.
 */
void getSockName(int sock)
{
    socklen_t socklen = sizeof(struct sockaddr_in);
    sockadd = (sockaddr_in*) malloc(sizeof(struct sockaddr_in));
    getsockname(sock, (sockaddr*) sockadd, &socklen);
}

/**
 * Fill a sockaddr_in struct from the socket descriptor given using
 * getpeername().
 *
 * @param sock the socket file descriptor to use.
 */
void getPeerName(int sock)
{
    socklen_t socklen = sizeof(struct sockaddr_in);
    sockadd = (sockaddr_in*) malloc(sizeof(struct sockaddr_in));
    getpeername(sock, (sockaddr*) sockadd, &socklen);
}

extern "C" {

/**
 *
 */
static PyObject* init(PyObject *self, PyObject *args)
{
    return Py_BuildValue("");
}

/**
 * Build a security token to send as a response to a kXR_login request,
 * if the given sec.protocol configuration directive is not empty.
 *
 * @param args the Python tuple containing the configuration directive
 *             and the authentication library name.
 * @throw IOError on error.
 * @return the security token that was built.
 */
static PyObject* get_parms(PyObject *self, PyObject *args)
{

    XrdSecService *securityService;
    std::stringstream err;

    // Parse the python parameters
    if (!PyArg_ParseTuple(args, "ss", &config, &authLibName))
        return NULL;

    // dlopen the library
    if (!(libHandle = openLibrary(authLibName)))
    {
        return NULL;
    }

    // Get the authentication function handle
    XrdSecGetServ_t authHandler = (XrdSecGetServ_t) dlsym(libHandle,
            "XrdSecgetService");
    if (!authHandler)
    {
        err << "Unable to get the XrdSecgetService symbol from library "
        << authLibName << ": " << ::dlerror() << endl;
        ::dlclose(libHandle);
        libHandle = 0;
        return PyErr_Format(AuthenticationError, err.str().c_str());;
    }

    // Write the temporary config file
    const char *tempConfFile = writeTempFile(config);

    // Get the security service object
    securityService = (*authHandler)(&logger, tempConfFile);
    if (!securityService)
    {
        err << "Unable to create security service" << endl;
        ::dlclose(libHandle);
        libHandle = 0;
        return PyErr_Format(AuthenticationError, err.str().c_str());;
    }

    // Get the security token
    int tokenSize;
    const char *token = securityService->getParms(tokenSize, host);
    if (!token)
    {
        err << "No security token for " << host << endl;
        return PyErr_Format(AuthenticationError, err.str().c_str());;
    }

    // Return the security token
    return Py_BuildValue("s", token);
}

/**
 * Authenticate a client's credentials which were supplied via a kXR_auth
 * request.
 *
 * @param args the Python tuple containing the credential string, the length
 *             of the credentials, the name of the authentication shared
 *             library, the sec.protocol directive and the client socket file
 *             descriptor.
 * @throw IOError on error or invalid credentials.
 * @return NULL on success and no further authentication needed, continuation
 *         parameters and their length on success and more authentication
 *         needed.
 */
static PyObject* authenticate(PyObject *self, PyObject *args)
{

    const char *creds;
    int credsLen;

    XrdSecCredentials *credentials = 0;
    XrdSecParameters *contParams;
    XrdSecService *securityService;
    std::stringstream err;

    // Parse the python parameters
    if (!PyArg_ParseTuple(args, "z#ssi", &creds, &credsLen, &authLibName,
            &config, &sock))
        return NULL;

    // Prepare some variables
    authEnv = new XrdOucEnv();
    authEnv->Put("sockname", "");
    XrdOucErrInfo ei("", authEnv);
    credentials = new XrdSecCredentials((char*) creds, credsLen);
    getPeerName(sock);

    // dlopen the library
    if (!(libHandle = openLibrary(authLibName)))
    {
        return NULL;
    }

    // Get the authentication function handle
    XrdSecGetServ_t authHandler = (XrdSecGetServ_t) dlsym(libHandle,
            "XrdSecgetService");
    if (!authHandler)
    {
        err << "Unable to get the XrdSecgetService symbol from library "
                << authLibName << ": " << ::dlerror() << endl;
        ::dlclose(libHandle);
        libHandle = 0;
        return PyErr_Format(AuthenticationError, err.str().c_str());;
    }

    // Write the temporary config file
    const char *tempConfFile = writeTempFile(config);

    // Get the security service object
    securityService = (*authHandler)(&logger, tempConfFile);
    if (!securityService)
    {
        err << "Unable to create security service" << endl;
        return PyErr_Format(AuthenticationError, err.str().c_str());;
    }

    // Get the protocol (unless it already exists)
    if (!authProtocol)
    {
        authProtocol = securityService->getProtocol((const char *) host,
                (const sockaddr &) *sockadd,
                (const XrdSecCredentials *) credentials, &ei);
    }

    if (!authProtocol)
    {
        err << "getProtocol error: " << ei.getErrText() << endl;
        return PyErr_Format(AuthenticationError, err.str().c_str());;
    }

    // Now authenticate the credentials
    int authResult = authProtocol->Authenticate(credentials, &contParams, &ei);
    if (authResult < 0)
    {
        authProtocol->Delete();
        err << "Authentication error: " << ei.getErrText() << endl;
        return PyErr_Format(AuthenticationError, err.str().c_str());;
    }
    else if (authResult > 0)
    {
        return Py_BuildValue("s#", contParams->buffer, contParams->size);
    }
    else
    {
        return Py_BuildValue("");
    }
}

/**
 * Try to get an initial credentials object for any supported protocol (prompted
 * by a kXR_auth response), or a continuation credentials object (prompted by a
 * kXR_authmore response).
 *
 * On the first call to this method, the args tuple should contain the
 * authToken variable, and the contCred variable should be null. On subsequent
 * calls, the opposite should be true.
 *
 * @param args the Python tuple containing (potentially) the security token, the
 *             length of the security token, the continuation credentials, the
 *             continuation credential length, the name of the authentication
 *             library and the client socket file descriptor.
 * @throw IOError on error or credentials cannot be acquired for any protocols.
 * @return name of the successful protocol, the opaque credentials string and
 *         length of the credentials on success.
 */
static PyObject* get_credentials(PyObject *self, PyObject *args)
{

    const char* authToken;
    int authTokenLen;

    const char *contCred;
    int contCredLen;

    XrdSecCredentials *credentials = 0;
    XrdSecParameters *authParams = 0;
    std::stringstream err;

    // Parse the python parameters
    if (!PyArg_ParseTuple(args, "z#z#si", &authToken, &authTokenLen, &contCred,
                    &contCredLen, &authLibName, &sock))
        return NULL;

    // Prepare some variables
    authEnv = new XrdOucEnv();
    authEnv->Put("sockname", "");
    XrdOucErrInfo ei("", authEnv);
    getSockName(sock);

    if (authToken != NULL)
    {
        authParams = new XrdSecParameters((char*) authToken, authTokenLen);
    }

    // Check if this is an authmore call, i.e. we have continuation credentials
    if (authProtocol && (contCred != NULL))
    {
        XrdSecParameters *secToken = new XrdSecParameters((char*) contCred,
                contCredLen);

        credentials = authProtocol->getCredentials(secToken, &ei);
        if (!credentials)
        {
            err << "Unable to get continuation credentials: " << ei.getErrText()
            << endl;
            return PyErr_Format(AuthenticationError, err.str().c_str());;
        }

        return Py_BuildValue("ss#", protocolName.c_str(), credentials->buffer,
                credentials->size);
    }

    // dlopen the library
    if (!(libHandle = openLibrary(authLibName)))
    {
        return NULL;
    }

    // Get the authentication function handle
    XrdSecGetProt_t authHandler = (XrdSecGetProt_t) dlsym(libHandle,
            "XrdSecGetProtocol");
    if (!authHandler)
    {
        err << "Unable to get the XrdSecGetProtocol symbol from library "
        << authLibName << ": " << ::dlerror() << endl;
        ::dlclose(libHandle);
        libHandle = 0;
        return PyErr_Format(AuthenticationError, err.str().c_str());;
    }

    // Loop over the possible protocols to find one that gives us valid
    // credentials
    while (1)
    {
        // Get the protocol
        authProtocol = (*authHandler)(host, *((sockaddr*) sockadd), *authParams,
                0);
        if (!authProtocol)
        {
            err << "No protocols left to try" << endl;
            return PyErr_Format(AuthenticationError, err.str().c_str());;
        }

        protocolName = authProtocol->Entity.prot;
        cout << "Trying to get credentials for protocol: "
        << protocolName.c_str() << endl;

        // Get the credentials from the current protocol
        credentials = authProtocol->getCredentials(0, &ei);
        if (!credentials)
        {
            cout << "Cannot get credentials for protocol "
            << protocolName.c_str() << ": " << ei.getErrText() << endl;
            authProtocol->Delete();
            continue;
        }
        else
        break;
    }

    cout << "Successfully got credentials for protocol: "
    << protocolName.c_str() << endl;

    return Py_BuildValue("ss#", protocolName.c_str(), credentials->buffer,
            credentials->size);
}
}

static PyMethodDef AuthBindMethods[] =
{
    { "init", init, METH_VARARGS, "Initialize authentication bindings"},
    { "get_credentials", get_credentials, METH_VARARGS,
      "Get opaque credentials object or continuation credentials." },
    { "authenticate", authenticate, METH_VARARGS,
      "Authenticate credentials provided by a client." },
    { "get_parms", get_parms, METH_VARARGS,
      "Get a security token for a login response." },
    { NULL, NULL, 0, NULL } /* Sentinel */
};

PyMODINIT_FUNC initXrdAuthBind(void)
{
    PyObject* XrdAuthBind = Py_InitModule("XrdAuthBind", AuthBindMethods);

    // Set some environment vars
    setenv("XRDINSTANCE", "imposter", 1);
    setenv("XrdSecDEBUG", "1", 1);

    AuthenticationError = PyErr_NewException("XrdAuthBind.AuthenticationError",
            NULL, NULL);
    PyModule_AddObject(XrdAuthBind, "AuthenticationError", AuthenticationError);
}

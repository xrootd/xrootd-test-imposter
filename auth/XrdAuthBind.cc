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
 * Return a filled sockaddr_in struct from the socket descriptor given using
 * getsockname().
 *
 * @param sock the socket file descriptor to use.
 */
struct sockaddr_in *getSockName(int sock)
{
    struct sockaddr_in *sockadd;
    socklen_t socklen = sizeof(struct sockaddr_in);
    sockadd = (sockaddr_in*) malloc(sizeof(struct sockaddr_in));
    getsockname(sock, (sockaddr*) sockadd, &socklen);
    return sockadd;
}

/**
 * Return a filled sockaddr_in struct from the socket descriptor given using
 * getpeername().
 *
 * @param sock the socket file descriptor to use.
 */
struct sockaddr_in *getPeerName(int sock)
{
    struct sockaddr_in *sockadd;
    socklen_t socklen = sizeof(struct sockaddr_in);
    sockadd = (sockaddr_in*) malloc(sizeof(struct sockaddr_in));
    getpeername(sock, (sockaddr*) sockadd, &socklen);
    return sockadd;
}

/**
 * Build a security token to send as a response to a kXR_login request,
 * if the sec.protocol configuration directive exists in our config file.
 *
 * @throw AuthenticationError on error.
 * @return the security token that was built.
 */
const char *getSecurityToken()
{
    XrdSecService *securityService;
    std::stringstream err;

    // Get the authentication function handle
    XrdSecGetServ_t authHandler = (XrdSecGetServ_t) dlsym(pAuthLibHandle,
            "XrdSecgetService");
    if (!authHandler)
    {
        err << "Unable to get symbol XrdSecgetService from library "
            << pAuthLibName << ": " << ::dlerror() << endl;
        ::dlclose(pAuthLibHandle);
        pAuthLibHandle = 0;
        PyErr_SetString(AuthenticationError, err.str().c_str());
        return NULL;
    }

    // Get the security service object
    securityService = (*authHandler)(&pLogger, pTempConfigFile);
    cout << "[XrdAuthBind] Building security token" << endl;
    if (!securityService)
    {
        err << "Unable to create security service" << endl;
        ::dlclose(pAuthLibHandle);
        pAuthLibHandle = 0;
        PyErr_SetString(AuthenticationError, err.str().c_str());
        return NULL;
    }

    // Get the security token
    int tokenSize;
    const char *token = securityService->getParms(tokenSize, host);
    if (token == NULL)
    {
        err << "No security token for " << host << endl;
        PyErr_SetString(AuthenticationError, err.str().c_str());
        return NULL;
    }

    cout << "[XrdAuthBind] Built security token: " << token << endl;
    return token;
}

extern "C" {

/**
 * Initialize the extension. This method will set environment variables,
 * prepare the temporary configuration file and build the server security
 * token (if called by a server). This method need only be called once, but
 * it is safe to call multiple times.
 *
 * @param args the Python tuple containing the configuration file string and
 *             the name of the authentication shared library.
 * @throw AuthenticationError on error.
 */
static PyObject* init(PyObject *self, PyObject *args)
{
    if (pInitialized == true)
    {
        return Py_BuildValue("");
    }

    cout << "[XrdAuthBind] Initializing extension" << endl;

    const char *config;
    // Parse the python parameters
    if (!PyArg_ParseTuple(args, "ss", &config, &pAuthLibName))
        return NULL;

    // Write the temporary config file
    pTempConfigFile = writeTempFile(config);

    // dlopen the library
    if (!(pAuthLibHandle = openLibrary(pAuthLibName)))
    {
        return NULL;
    }

    // Build the security token
    if (!(pSecurityToken = getSecurityToken()))
    {
        return NULL;
    }

    cout << "[XrdAuthBind] Extension initialized" << endl;
    pInitialized = true;
    // Return nothing
    return Py_BuildValue("");
}

/**
 * Return this server's security parameters (security token).
 */
static PyObject* get_parms(PyObject *self, PyObject *args)
{
    return Py_BuildValue("s", pSecurityToken);
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
 *             continuation credential length and the client socket file
 *             descriptor.
 * @throw AuthenticationError on error or credentials cannot be acquired for
 *        any protocols.
 * @return name of the successful protocol, the opaque credentials string and
 *         length of the credentials on success.
 */
static PyObject* get_credentials(PyObject *self, PyObject *args)
{
    pMutex.Lock();

    const char* authToken;
    int authTokenLen;
    const char *contCred;
    int contCredLen;
    int sock;
    struct sockaddr_in *sockAdd;

    XrdSecProtocol *authProtocol;
    XrdSecCredentials *credentials = 0;
    XrdSecParameters *authParams = 0;
    XrdOucErrInfo ei("imposter", pAuthEnv);
    string protocolName;

    // Parse the python parameters
    if (!PyArg_ParseTuple(args, "z#z#i", &authToken, &authTokenLen, &contCred,
                    &contCredLen, &sock))
        return NULL;

    // Fill our sockaddr_in struct
    sockAdd = getSockName(sock);

    // Check if this is an authmore call, i.e. we have continuation credentials
    if (contCred != NULL)
    {
        // We got continuation credentials, but out auth protocol hasn't been
        // instantiated
        if (pAuthProtocols.find(sock) == pAuthProtocols.end())
        {
            pMutex.UnLock();
            return PyErr_Format(AuthenticationError, "Continuation credentials"
                    " requested before initial credentials");
        }
        // Get and return the continuation credentials
        else
        {
            authProtocol = pAuthProtocols.at(sock);
            XrdSecParameters *secToken = new XrdSecParameters((char*) contCred,
                            contCredLen);

            credentials = authProtocol->getCredentials(secToken, &ei);
            if (!credentials)
            {
                pMutex.UnLock();
                return PyErr_Format(AuthenticationError, "Unable to get "
                        "continuation credentials: %s", ei.getErrText());
            }

            protocolName = authProtocol->Entity.prot;
            pMutex.UnLock();
            return Py_BuildValue("ss#", protocolName.c_str(),
                    credentials->buffer, credentials->size);
        }
    }

    // This must be the initial call, continue
    // Get the authentication function handle
    XrdSecGetProt_t authHandler = (XrdSecGetProt_t) dlsym(pAuthLibHandle,
            "XrdSecGetProtocol");
    if (!authHandler)
    {
        ::dlclose(pAuthLibHandle);
        pAuthLibHandle = 0;
        pMutex.UnLock();
        return PyErr_Format(AuthenticationError, "Unable to get symbol"
                " XrdSecGetProtocol from library %s: %s", pAuthLibName,
                ::dlerror());
    }

    // Create our auth parameters object if we have a token
    if (authToken != NULL)
    {
        authParams = new XrdSecParameters((char*) authToken, authTokenLen);
    }

    // Loop over the possible protocols to find one that gives us valid
    // credentials
    while (1)
    {
        // Get the protocol
        authProtocol = (*authHandler)(host, *((sockaddr*) sockAdd), *authParams,
                0);
        if (!authProtocol)
        {
            pMutex.UnLock();
            return PyErr_Format(AuthenticationError, "Couldn't get credentials"
                   " for any supported protocols");
        }

        protocolName = authProtocol->Entity.prot;
        cout << "[XrdAuthBind] Trying to get credentials for protocol: "
             << protocolName.c_str() << endl;

        // Get the credentials from the current protocol
        credentials = authProtocol->getCredentials(0, &ei);
        if (!credentials)
        {
            cout << "[XrdAuthBind] Cannot get credentials for protocol "
                 << protocolName.c_str() << ": " << ei.getErrText() << endl;
            authProtocol->Delete();
            continue;
        }
        else
            break;
    }

    cout << "[XrdAuthBind] Successfully got credentials for protocol: "
         << protocolName.c_str() << endl;

    // Place the authProtocol in the map for re-use
    pAuthProtocols.insert(make_pair(sock, authProtocol));
    pMutex.UnLock();

    return Py_BuildValue("ss#", protocolName.c_str(), credentials->buffer,
            credentials->size);
}

/**
 * Authenticate a client's credentials which were supplied via a kXR_auth
 * request.
 *
 * @param args the Python tuple containing the credential string, the length
 *             of the credentials and the client socket file descriptor.
 * @throw AuthenticationError on error or invalid credentials.
 * @return NULL on success and no further authentication needed, continuation
 *         parameters and their length on success and more authentication
 *         needed.
 */
static PyObject* authenticate(PyObject *self, PyObject *args)
{
    pMutex.Lock();

    const char *creds;
    int credsLen;
    struct sockaddr_in *sockAdd;
    int sock;

    XrdSecProtocol *authProtocol;
    XrdSecService *securityService;
    XrdSecCredentials *credentials = 0;
    XrdSecParameters *contParams;
    XrdOucErrInfo ei("imposter", pAuthEnv);

    // Parse the python parameters
    if (!PyArg_ParseTuple(args, "z#i", &creds, &credsLen, &sock))
        return NULL;

    credentials = new XrdSecCredentials((char*) creds, credsLen);

    // Fill our sockaddr_in struct
    sockAdd = getPeerName(sock);

    // Get the authentication function handle
    XrdSecGetServ_t authHandler = (XrdSecGetServ_t) dlsym(pAuthLibHandle,
            "XrdSecgetService");
    if (!authHandler)
    {
        ::dlclose(pAuthLibHandle);
        pAuthLibHandle = 0;
        pMutex.UnLock();
        return PyErr_Format(AuthenticationError, "Unable to get symbol "
                "XrdSecgetService from library %s: %s", pAuthLibName,
                ::dlerror());
    }

    // Get the security service object
    securityService = (*authHandler)(&pLogger, pTempConfigFile);
    if (!securityService)
    {
        pMutex.UnLock();
        return PyErr_Format(AuthenticationError, "Unable to create security "
                "service");
    }

    // Get the protocol (unless it already exists)
    if (pAuthProtocols.find(sock) == pAuthProtocols.end())
    {
        authProtocol = securityService->getProtocol((const char *) host,
                (const sockaddr &) *sockAdd,
                (const XrdSecCredentials *) credentials, &ei);
        if (!authProtocol)
        {
            pMutex.UnLock();
            return PyErr_Format(AuthenticationError, "getProtocol error: %s",
                    ei.getErrText());
        }
    }
    else
    {
        authProtocol = pAuthProtocols.at(sock);
    }

    // Now authenticate the credentials
    int authResult = authProtocol->Authenticate(credentials, &contParams, &ei);
    if (authResult < 0)
    {
        // Error
        authProtocol->Delete();
        pMutex.UnLock();
        return PyErr_Format(AuthenticationError, "Authentication error: %s",
                ei.getErrText());
    }
    else if (authResult > 0)
    {
        // Protocol gave us continuation parameters
        pAuthProtocols.insert(make_pair(sock, authProtocol));
        pMutex.UnLock();
        return Py_BuildValue("s#", contParams->buffer, contParams->size);
    }
    else
    {
        // Authentication completed
        pMutex.UnLock();
        return Py_BuildValue("");
    }
}
}

/**
 * Python method table. Lists methods which will be available to the module
 * inside Python.
 */
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

/**
 * Python module initialization function (mandatory). Will be called when the
 * XrdAuthBind method is imported inside Python.
 */
PyMODINIT_FUNC initXrdAuthBind(void)
{
    PyObject* XrdAuthBind = Py_InitModule("XrdAuthBind", AuthBindMethods);

    // Create custom exception
    AuthenticationError = PyErr_NewException("XrdAuthBind.AuthenticationError",
            NULL, NULL);
    Py_INCREF(AuthenticationError);

    // Add custom exception to module
    PyModule_AddObject(XrdAuthBind, "AuthenticationError", AuthenticationError);

    // Set some environment vars
    setenv("XRDINSTANCE", "imposter", 1);
    //setenv("XrdSecDEBUG", "1", 1);

    // Prepare some variables
    pAuthEnv = new XrdOucEnv();
    pAuthEnv->Put("sockname", "imposter");
}

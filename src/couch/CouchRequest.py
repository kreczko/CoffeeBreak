#!/usr/bin/env python
"""
_Requests_
A class representing HTTP requests to CouchDB
"""
import urllib
import os
import sys
import types
import base64
import httplib2
import socket
import logging
from urlparse import urlparse
from httplib import HTTPException

def check_server_url(srvurl):
    good_name = srvurl.startswith('http://') or srvurl.startswith('https://')
    if not good_name:
        msg = "You must include http(s):// in your servers address, %s doesn't" % srvurl
        raise ValueError(msg)

_module = "json"

try:
    import cjson
    _module = "cjson"
except:
    pass
import json # python 2.6 and later

def loads(idict, **kwargs):
    """
    Based on default _module invoke appropriate JSON decoding API call
    """
    if  _module == 'json':
        return json.loads(idict, **kwargs)
    elif _module == 'cjson':
        return cjson.decode(idict)

def load(source):
    """
    Use json.load for back-ward compatibility, since cjson doesn't
    provide this method. The load method works on file-descriptor
    objects.
    """
    if  _module == 'json':
        return json.load(source)
    elif _module == 'cjson':
        data = source.read()
        return cjson.decode(data)

def dumps(idict, **kwargs):
    """
    Based on default _module invoke appropriate JSON encoding API call
    """
    if  _module == 'json':
        return json.dumps(idict, **kwargs)
    elif _module == 'cjson':
        return cjson.encode(idict)

def dump(doc, source):
    """
    Use json.dump for back-ward compatibility, since cjson doesn't
    provide this method. The dump method works on file-descriptor
    objects.
    """
    if  _module == 'json':
        return json.dump(doc, source)
    elif _module == 'cjson':
        stj = cjson.encode(doc)
        return source.write(stj)

class JSONEncoder(object):
    def __init__(self):
        self.encoder = json.JSONEncoder()

    def encode(self, idict):
        if  _module == 'cjson':
            return cjson.encode(idict)
        return self.encoder.encode(idict)

    def iterencode(self, idict):
        return self.encoder.iterencode(idict)

class JSONDecoder(object):
    def __init__(self):
        self.decoder = json.JSONDecoder()

    def decode(self, idict):
        if  _module == 'cjson':
            return cjson.decode(idict)
        return self.decoder.decode(idict)

    def raw_decode(self, idict):
        return self.decoder.raw_decode(idict)

class JSONThunker:
    """
    _JSONThunker_
    Converts an arbitrary object to <-> from a jsonable object.

    Will, for the most part "do the right thing" about various instance objects
    by storing their class information along with their data in a dict. Handles
    a recursion limit to prevent infinite recursion.

    self.passThroughTypes - stores a list of types that should be passed
      through unchanged to the JSON parser

    self.blackListedModules - a list of modules that should not be stored in
      the JSON.

    """
    def __init__(self):
        self.passThroughTypes = (types.NoneType,
                                 types.BooleanType,
                                 types.IntType,
                                 types.FloatType,
                                 types.LongType,
                                 types.ComplexType,
                                 types.StringTypes,
                                 types.StringType,
                                 types.UnicodeType
                                 )
        # objects that inherit from dict should be treated as a dict
        #   they don't store their data in __dict__. There was enough
        #   of those classes that it warrented making a special case
        self.dictSortOfObjects = ( ('WMCore.Datastructs.Job', 'Job'),
                                   ('WMCore.WMBS.Job', 'Job'),
                                   ('WMCore.Database.CMSCouch', 'Document' ))
        # ditto above, but for lists
        self.listSortOfObjects = ( ('WMCore.DataStructs.JobPackage', 'JobPackage' ),
                                   ('WMCore.WMBS.JobPackage', 'JobPackage' ),)

        self.foundIDs = {}
        # modules we don't want JSONed
        self.blackListedModules = ('sqlalchemy.engine.threadlocal',
                                   'WMCore.Database.DBCore',
                                   'logging',
                                   'WMCore.DAOFactory',
                                   'WMCore.WMFactory',
                                   'WMFactory',
                                   'WMCore.Configuration',
                                   'WMCore.Database.Transaction',
                                   'threading',
                                   'datetime')

    def checkRecursion(self, data):
        """
        handles checking for infinite recursion
        """
        if (id(data) in self.foundIDs):
            if (self.foundIDs[id(data)] > 5):
                self.unrecurse(data)
                return "**RECURSION**"
            else:
                self.foundIDs[id(data)] += 1
                return data
        else:
            self.foundIDs[id(data)] = 1
            return data

    def unrecurse(self, data):
        """
        backs off the recursion counter if we're returning from _thunk
        """
        self.foundIDs[id(data)] = self.foundIDs[id(data)] -1

    def checkBlackListed(self, data):
        """
        checks to see if a given object is from a blacklisted module
        """
        try:
            # special case
            if ((data.__class__.__module__ == 'WMCore.Database.CMSCouch') and
                (data.__class__.__name__ == 'Document')):
                data.__class__ = type({})
                return data
            if (data.__class__.__module__ in self.blackListedModules):
                return "Blacklisted JSON object: module %s, name %s, str() %s" %\
                    (data.__class__.__module__,data.__class__.__name__ , str(data))
            else:
                return data
        except:
            return data


    def thunk(self, toThunk):
        """
        Thunk - turns an arbitrary object into a JSONable object
        """
        self.foundIDs = {}
        data = self._thunk(toThunk)
        return data

    def unthunk(self, data):
        """
        unthunk - turns a previously 'thunked' object back into a python object
        """
        return self._unthunk(data)

    def handleSetThunk(self, toThunk):
        toThunk = self.checkRecursion( toThunk )
        tempDict = {'thunker_encoded_json':True, 'type': 'set'}
        tempDict['set'] = self._thunk(list(toThunk))
        self.unrecurse(toThunk)
        return tempDict

    def handleListThunk(self, toThunk):
        toThunk = self.checkRecursion( toThunk )
        for k,v in enumerate(toThunk):
                toThunk[k] = self._thunk(v)
        self.unrecurse(toThunk)
        return toThunk

    def handleDictThunk(self, toThunk):
        toThunk = self.checkRecursion( toThunk )
        special = False
        tmpdict = {}
        for k,v in toThunk.iteritems():
            if type(k) == type(int):
                special = True
                tmpdict['_i:%s' % k] = self._thunk(v)
            elif type(k) == type(float):
                special = True
                tmpdict['_f:%s' % k] = self._thunk(v)
            else:
                tmpdict[k] = self._thunk(v)
        if special:
            toThunk['thunker_encoded_json'] = self._thunk(True)
            toThunk['type'] = self._thunk('dict')
            toThunk['dict'] = tmpdict
        else:
            toThunk.update(tmpdict)
        self.unrecurse(toThunk)
        return toThunk

    def handleObjectThunk(self, toThunk):
        toThunk = self.checkRecursion( toThunk )
        toThunk = self.checkBlackListed(toThunk)

        if (type(toThunk) == type("")):
            # things that got blacklisted
            return toThunk
        if (hasattr(toThunk, '__to_json__')):
            #Use classes own json thunker
            toThunk2 = toThunk.__to_json__(self)
            self.unrecurse(toThunk)
            return toThunk2
        elif ( isinstance(toThunk, dict) ):
            toThunk2 = self.handleDictObjectThunk( toThunk )
            self.unrecurse(toThunk)
            return toThunk2
        elif ( isinstance(toThunk, list) ):
            #a mother thunking list
            toThunk2 = self.handleListObjectThunk( toThunk )
            self.unrecurse(toThunk)
            return toThunk2
        else:
            try:
                thunktype = '%s.%s' % (toThunk.__class__.__module__,
                                       toThunk.__class__.__name__)
                tempDict = {'thunker_encoded_json':True, 'type': thunktype}
                tempDict[thunktype] = self._thunk(toThunk.__dict__)
                self.unrecurse(toThunk)
                return tempDict
            except Exception, e:
                tempDict = {'json_thunk_exception_' : "%s" % e }
                self.unrecurse(toThunk)
                return tempDict

    def handleDictObjectThunk(self, data):
        thunktype = '%s.%s' % (data.__class__.__module__,
                               data.__class__.__name__)
        tempDict = {'thunker_encoded_json':True,
                    'is_dict': True,
                    'type': thunktype,
                    thunktype: {}}

        for k,v in data.__dict__.iteritems():
            tempDict[k] = self._thunk(v)
        for k,v in data.iteritems():
            tempDict[thunktype][k] = self._thunk(v)

        return tempDict

    def handleDictObjectUnThunk(self, value, data):
        data.pop('thunker_encoded_json', False)
        data.pop('is_dict', False)
        thunktype = data.pop('type', False)

        for k,v in data.iteritems():
            if (k == thunktype):
                for k2,v2 in data[thunktype].iteritems():
                    value[k2] = self._unthunk(v2)
            else:
                value.__dict__[k] = self._unthunk(v)
        return value

    def handleListObjectThunk(self, data):
        thunktype = '%s.%s' % (data.__class__.__module__,
                               data.__class__.__name__)
        tempDict = {'thunker_encoded_json':True,
                    'is_list': True,
                    'type': thunktype,
                    thunktype: []}
        for k,v in enumerate(data):
            tempDict['thunktype'].append(self._thunk(v))
        for k,v in data.__dict__.iteritems():
            tempDict[k] = self._thunk(v)
        return tempDict

    def handleListObjectUnThunk(self, value, data):
        data.pop('thunker_encoded_json', False)
        data.pop('is_list', False)
        thunktype = data.pop('type')
        tmpdict = {}
        for k,v in data[thunktype].iteritems():
            setattr(value, k, self._unthunk(v))

        for k,v in data.iteritems():
            if (k == thunktype):
                continue
            value.__dict__ = self._unthunk(v)
        return value

    def _thunk(self, toThunk):
        """
        helper function for thunk, does the actual work
        """

        if (type(toThunk) in self.passThroughTypes):
            return toThunk
        elif (type(toThunk) == type([])):
            return self.handleListThunk(toThunk)

        elif (type(toThunk) == type({})):
            return self.handleDictThunk(toThunk)

        elif ((type(toThunk) == type(set()))):
            return self.handleSetThunk(toThunk)

        elif (type(toThunk) == types.FunctionType):
            self.unrecurse(toThunk)
            return "function reference"
        elif (isinstance(toThunk, object)):
            return self.handleObjectThunk(toThunk)
        else:
            self.unrecurse(toThunk)
            raise RuntimeError, type(toThunk)

    def _unthunk(self, jsondata):
        """
        _unthunk - does the actual work for unthunk
        """
        if (type(jsondata) == types.UnicodeType):
            return str(jsondata)
        if (type(jsondata) == type({})):
            if ('thunker_encoded_json' in jsondata):
                # we've got a live one...
                if jsondata['type'] == 'set':
                    newSet = set()
                    for i in self._unthunk(jsondata['set']):
                        newSet.add( self._unthunk( i ) )
                    return newSet
                if jsondata['type'] == 'dict':
                    # We have a "special" dict
                    data = {}
                    for k,v in jsondata['dict'].iteritems():
                        tmp = self._unthunk(v)
                        if k.startswith('_i:'):
                            data[int(k.lstrip('_i:'))] = tmp
                        elif k.startswith('_f:'):
                            data[float(k.lstrip('_f:'))] = tmp
                        else:
                            data[k] = tmp
                    return data
                else:
                    # spawn up an instance.. good luck
                    #   here be monsters
                    #   inspired from python's pickle code
                    ourClass = self.getThunkedClass(jsondata)

                    value = _EmptyClass()
                    if (hasattr(ourClass, '__from_json__')):
                        # Use classes own json loader
                        try:
                            value.__class__ = ourClass
                        except:
                            value = ourClass()
                        value = ourClass.__from_json__(value, jsondata, self)
                    elif ('thunker_encoded_json' in jsondata and
                                     'is_dict' in jsondata):
                        try:
                            value.__class__ = ourClass
                        except:
                            value = ourClass()
                        value = self.handleDictObjectUnThunk( value, jsondata )
                    elif ( 'thunker_encoded_json' in jsondata ):
                        #print "list obj unthunk"
                        try:
                            value.__class__ = ourClass
                        except:
                            value = ourClass()
                        value = self.handleListObjectUnThunk( value, jsondata )
                    else:
                        #print "did we get here"
                        try:
                            value.__class__ = getattr(ourClass, name).__class__
                            #print "changed the class to %s " % value.__class__
                        except Exception, ex:
                            #print "Except1 in requests %s " % ex
                            try:
                                #value = _EmptyClass()
                                value.__class__ = ourClass
                            except Exception, ex2:
                                #print "Except2 in requests %s " % ex2
                                #print type(ourClass)
                                try:
                                    value = ourClass();
                                except:
                                    #print 'megafail'
                                    pass

                        #print "name %s module %s" % (name, module)
                        value.__dict__ = data
                #print "our value is %s "% value
                return value
            else:
                #print 'last ditch attempt'
                data = {}
                for k,v in jsondata.iteritems():
                    data[k] = self._unthunk(v)
                return data

        else:
            return jsondata

    def getThunkedClass(self, jsondata):
        """
        Work out the class from it's thunked json representation
        """
        module = jsondata['type'].rsplit('.',1)[0]
        name = jsondata['type'].rsplit('.',1)[1]
        if (module == 'WMCore.Services.Requests') and (name == JSONThunker):
            raise RuntimeError, "Attempted to unthunk a JSONThunker.."

        __import__(module)
        mod = sys.modules[module]
        ourClass = getattr(mod, name)
        return ourClass


class Requests(dict):
    """
    Generic class for sending different types of HTTP Request to a given URL
    """
    default_timeout = 30

    def __init__(self, url = 'http://localhost', dict={}, timeout=None):
        """
        url should really be host - TODO fix that when have sufficient code
        coverage and change _getURLOpener if needed
        """

        self.additionalHeaders = {}

        if url.find("@") != -1:
            endpoint_components = urlparse(url)
            scheme = endpoint_components.scheme
            netloc = endpoint_components.netloc

            (auth, hostname) = netloc.split('@')
            self.additionalHeaders["Authorization"] = \
            	    "Basic " + base64.encodestring(auth).strip()
            url = '%s://%s' % (scheme, hostname)

        #set up defaults
        self['accept_type'] = "application/json"
        self['content_type'] = "application/json"
        self.setdefault("host", url)
        self.setdefault("req_cache_path", '.cache')
        if timeout > 0: # Don't set the timeout at all if it is zero - allows for workaround of httplib2/osx/reverse proxy issue
            self.setdefault("timeout", timeout)
        elif timeout is None:
            self.setdefault("timeout", Requests.default_timeout)
        self.setdefault("logger", logging)

        # then update with the incoming dict
        self.update(dict)
        check_server_url(self['host'])
        # and then get the URL opener
        self.setdefault("conn", self._getURLOpener())
        return

    def get(self, uri=None, data={}, incoming_headers={},
               encode = True, decode=True, contentType=None):
        """
        GET some data
        """
        return self.makeRequest(uri, data, 'GET', incoming_headers,
                                encode, decode, contentType)

    def post(self, uri=None, data={}, incoming_headers={},
               encode = True, decode=True, contentType=None):
        """
        POST some data
        """
        return self.makeRequest(uri, data, 'POST', incoming_headers,
                                encode, decode, contentType)

    def put(self, uri=None, data={}, incoming_headers={},
               encode = True, decode=True, contentType=None):
        """
        PUT some data
        """
        return self.makeRequest(uri, data, 'PUT', incoming_headers,
                                encode, decode, contentType)

    def delete(self, uri=None, data={}, incoming_headers={},
               encode = True, decode=True, contentType=None):
        """
        DELETE some data
        """
        return self.makeRequest(uri, data, 'DELETE', incoming_headers,
                                encode, decode, contentType)

    def move(self, uri=None, data=None):
        """
        MOVE some data
        """
        return self.makeRequest(uri, data, 'MOVE')

    def copy(self, uri=None, data=None):
        """
        COPY some data
        """
        return self.makeRequest(uri, data, 'COPY')

    def makeRequest(self, uri=None, data=None, type='GET', incoming_headers = {},
                     encode=True, decode=True, contentType=None, cache=False):
        """
        Make the request, handle any failed status, return just the data (for
        compatibility). By default do not cache the response.

        TODO: set caching in the calling methods.
        """
        try:
            if not cache:
                incoming_headers.update({'Cache-Control':'no-cache'})
            result, status, reason, cached = self.makeHTTPRequest(
                                        uri.encode('utf-8'), data, type, incoming_headers,
                                        encode, decode,contentType)
        except HTTPException, e:
            self.checkForCouchError(getattr(e, "status", None),
                                    getattr(e, "reason", None), data)

        return result

    def makeHTTPRequest(self, uri=None, data={}, verb='GET', incoming_headers={},
                     encoder=True, decoder=True, contentType=None):
        """
        Make a request to the remote database. for a give URI. The type of
        request will determine the action take by the server (be careful with
        DELETE!). Data should be a dictionary of {dataname: datavalue}.

        Returns a tuple of the data from the server, decoded using the
        appropriate method the response status and the response reason, to be
        used in error handling.

        You can override the method to encode/decode your data by passing in an
        encoding/decoding function to this method. Your encoded data must end up
        as a string.

        """
        #TODO: User agent should be:
        # $client/$client_version (CMS) $http_lib/$http_lib_version $os/$os_version ($arch)
        if contentType:
            headers = {"Content-type": contentType,
                   "User-agent": "WMCore.Services.Requests/v001",
                   "Accept": self['accept_type']}
        else:
            headers = {"Content-type": self['content_type'],
                   "User-agent": "WMCore.Services.Requests/v001",
                   "Accept": self['accept_type']}
        encoded_data = ''

        for key in self.additionalHeaders.keys():
            headers[key] = self.additionalHeaders[key]

        #And now overwrite any headers that have been passed into the call:
        headers.update(incoming_headers)

        # httpib2 requires absolute url
        uri = self['host'] + uri

        # If you're posting an attachment, the data might not be a dict
        #   please test against ConfigCache_t if you're unsure.
        #assert type(data) == type({}), \
        #        "makeRequest input data must be a dict (key/value pairs)"

        # There must be a better way to do this...
        def f(): pass

        if verb != 'GET' and data:
            if type(encoder) == type(self.get) or type(encoder) == type(f):
                encoded_data = encoder(data)
            elif encoder == False:
                # Don't encode the data more than we have to
                #  we don't want to URL encode the data blindly,
                #  that breaks POSTing attachments... ConfigCache_t
                #encoded_data = urllib.urlencode(data)
                #  -- Andrew Melo 25/7/09
                encoded_data = data
            else:
                # Either the encoder is set to True or it's junk, so use
                # self.encode
                encoded_data = self.encode(data)
            headers["Content-length"] = len(encoded_data)
        elif verb == 'GET' and data:
            #encode the data as a get string
            uri = "%s?%s" % (uri, urllib.urlencode(data, doseq=True))

        headers["Content-length"] = str(len(encoded_data))

        assert type(encoded_data) == type('string'), \
                    "Data in makeRequest is %s and not encoded to a string" % type(encoded_data)

        # httplib2 will allow sockets to close on remote end without retrying
        # try to send request - if this fails try again - should then succeed
        try:
            response, result = self['conn'].request(uri, method = verb,
                                    body = encoded_data, headers = headers)
            if response.status == 408: # timeout can indicate a socket error
                response, result = self['conn'].request(uri, method = verb,
                                    body = encoded_data, headers = headers)
        except (socket.error, AttributeError):
            # AttributeError implies initial connection error - need to close
            # & retry. httplib2 doesn't clear httplib state before next request
            # if this is threaded this may spoil things
            # only have one endpoint so don't need to determine which to shut
            [conn.close() for conn in self['conn'].connections.values()]
            # ... try again... if this fails propagate error to client
            try:
                response, result = self['conn'].request(uri, method = verb,
                                    body = encoded_data, headers = headers)
            except AttributeError:
                # socket/httplib really screwed up - nuclear option
                self['conn'].connections = {}
                raise socket.error, 'Error contacting: %s' % self['host']
        if response.status >= 400:
            e = HTTPException()
            setattr(e, 'req_data', encoded_data)
            setattr(e, 'req_headers', headers)
            setattr(e, 'url', uri)
            setattr(e, 'result', result)
            setattr(e, 'status', response.status)
            setattr(e, 'reason', response.reason)
            setattr(e, 'headers', response)
            raise e

        if type(decoder) == type(self.makeRequest) or type(decoder) == type(f):
            result = decoder(result)
        elif decoder != False:
            result = self.decode(result)
        #TODO: maybe just return result and response...
        return result, response.status, response.reason, response.fromcache

    def encode(self, data):
        """
        encode data as json
        """
        encoder = JSONEncoder()
        thunker = JSONThunker()
        thunked = thunker.thunk(data)
        return encoder.encode(thunked)


    def decode(self, data):
        """
        decode the data to python from json
        """
        if data:
            decoder = JSONDecoder()
            thunker = JSONThunker()
            data =  decoder.decode(data)
            unthunked = thunker.unthunk(data)
            return unthunked
        else:
            return {}

    def _getURLOpener(self):
        """
        method getting an HTTPConnection, it is used by the constructor such
        that a sub class can override it to have different type of connection
        i.e. - if it needs authentication, or some fancy handler
        """
        if 'timeout' in self:
            return httplib2.Http(self['req_cache_path'], self['timeout'])
        else:
            return httplib2.Http(self['req_cache_path'])


    def checkForCouchError(self, status, reason, data = None, result = None):
        """
        _checkForCouchError_

        Check the HTTP status and raise an appropriate exception.
        """
        if status == 400:
            raise CouchBadRequestError(reason, data, result)
        elif status == 401:
            raise CouchUnauthorisedError(reason, data, result)
        elif status == 403:
            raise CouchForbidden(reason, data, result)
        elif status == 404:
            raise CouchNotFoundError(reason, data, result)
        elif status == 405:
            raise CouchNotAllowedError(reason, data, result)
        elif status == 409:
            raise CouchConflictError(reason, data, result)
        elif status == 412:
            raise CouchPreconditionFailedError(reason, data, result)
        elif status == 500:
            raise CouchInternalServerError(reason, data, result)
        else:
            # We have a new error status, log it
            raise CouchError(reason, data, result, status)

        return

        # define some standard couch error classes
# from:
#  http://wiki.apache.org/couchdb/HTTP_status_list

class CouchError(Exception):
    "An error thrown by CouchDB"
    def __init__(self, reason, data, result, status = None):
        Exception.__init__(self)
        self.reason = reason
        self.data = data
        self.result = result
        self.type = "CouchError"
        self.status = status

    def __str__(self):
        "Stringify the error"
        if self.status != None:
            errorMsg = "NEW ERROR STATUS! UPDATE CMSCOUCH.PY!: %s\n" % self.status
        else:
            errorMsg = ""
        return errorMsg + "%s - reason: %s, data: %s result: %s" % (self.type,
                                             self.reason,
                                             repr(self.data),
                                             self.result)

class CouchBadRequestError(CouchError):
    def __init__(self, reason, data, result):
        CouchError.__init__(self, reason, data, result)
        self.type = "CouchBadRequestError"

class CouchUnauthorisedError(CouchError):
    def __init__(self, reason, data, result):
        CouchError.__init__(self, reason, data, result)
        self.type = "CouchUnauthorisedError"

class CouchNotFoundError(CouchError):
    def __init__(self, reason, data, result):
        CouchError.__init__(self, reason, data, result)
        self.type = "CouchNotFoundError"

class CouchNotAllowedError(CouchError):
    def __init__(self, reason, data, result):
        CouchError.__init__(self, reason, data, result)
        self.type = "CouchNotAllowedError"

class CouchConflictError(CouchError):
    def __init__(self, reason, data, result):
        CouchError.__init__(self, reason, data, result)
        self.type = "CouchConflictError"

class CouchPreconditionFailedError(CouchError):
    def __init__(self, reason, data, result):
        CouchError.__init__(self, reason, data, result)
        self.type = "CouchPreconditionFailedError"

class CouchInternalServerError(CouchError):
    def __init__(self, reason, data, result):
        CouchError.__init__(self, reason, data, result)
        self.type = "CouchInternalServerError"

class CouchForbidden(CouchError):
    def __init__(self, reason, data, result):
        CouchError.__init__(self, reason, data, result)
        self.type = "CouchForbidden"

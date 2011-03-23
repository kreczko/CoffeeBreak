#!/usr/bin/env python
"""
_Couch_

A simple API to CouchDB that sends HTTP requests to the REST interface.

Warning: There is a known issue when posting large (~800KB) JSON documents
from OSX through a reverse proxy. If a timeout is set then the client will
stop sending data and the request will not complete. This issue can be
worked-around by creating a CouchServer with timeout=0.

http://wiki.apache.org/couchdb/API_Cheatsheet
"""

import time
import urllib
import re
import hashlib
import base64
from httplib import HTTPException
from CouchRequest import Requests, check_server_url

def check_name(dbname):
    match = re.match("^[a-z0-9_$()+-/]+$", urllib.unquote_plus(dbname))
    if not match:
        msg = '%s is not a valid database name'
        raise ValueError(msg % urllib.unquote_plus(dbname))

class CouchType(object):
    """ Enumeration for types of Couch instances """
    COUCHDB = 0
    BIGCOUCH = 1

class Document(dict):
    """
    Document class is the instantiation of one document in the CouchDB
    """
    def __init__(self, id=None, dict = {}):
        """
        Initialise our Document object - a dictionary which has an id field
        """
        dict.__init__(self)
        self.update(dict)
        if id:
            self.setdefault("_id", id)

    def delete(self):
        """
        Mark the document as deleted
        """
        self['_deleted'] = True

    def __to_json__(self, thunker):
        """
        __to_json__

        This is here to prevent the serializer from attempting to serialize
        this object and adding a bunch of keys that couch won't understand.
        """
        jsonDict = {}
        for key in self.keys():
            jsonDict[key] = self[key]

        return jsonDict

class Database(Requests):
    """
    Object representing a connection to a CouchDB Database instance.
    TODO: implement COPY and MOVE calls.
    TODO: remove leading whitespace when committing a view
    """
    def __init__(self, dbname = 'database',
                  url = 'http://localhost:5984', size = 1000, couch_type = CouchType.COUCHDB, timeout = None):
        """
        A set of queries against a CouchDB database
        """
        check_name(dbname)

        self.name = urllib.quote_plus(dbname)

        Requests.__init__(self, url, timeout=timeout)
        self._reset_queue()

        self._queue_size = size
        self.threads = []
        self.last_seq = 0
        self.couch_type = couch_type

    def _reset_queue(self):
        """
        Set the queue to an empty list, e.g. after a commit
        """
        self._queue = []

    def timestamp(self, data, label=''):
        """
        Time stamp each doc in a list
        """
        if label == True:
            label = 'timestamp'

        if type(data) == type({}):
            data[label] = int(time.time())
        else:
            for doc in data:
                if label not in doc.keys():
                    doc[label] = int(time.time())
        return data

    def queue(self, doc, timestamp = False, viewlist=[]):
        """
        Queue up a doc for bulk insert. If timestamp = True add a timestamp
        field if one doesn't exist. Use this over commit(timestamp=True) if you
        want to timestamp when a document was added to the queue instead of when
        it was committed
        """
        if timestamp:
            self.timestamp(doc, timestamp)
        #TODO: Thread this off so that it's non blocking...
        if self.queue_size() >= self._queue_size:
            print '%s: queue larger than %s records, committing' % (self.name, self._queue_size)
            self.commit(viewlist=viewlist)
        self._queue.append(doc)

    def queue_size(self):
        """
        Return the current size of the queue
        """
        return len(self._queue)

    def queueDelete(self, doc, viewlist=[]):
        """
        Queue up a document for deletion
        """
        assert isinstance(doc, type({})), "document not a dictionary"
        doc['_deleted'] = True
        self.queue(doc)

    def commitOne(self, doc, returndocs=False, timestamp = False, viewlist=[]):
        """
        Helper function for when you know you only want to insert one doc
        additionally keeps from having to rewrite ConfigCache to handle the
        new commit function's semantics
        """
        uri  = '/%s/_bulk_docs/' % self.name
        if timestamp:
            self.timestamp(doc, timestamp)

        data = {'docs': [doc]}
        retval = self.post(uri , data)
        for v in viewlist:
            design, view = v.split('/')
            self.loadView(design, view, {'limit': 0})
        return retval

    def commit(self, doc=None, returndocs = False, timestamp = False,
               viewlist=[]):
        """
        Add doc and/or the contents of self._queue to the database. If
        returndocs is true, return document objects representing what has been
        committed. If timestamp is true timestamp all documents with a unix style
        timestamp - this will be the timestamp of when the commit was called, it
        will not override an existing timestamp field.  If timestamp is a string
        that string will be used as the label for the timestamp.

        TODO: restore support for returndocs and viewlist

        Returns a list of good documents
            throws an exception otherwise
        """
        if (doc):
            self.queue(doc, timestamp, viewlist)

        if timestamp:
            self.timestamp(self._queue, timestamp)
        # commit in thread to avoid blocking others
        uri  = '/%s/_bulk_docs/' % self.name

        if self.queue_size():
            data = {'docs': list(self._queue)}
            retval = self.post(uri , data)
            self._reset_queue()
            for v in viewlist:
                design, view = v.split('/')
                self.loadView(design, view, {'limit': 0})
            return retval
        return []

    def document(self, id, rev = None):
        """
        Load a document identified by id. You can specify a rev to see an older revision
        of the document. This **should only** be used when resolving conflicts, relying
        on CouchDB revisions for document history is not safe, as any compaction will
        remove the older revisions.
        """
        uri = '/%s/%s' % (self.name, urllib.quote_plus(id))
        if rev:
            uri += '?' + urllib.urlencode({'rev' : rev})
        return Document(id = id, dict=self.get(uri))

    def documentExists(self, id, rev = None):
        """
        Check if a document exists by ID. If specified check that the revision rev exists.
        """
        uri = "/%s/%s" % (self.name, urllib.quote_plus(id))
        if rev:
            uri += '?' + urllib.urlencode({'rev' : rev})
        docExists = False
        try:
            self.makeRequest(uri, {}, 'HEAD')
            return True
        except:
            return False

    def delete_doc(self, id, rev = None):
        """
        Immediately delete a document identified by id. Delete with a revision
        specified to resolve conflicts.
        """
        doc = self.document(id, rev)
        doc.delete()
        self.commitOne(doc)

    def compact(self, views=[], blocking=False, blocking_poll=5, callback=False):
       """
       Compact the database: http://wiki.apache.org/couchdb/Compaction

       If given, views should be a list of design document name (minus the
       _design/ - e.g. myviews not _design/myviews). For each view in the list
       view compaction will be triggered. Also, if the views list is provided
       _view_cleanup is called to remove old view output.

       If True blocking will cause this call to wait until the compaction is
       completed, polling for status with frequency blocking_poll and calling
       the function specified by callback on each iteration.

       The callback function can be used for logging and could also be used to
       timeout the compaction based on status (e.g. don't time out if compaction
       is less than X% complete. The callback function takes the Database (self)
       as an argument. If the callback function raises an exception the block is
       removed and the compact call returns.
       """
       if self.couch_type == CouchType.BIGCOUCH:
           raise NotImplementedError('User-triggered compaction not supported by BigCouch')
       response = self.post('/%s/_compact' % self.name)
       if len(views) > 0:
         for view in views:
           response[view] = self.post('/%s/_compact/%s' % (self.name, view))
           response['view_cleanup' ] = self.post('/%s/_view_cleanup' % (self.name))

       if blocking:
         while self.info()['compact_running']:
           if callback:
             try:
               callback(self)
             except Exception, e:
               return response
           time.sleep(blocking_poll)
       return response

    def changes(self, since=-1):
        """
        Get the changes since sequence number. Store the last sequence value to
        self.last_seq. If the since is negative use self.last_seq.
        """
        if since < 0:
            since = self.last_seq
        data = self.get('/%s/_changes/?since=%s' % (self.name, since))
        self.last_seq = data['last_seq']
        return data

    def loadView(self, design, view, options = {}, keys = []):
        """
        Load a view by getting, for example:
        http://localhost:5984/tester/_view/viewtest/age_name?count=10&group=true

        The following URL query arguments are allowed:

        GET
                key=keyvalue
                startkey=keyvalue
                startkey_docid=docid
                endkey=keyvalue
                endkey_docid=docid
                limit=max rows to return
                stale=ok
                descending=true
                skip=number of rows to skip
                group=true Version 0.8.0 and forward
                group_level=int
                reduce=false Trunk only (0.9)
                include_docs=true Trunk only (0.9)
        POST
                {"keys": ["key1", "key2", ...]} Trunk only (0.9)

        more info: http://wiki.apache.org/couchdb/HTTP_view_API
        """
        encodedOptions = {}
        for k,v in options.iteritems():
            encodedOptions[k] = self.encode(v)

        if len(keys):
            if (encodedOptions):
                data = urllib.urlencode(encodedOptions)
                retval = self.post('/%s/_design/%s/_view/%s?%s' % \
                            (self.name, design, view, data), {'keys':keys})
            else:
                retval = self.post('/%s/_design/%s/_view/%s' % \
                            (self.name, design, view), {'keys':keys})
        else:
            retval = self.get('/%s/_design/%s/_view/%s' % \
                            (self.name, design, view), encodedOptions)

        if ('error' in retval):
            raise RuntimeError ,\
                    "Error in CouchDB: viewError '%s' reason '%s'" %\
                        (retval['error'], retval['reason'])
        else:
            return retval

    def loadShow(self, design, show, document_id, options = {}):
        """
        Load a document via a show function. This returns data that hasn't been
        decoded, since a show can return data in any format. It is expected that
        the caller of this function knows what data is being returned and how to
        deal with it appropriately.
        """
        encodedOptions = {}
        for k,v in options.iteritems():
            encodedOptions[k] = self.encode(v)

        retval = self.get('/%s/_design/%s/_show/%s/%s' % \
                    (self.name, design, show, document_id), encodedOptions,
                    decode=False)

        if ('error' in retval):
            raise RuntimeError ,\
                    "Error in CouchDB: viewError '%s' reason '%s'" %\
                        (retval['error'], retval['reason'])
        else:
            return retval

    def loadList(self, design, list, view, options = {}, keys = []):
        """
        Load data from a list function. This returns data that hasn't been
        decoded, since a list can return data in any format. It is expected that
        the caller of this function knows what data is being returned and how to
        deal with it appropriately.
        """
        encodedOptions = {}
        for k,v in options.iteritems():
            encodedOptions[k] = self.encode(v)

        if len(keys):
            if (encodedOptions):
                data = urllib.urlencode(encodedOptions)
                retval = self.post('/%s/_design/%s/_list/%s/%s?%s' % \
                        (self.name, design, list, view, data), {'keys':keys},
                        decode=False)
            else:
                retval = self.post('/%s/_design/%s/_list/%s/%s' % \
                        (self.name, design, list, view), {'keys':keys},
                        decode=False)
        else:
            retval = self.get('/%s/_design/%s/_list/%s/%s' % \
                        (self.name, design, list, view), encodedOptions,
                        decode=False)

        if ('error' in retval):
            raise RuntimeError ,\
                    "Error in CouchDB: viewError '%s' reason '%s'" %\
                        (retval['error'], retval['reason'])
        else:
            return retval

    def loadDocuments(self, doc_list):
        """
        Return all the documents specified in doc_list
        TODO: Batch queries by a limit, e.g. load 100 docs at a time
        """
        return self.post('/%s/_all_docs?include_docs=true' % self.name, {'keys': doc_list})

    def allDocs(self):
        """
        Return all the documents in the database
        """
        return self.get('/%s/_all_docs' % self.name)

    def info(self):
        """
        Return information about the databaes (size, number of documents etc).
        """
        return self.get('/%s/' % self.name)

    def addAttachment(self, id, rev, value, name=None, contentType=None, checksum=None, add_checksum=False):
        """
        Add an attachment stored in value to a document identified by id at revision rev.
        If specified the attachement will be uploaded as name, other wise the attachment is
        named "attachment".

        If not set CouchDB will try to determine contentType and default to text/plain.

        If checksum is specified pass this to CouchDB, it will refuse if the MD5 checksum
        doesn't match the one provided. If add_checksum is True calculate the checksum of
        the attachment and pass that into CouchDB for validation. The checksum should be the
        base64 encoded binary md5 (as returned by hashlib.md5().digest())
        """
        if (name == None):
            name = "attachment"
        req_headers = {}

        if add_checksum:
            #calculate base64 encoded MD5
            keyhash = hashlib.md5()
            keyhash.update(str(value))
            req_headers['Content-MD5'] = base64.b64encode(keyhash.digest())
        elif checksum:
            req_headers['Content-MD5'] = checksum
        return self.put('/%s/%s/%s?rev=%s' % (self.name, id, name, rev),
                         value, encode = False,
                         contentType=contentType,
                         incoming_headers = req_headers)

    def getAttachment(self, id, name = "attachment"):
        """
        _getAttachment_

        Retrieve an attachment for a couch document.
        """
        url = "/%s/%s/%s" % (self.name, id, name)
        attachment = self.get(url, None, encode = False, decode = False)

        # there has to be a better way to do this but if we're not de-jsoning
        # the return values, then this is all I can do for error checking,
        # right?
        # TODO: MAKE BETTER ERROR HANDLING
        if (attachment.find('{"error":"not_found","reason":"deleted"}') != -1):
            raise RuntimeError, "File not found, deleted"
        if (id == "nonexistantid"):
            print attachment
        return attachment

    def getUuids(self, count=None):
        """ Retrieve a list of couch-generated uuids """
        url = '/_uuids'
        if count:
            url = '%s?count=%s' % (url, count)
        return self.get(url)['uuids']

class CouchServer(Requests):
    """
    An object representing the CouchDB server, use it to list, create, delete
    and connect to databases.

    More info http://wiki.apache.org/couchdb/HTTP_database_API
    """

    def __init__(self, dburl='http://localhost:5984', timeout=None):
        """
        Set up a connection to the CouchDB server
        """
        check_server_url(dburl)
        Requests.__init__(self, dburl)
        self.url = dburl
        self.couch_type = self.__get_couch_type()
        self.timeout = timeout

    def __get_couch_type(self):
        """
        Determine which type of CouchDB instance we have connected to. This will either be couchdb or bigcouch.
        """
        server_metadata = self.get(uri='/')
        if 'bigcouch' in server_metadata:
            return CouchType.BIGCOUCH
        else:
            return CouchType.COUCHDB

    def getUuids(self, count=None):
        """ Retrieve a list of couch-generated uuids """
        url = '/_uuids'
        if count:
            url = '%s?count=%s' % (url, count)
        return self.get(url)['uuids']

    def listDatabases(self):
        "List all the databases the server hosts"
        return self.get('/_all_dbs')

    def createDatabase(self, dbname):
        """
        A database must be named with all lowercase characters (a-z),
        digits (0-9), or any of the _$()+-/ characters and must end with a slash
        in the URL.
        """
        check_name(dbname)

        self.put("/%s" % urllib.quote_plus(dbname))
        # Pass the Database constructor the unquoted name - the constructor will
        # quote it for us.
        return Database(dbname, self.url, couch_type=self.couch_type, timeout=self.timeout)

    def deleteDatabase(self, dbname):
        "Delete a database from the server"
        check_name(dbname)
        dbname = urllib.quote_plus(dbname)
        return self.delete("/%s" % dbname)

    def connectDatabase(self, dbname = 'database', create = True, size = 1000):
        """
        Return a Database instance, pointing to a database in the server. If the
        database doesn't exist create it if create is True.
        """
        check_name(dbname)
        if create and dbname not in self.listDatabases():
            return self.createDatabase(dbname)
        return Database(dbname, self.url, size, couch_type=self.couch_type, timeout=self.timeout)

    def __dbname_to_uri(self, dbname):
        """
        Convert database name to a URI if it isn't already
        """
        try:
            check_server_url(dbname)
        except:
            dbname = '%s/%s' % (self.url, dbname)
            check_server_url(dbname)
        return dbname

    def replicate(self, source, destination, continuous = False,
                  create_target = False, cancel = False, doc_ids=False,
                  filter = False, query_params = False):
        """Trigger replication between source and destination. Options are as
        described in http://wiki.apache.org/couchdb/Replication, in summary:
            continuous = bool, trigger continuous replication
            create_target = bool, implicitly create the target database
            cancel = bool, stop continuous replication
            doc_ids = list, id's of specific documents you want to replicate
            filter = string, name of the filter function you want to apply to
                     the replication, the function should be defined in a design
                     document in the source database.
            query_params = dictionary of parameters to pass into the filter
                     function

        Source and destination need to be appropriately urlquoted after the port
        number. E.g. if you have a database with /'s in the name you need to
        convert them into %2F's.

        TODO: Improve source/destination handling - can't simply URL quote,
        though, would need to decompose the URL and rebuild it.
        """
        if self.couch_type == CouchType.BIGCOUCH:
            source = self.__dbname_to_uri(source)
            destination = self.__dbname_to_uri(destination)
        else:
            if source not in self.listDatabases():
                check_server_url(source)
            if destination not in self.listDatabases():
                if create_target:
                    check_name(destination)
                else:
                    check_server_url(destination)

        data={"source":source,"target":destination}
        data.update(dict([(key, locals()[key]) for key in ("continuous", "create_target", "cancel", "doc_ids") if locals()[key]]))
        if filter:
            data["filter"] = filter
            if query_params:
                data["query_params"] = query_params
        self.post('/_replicate', data)

    def status(self):
        """
        See what active tasks are running on the server.
        """
        return {'databases': self.listDatabases(),
                'server_stats': self.get('/_stats'),
                'active_tasks': self.get('/_active_tasks')}

    def __str__(self):
        """
        List all the databases the server has
        """
        return self.listDatabases().__str__()

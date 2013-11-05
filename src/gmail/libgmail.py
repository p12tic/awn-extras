#!/usr/bin/env python
#
# libgmail -- Gmail access via Python
#
## To get the version number of the available libgmail version.
## Reminder: add date before next release. This attribute is also
## used in the setup script.
Version = '0.1.6.1' # (Aug 2007)

# Original author: follower@myrealbox.com
# Maintainers: Waseem (wdaher@mit.edu) and Stas Z (stas@linux.isbeter.nl)
#
# Contacts support added by wdaher@mit.edu and Stas Z
# (with massive initial help from
#  Adrian Holovaty's 'gmail.py'
#  and the Johnvey Gmail API)
#
# License: GPL 2.0
#
# Thanks:
#   * Live HTTP Headers <http://livehttpheaders.mozdev.org/>
#   * Gmail <http://gmail.google.com/>
#   * Google Blogoscoped <http://blog.outer-court.com/>
#   * ClientCookie <http://wwwsearch.sourceforge.net/ClientCookie/>
#     (There when I needed it...)
#   * The *first* big G. :-)
#
# NOTE:
#   You should ensure you are permitted to use this script before using it
#   to access Google's Gmail servers.
#
#
# Gmail Implementation Notes
# ==========================
#
# * Folders contain message threads, not individual messages. At present I
#   do not know any way to list all messages without processing thread list.
#

LG_DEBUG=0
from lgconstants import *

import os,pprint
import re
import urllib
import urllib2
import mimetypes
import types
from cPickle import load, dump

from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart

GMAIL_URL_LOGIN = "https://www.google.com/accounts/ServiceLoginBoxAuth"
GMAIL_URL_GMAIL = "https://mail.google.com/mail/"

# TODO: Get these on the fly?
STANDARD_FOLDERS = [U_INBOX_SEARCH, U_STARRED_SEARCH,
                    U_ALL_SEARCH, U_DRAFTS_SEARCH,
                    U_SENT_SEARCH, U_SPAM_SEARCH]

# Constants with names not from the Gmail Javascript:
# TODO: Move to `lgconstants.py`?
U_SAVEDRAFT_VIEW = "sd"

D_DRAFTINFO = "di"
# NOTE: All other DI_* field offsets seem to match the MI_* field offsets
DI_BODY = 19

versionWarned = False # If the Javascript version is different have we
                      # warned about it?


RE_SPLIT_PAGE_CONTENT = re.compile("D\((.*?)\);", re.DOTALL)

class GmailError(Exception):
    '''
    Exception thrown upon gmail-specific failures, in particular a
    failure to log in and a failure to parse responses.

    '''
    pass

class GmailSendError(Exception):
    '''
    Exception to throw if we're unable to send a message
    '''
    pass

def _parsePage(pageContent):
    """
    Parse the supplied HTML page and extract useful information from
    the embedded Javascript.

    """
    lines = pageContent.splitlines()
    data = '\n'.join([x for x in lines if x and x[0] in ['D', ')', ',', ']']])
    #data = data.replace(',,',',').replace(',,',',')
    data = re.sub(',{2,}', ',', data)

    result = []
    try:
        exec data in {'__builtins__': None}, {'D': lambda x: result.append(x)}
    except SyntaxError,info:
        print info
        raise GmailError, 'Failed to parse data returned from gmail.'

    items = result
    itemsDict = {}
    namesFoundTwice = []
    for item in items:
        name = item[0]
        try:
            parsedValue = item[1:]
        except Exception:
            parsedValue = ['']
        if itemsDict.has_key(name):
            # This handles the case where a name key is used more than
            # once (e.g. mail items, mail body etc) and automatically
            # places the values into list.
            # TODO: Check this actually works properly, it's early... :-)

            if len(parsedValue) and type(parsedValue[0]) is types.ListType:
                    for item in parsedValue:
                        itemsDict[name].append(item)
            else:
                itemsDict[name].append(parsedValue)
        else:
            if len(parsedValue) and type(parsedValue[0]) is types.ListType:
                    itemsDict[name] = []
                    for item in parsedValue:
                        itemsDict[name].append(item)
            else:
                itemsDict[name] = [parsedValue]

    return itemsDict

def _splitBunches(infoItems):# Is this still needed ?? Stas
    """
    Utility to help make it easy to iterate over each item separately,
    even if they were bunched on the page.
    """
    result= []
    # TODO: Decide if this is the best approach.
    for group in infoItems:
        if type(group) == tuple:
            result.extend(group)
        else:
            result.append(group)
    return result

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def __init__(self, cookiejar):
        self.cookiejar = cookiejar

    def http_error_302(self, req, fp, code, msg, headers):
        # The location redirect doesn't seem to change
        # the hostname header appropriately, so we do
        # by hand. (Is this a bug in urllib2?)
        new_host = re.match(r'http[s]*://(.*?\.google\.com)',
                            headers.getheader('Location'))
        if new_host:
            req.add_header("Host", new_host.groups()[0])
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        return result

class CookieJar:
    """
    A rough cookie handler, intended to only refer to one domain.

    Does no expiry or anything like that.

    (The only reason this is here is so I don't have to require
    the `ClientCookie` package.)

    """

    def __init__(self):
        """
        """
        self._cookies = {}


    def extractCookies(self, headers, nameFilter = None):
        """
        """
        # TODO: Do this all more nicely?
        for cookie in headers.getheaders('Set-Cookie'):
            name, value = (cookie.split("=", 1) + [""])[:2]
            if LG_DEBUG: print "Extracted cookie `%s`" % (name)
            if not nameFilter or name in nameFilter:
                self._cookies[name] = value.split(";")[0]
                if LG_DEBUG: print "Stored cookie `%s` value `%s`" % (name, self._cookies[name])
                if self._cookies[name] == "EXPIRED":
                    if LG_DEBUG:
                        print "We got an expired cookie: %s:%s, deleting." % (name, self._cookies[name])
                    del self._cookies[name]


    def addCookie(self, name, value):
        """
        """
        self._cookies[name] = value


    def setCookies(self, request):
        """
        """
        request.add_header('Cookie',
                           ";".join(["%s=%s" % (k,v)
                                     for k,v in self._cookies.items()]))



def _buildURL(**kwargs):
    """
    """
    return "%s?%s" % (URL_GMAIL, urllib.urlencode(kwargs))



def _paramsToMime(params, filenames, files):
    """
    """
    mimeMsg = MIMEMultipart("form-data")

    for name, value in params.iteritems():
        mimeItem = MIMEText(value)
        mimeItem.add_header("Content-Disposition", "form-data", name=name)

        # TODO: Handle this better...?
        for hdr in ['Content-Type','MIME-Version','Content-Transfer-Encoding']:
            del mimeItem[hdr]

        mimeMsg.attach(mimeItem)

    if filenames or files:
        filenames = filenames or []
        files = files or []
        for idx, item in enumerate(filenames + files):
            # TODO: This is messy, tidy it...
            if isinstance(item, str):
                # We assume it's a file path...
                filename = item
                contentType = mimetypes.guess_type(filename)[0]
                payload = open(filename, "rb").read()
            else:
                # We assume it's an `email.Message.Message` instance...
                # TODO: Make more use of the pre-encoded information?
                filename = item.get_filename()
                contentType = item.get_content_type()
                payload = item.get_payload(decode=True)

            if not contentType:
                contentType = "application/octet-stream"

            mimeItem = MIMEBase(*contentType.split("/"))
            mimeItem.add_header("Content-Disposition", "form-data",
                                name="file%s" % idx, filename=filename)
            # TODO: Encode the payload?
            mimeItem.set_payload(payload)

            # TODO: Handle this better...?
            for hdr in ['MIME-Version','Content-Transfer-Encoding']:
                del mimeItem[hdr]

            mimeMsg.attach(mimeItem)

    del mimeMsg['MIME-Version']

    return mimeMsg


class GmailLoginFailure(Exception):
    """
    Raised whenever the login process fails--could be wrong username/password,
    or Gmail service error, for example.
    Extract the error message like this:
    try:
        foobar
    except GmailLoginFailure,e:
        mesg = e.message# or
        print e# uses the __str__
    """
    def __init__(self,message):
        self.message = message
    def __str__(self):
        return repr(self.message)

class GmailAccount:
    """
    """

    def __init__(self, name = "", pw = "", state = None, domain = None):
        global URL_LOGIN, URL_GMAIL
        """
        """
        self.domain = domain
        if self.domain:
            URL_LOGIN = "https://www.google.com/a/" + self.domain + "/LoginAction"
            URL_GMAIL = "http://mail.google.com/a/" + self.domain
        else:
            URL_LOGIN = GMAIL_URL_LOGIN
            URL_GMAIL = GMAIL_URL_GMAIL
        if name and pw:
            self.name = name
            self._pw = pw
            self._cookieJar = CookieJar()
            self.opener = urllib2.build_opener(
                                urllib2.HTTPHandler(debuglevel=0),
                                urllib2.HTTPSHandler(debuglevel=0),
                                SmartRedirectHandler(self._cookieJar))
        elif state:
            # TODO: Check for stale state cookies?
            self.name, self._cookieJar = state.state
        else:
            raise ValueError("GmailAccount must be instantiated with " \
                             "either GmailSessionState object or name " \
                             "and password.")
	self.inboxunread = None
        self._cachedQuotaInfo = None
        self._cachedLabelNames = None


    def login(self):
        """
        """
        # TODO: Throw exception if we were instantiated with state?
        if self.domain:
            data = urllib.urlencode({'continue': URL_GMAIL,
                                     'at'      : 'null',
                                     'service' : 'mail',
                                     'userName': self.name,
                                     'password': self._pw,
                                     })
        else:
            data = urllib.urlencode({'continue': URL_GMAIL,
                                     'Email': self.name,
                                     'Passwd': self._pw,
                                     })

        headers = {'Host': 'www.google.com',
                   'User-Agent': 'Mozilla/5.0 (Compatible; libgmail-python)'}

        req = urllib2.Request(URL_LOGIN, data=data, headers=headers)
        pageData = self._retrievePage(req)

        if not self.domain:
        # The GV cookie no longer comes in this page for
        # "Apps", so this bottom portion is unnecessary for it.
            # This requests the page that provides the required "GV" cookie.
            RE_PAGE_REDIRECT = 'CheckCookie\?continue=([^"\']+)'

            # TODO: Catch more failure exceptions here...?
            try:
                link = re.search(RE_PAGE_REDIRECT, pageData).group(1)
                redirectURL = urllib2.unquote(link)
                redirectURL = redirectURL.replace('\\x26', '&')

            except AttributeError:
                raise GmailLoginFailure("Login failed. (Wrong username/password?)")
            # We aren't concerned with the actual content of this page,
            # just the cookie that is returned with it.
            pageData = self._retrievePage(redirectURL)

    def _retrievePage(self, urlOrRequest):
        """
        """
        if self.opener is None:
            raise "Cannot find urlopener"

        if not isinstance(urlOrRequest, urllib2.Request):
            req = urllib2.Request(urlOrRequest)
        else:
            req = urlOrRequest

        self._cookieJar.setCookies(req)
        req.add_header('User-Agent',
                       'Mozilla/5.0 (Compatible; libgmail-python)')

        try:
            resp = self.opener.open(req)
        except urllib2.HTTPError,info:
            print info
            return None
        pageData = resp.read()

        # Extract cookies here
        self._cookieJar.extractCookies(resp.headers)

        # TODO: Enable logging of page data for debugging purposes?

        return pageData


    def _parsePage(self, urlOrRequest):
        """
        Retrieve & then parse the requested page content.

        """
        items = _parsePage(self._retrievePage(urlOrRequest))

		
        # Automatically cache some things like quota usage.
        # TODO: Cache more?
        # TODO: Expire cached values?
        # TODO: Do this better.
        try:

            #self._cachedQuotaInfo = items[D_QUOTA]
	    self.inboxunread = items['ds']
	
	

        except KeyError:
            pass
        #pprint.pprint(items)

        try:
            self._cachedLabelNames = [category[CT_NAME] for category in items[D_CATEGORIES][0]]
        except KeyError:
            pass

        return items


    def _parseSearchResult(self, searchType, start = 0, **kwargs):
        """
        """
        params = {U_SEARCH: searchType,
                  U_START: start,
                  U_VIEW: U_THREADLIST_VIEW,
                  }
        params.update(kwargs)
        return self._parsePage(_buildURL(**params))


    def _parseThreadSearch(self, searchType, allPages = False, **kwargs):
        """

        Only works for thread-based results at present. # TODO: Change this?
        """
        start = 0
        tot = 0
        threadsInfo = []
        # Option to get *all* threads if multiple pages are used.
        while (start == 0) or (allPages and
                               len(threadsInfo) < threadListSummary[TS_TOTAL]):

                items = self._parseSearchResult(searchType, start, **kwargs)
                #TODO: Handle single & zero result case better? Does this work?
                try:
                    threads = items[D_THREAD]
                except KeyError:
                    break
                else:
                    for th in threads:
                        if not type(th[0]) is types.ListType:
                            th = [th]
                        threadsInfo.append(th)
                    # TODO: Check if the total or per-page values have changed?
                    threadListSummary = items[D_THREADLIST_SUMMARY][0]
                    threadsPerPage = threadListSummary[TS_NUM]

                    start += threadsPerPage

        # TODO: Record whether or not we retrieved all pages..?
        return GmailSearchResult(self, (searchType, kwargs), threadsInfo)


    def _retrieveJavascript(self, version = ""):
        """

        Note: `version` seems to be ignored.
        """
        return self._retrievePage(_buildURL(view = U_PAGE_VIEW,
                                            name = "js",
                                            ver = version))


    def getMessagesByFolder(self, folderName, allPages = False):
        """

        Folders contain conversation/message threads.

          `folderName` -- As set in Gmail interface.

        Returns a `GmailSearchResult` instance.

        *** TODO: Change all "getMessagesByX" to "getThreadsByX"? ***
        """
        return self._parseThreadSearch(folderName, allPages = allPages)


    def getMessagesByQuery(self, query,  allPages = False):
        """

        Returns a `GmailSearchResult` instance.
        """
        return self._parseThreadSearch(U_QUERY_SEARCH, q = query,
                                       allPages = allPages)


    def getQuotaInfo(self, refresh = False):
        """

        Return MB used, Total MB and percentage used.
        """
        # TODO: Change this to a property.
        if not self._cachedQuotaInfo or refresh:
            # TODO: Handle this better...
            self.getMessagesByFolder(U_INBOX_SEARCH)

        return self._cachedQuotaInfo[0][:3]

    def getunreadInfo(self):
        """

        Return MB used, Total MB and percentage used.
        """
	self.getMessagesByFolder(U_INBOX_SEARCH)
	
        # TODO: Change this to a property.
        return self.inboxunread[0][:1]
	
    def getLabelNames(self, refresh = False):
        """
        """
        # TODO: Change this to a property?
        if not self._cachedLabelNames or refresh:
            # TODO: Handle this better...
            self.getMessagesByFolder(U_INBOX_SEARCH)

        return self._cachedLabelNames


    def getMessagesByLabel(self, label, allPages = False):
        """
        """
        return self._parseThreadSearch(U_CATEGORY_SEARCH,
                                       cat=label, allPages = allPages)

    def getRawMessage(self, msgId):
        """
        """
        # U_ORIGINAL_MESSAGE_VIEW seems the only one that returns a page.
        # All the other U_* results in a 404 exception. Stas
        PageView = U_ORIGINAL_MESSAGE_VIEW
        return self._retrievePage(
            _buildURL(view=PageView, th=msgId))

    def getUnreadMessages(self):
        """
        """
        return self._parseThreadSearch(U_QUERY_SEARCH,
                                        q = "is:" + U_AS_SUBSET_UNREAD)


    def getUnreadMsgCount(self):
        """
        """
        items = self._parseSearchResult(U_QUERY_SEARCH,
                                        q = "is:" + U_AS_SUBSET_UNREAD)
        try:
            result = items[D_THREADLIST_SUMMARY][0][TS_TOTAL_MSGS]
        except KeyError:
            result = 0
        return result


    def _getActionToken(self):
        """
        """
        try:
            at = self._cookieJar._cookies[ACTION_TOKEN_COOKIE]
        except KeyError:
            self.getLabelNames(True)
            at = self._cookieJar._cookies[ACTION_TOKEN_COOKIE]

        return at


    def sendMessage(self, msg, asDraft = False, _extraParams = None):
        """

          `msg` -- `GmailComposedMessage` instance.

          `_extraParams` -- Dictionary containing additional parameters
                            to put into POST message. (Not officially
                            for external use, more to make feature
                            additional a little easier to play with.)

        Note: Now returns `GmailMessageStub` instance with populated
              `id` (and `_account`) fields on success or None on failure.

        """
        # TODO: Handle drafts separately?
        params = {U_VIEW: [U_SENDMAIL_VIEW, U_SAVEDRAFT_VIEW][asDraft],
                  U_REFERENCED_MSG: "",
                  U_THREAD: "",
                  U_DRAFT_MSG: "",
                  U_COMPOSEID: "1",
                  U_ACTION_TOKEN: self._getActionToken(),
                  U_COMPOSE_TO: msg.to,
                  U_COMPOSE_CC: msg.cc,
                  U_COMPOSE_BCC: msg.bcc,
                  "subject": msg.subject,
                  "msgbody": msg.body,
                  }

        if _extraParams:
            params.update(_extraParams)

        # Amongst other things, I used the following post to work out this:
        # <http://groups.google.com/groups?
        #  selm=mailman.1047080233.20095.python-list%40python.org>
        mimeMessage = _paramsToMime(params, msg.filenames, msg.files)

        #### TODO: Ughh, tidy all this up & do it better...
        ## This horrible mess is here for two main reasons:
        ##  1. The `Content-Type` header (which also contains the boundary
        ##     marker) needs to be extracted from the MIME message so
        ##     we can send it as the request `Content-Type` header instead.
        ##  2. It seems the form submission needs to use "\r\n" for new
        ##     lines instead of the "\n" returned by `as_string()`.
        ##     I tried changing the value of `NL` used by the `Generator` class
        ##     but it didn't work so I'm doing it this way until I figure
        ##     out how to do it properly. Of course, first try, if the payloads
        ##     contained "\n" sequences they got replaced too, which corrupted
        ##     the attachments. I could probably encode the submission,
        ##     which would probably be nicer, but in the meantime I'm kludging
        ##     this workaround that replaces all non-text payloads with a
        ##     marker, changes all "\n" to "\r\n" and finally replaces the
        ##     markers with the original payloads.
        ## Yeah, I know, it's horrible, but hey it works doesn't it? If you've
        ## got a problem with it, fix it yourself & give me the patch!
        ##
        origPayloads = {}
        FMT_MARKER = "&&&&&&%s&&&&&&"

        for i, m in enumerate(mimeMessage.get_payload()):
            if not isinstance(m, MIMEText): #Do we care if we change text ones?
                origPayloads[i] = m.get_payload()
                m.set_payload(FMT_MARKER % i)

        mimeMessage.epilogue = ""
        msgStr = mimeMessage.as_string()
        contentTypeHeader, data = msgStr.split("\n\n", 1)
        contentTypeHeader = contentTypeHeader.split(":", 1)
        data = data.replace("\n", "\r\n")
        for k,v in origPayloads.iteritems():
            data = data.replace(FMT_MARKER % k, v)
        ####

        req = urllib2.Request(_buildURL(), data = data)
        req.add_header(*contentTypeHeader)
        items = self._parsePage(req)

        # TODO: Check composeid?
        # Sometimes we get the success message
        # but the id is 0 and no message is sent
        result = None
        resultInfo = items[D_SENDMAIL_RESULT][0]

        if resultInfo[SM_SUCCESS]:
            result = GmailMessageStub(id = resultInfo[SM_NEWTHREADID],
                                      _account = self)
        else:
            raise GmailSendError, resultInfo[SM_MSG]
        return result


    def trashMessage(self, msg):
        """
        """
        # TODO: Decide if we should make this a method of `GmailMessage`.
        # TODO: Should we check we have been given a `GmailMessage` instance?
        params = {
            U_ACTION: U_DELETEMESSAGE_ACTION,
            U_ACTION_MESSAGE: msg.id,
            U_ACTION_TOKEN: self._getActionToken(),
            }

        items = self._parsePage(_buildURL(**params))

        # TODO: Mark as trashed on success?
        return (items[D_ACTION_RESULT][0][AR_SUCCESS] == 1)


    def _doThreadAction(self, actionId, thread):
        """
        """
        # TODO: Decide if we should make this a method of `GmailThread`.
        # TODO: Should we check we have been given a `GmailThread` instance?
        params = {
            U_SEARCH: U_ALL_SEARCH, #TODO:Check this search value always works.
            U_VIEW: U_UPDATE_VIEW,
            U_ACTION: actionId,
            U_ACTION_THREAD: thread.id,
            U_ACTION_TOKEN: self._getActionToken(),
            }

        items = self._parsePage(_buildURL(**params))

        return (items[D_ACTION_RESULT][0][AR_SUCCESS] == 1)


    def trashThread(self, thread):
        """
        """
        # TODO: Decide if we should make this a method of `GmailThread`.
        # TODO: Should we check we have been given a `GmailThread` instance?

        result = self._doThreadAction(U_MARKTRASH_ACTION, thread)

        # TODO: Mark as trashed on success?
        return result


    def _createUpdateRequest(self, actionId): #extraData):
        """
        Helper method to create a Request instance for an update (view)
        action.

        Returns populated `Request` instance.
        """
        params = {
            U_VIEW: U_UPDATE_VIEW,
            }

        data = {
            U_ACTION: actionId,
            U_ACTION_TOKEN: self._getActionToken(),
            }

        #data.update(extraData)

        req = urllib2.Request(_buildURL(**params),
                              data = urllib.urlencode(data))

        return req


    # TODO: Extract additional common code from handling of labels?
    def createLabel(self, labelName):
        """
        """
        req = self._createUpdateRequest(U_CREATECATEGORY_ACTION + labelName)

        # Note: Label name cache is updated by this call as well. (Handy!)
        items = self._parsePage(req)
        print items
        return (items[D_ACTION_RESULT][0][AR_SUCCESS] == 1)


    def deleteLabel(self, labelName):
        """
        """
        # TODO: Check labelName exits?
        req = self._createUpdateRequest(U_DELETECATEGORY_ACTION + labelName)

        # Note: Label name cache is updated by this call as well. (Handy!)
        items = self._parsePage(req)

        return (items[D_ACTION_RESULT][0][AR_SUCCESS] == 1)


    def renameLabel(self, oldLabelName, newLabelName):
        """
        """
        # TODO: Check oldLabelName exits?
        req = self._createUpdateRequest("%s%s^%s" % (U_RENAMECATEGORY_ACTION,
                                                   oldLabelName, newLabelName))

        # Note: Label name cache is updated by this call as well. (Handy!)
        items = self._parsePage(req)

        return (items[D_ACTION_RESULT][0][AR_SUCCESS] == 1)

    def storeFile(self, filename, label = None):
        """
        """
        # TODO: Handle files larger than single attachment size.
        # TODO: Allow file data objects to be supplied?
        FILE_STORE_VERSION = "FSV_01"
        FILE_STORE_SUBJECT_TEMPLATE = "%s %s" % (FILE_STORE_VERSION, "%s")

        subject = FILE_STORE_SUBJECT_TEMPLATE % os.path.basename(filename)

        msg = GmailComposedMessage(to="", subject=subject, body="",
                                   filenames=[filename])

        draftMsg = self.sendMessage(msg, asDraft = True)

        if draftMsg and label:
            draftMsg.addLabel(label)

        return draftMsg

    ## CONTACTS SUPPORT
    def getContacts(self):
        """
        Returns a GmailContactList object
        that has all the contacts in it as
        GmailContacts
        """
        contactList = []
        # pnl = a is necessary to get *all* contacts
        myUrl = _buildURL(view='cl',search='contacts', pnl='a')
        myData = self._parsePage(myUrl)
        # This comes back with a dictionary
        # with entry 'cl'
        addresses = myData['cl']
        for entry in addresses:
            if len(entry) >= 6 and entry[0]=='ce':
                newGmailContact = GmailContact(entry[1], entry[2], entry[4], entry[5])
                #### new code used to get all the notes
                #### not used yet due to lockdown problems
                ##rawnotes = self._getSpecInfo(entry[1])
                ##print rawnotes
                ##newGmailContact = GmailContact(entry[1], entry[2], entry[4],rawnotes)
                contactList.append(newGmailContact)

        return GmailContactList(contactList)

    def addContact(self, myContact, *extra_args):
        """
        Attempts to add a GmailContact to the gmail
        address book. Returns true if successful,
        false otherwise

        Please note that after version 0.1.3.3,
        addContact takes one argument of type
        GmailContact, the contact to add.

        The old signature of:
        addContact(name, email, notes='') is still
        supported, but deprecated.
        """
        if len(extra_args) > 0:
            # The user has passed in extra arguments
            # He/she is probably trying to invoke addContact
            # using the old, deprecated signature of:
            # addContact(self, name, email, notes='')
            # Build a GmailContact object and use that instead
            (name, email) = (myContact, extra_args[0])
            if len(extra_args) > 1:
                notes = extra_args[1]
            else:
                notes = ''
            myContact = GmailContact(-1, name, email, notes)

        # TODO: In the ideal world, we'd extract these specific
        # constants into a nice constants file

        # This mostly comes from the Johnvey Gmail API,
        # but also from the gmail.py cited earlier
        myURL = _buildURL(view='up')

        myDataList =  [ ('act','ec'),
                        ('at', self._cookieJar._cookies['GMAIL_AT']), # Cookie data?
                        ('ct_nm', myContact.getName()),
                        ('ct_em', myContact.getEmail()),
                        ('ct_id', -1 )
                       ]

        notes = myContact.getNotes()
        if notes != '':
            myDataList.append( ('ctf_n', notes) )

        validinfokeys = [
                        'i', # IM
                        'p', # Phone
                        'd', # Company
                        'a', # ADR
                        'e', # Email
                        'm', # Mobile
                        'b', # Pager
                        'f', # Fax
                        't', # Title
                        'o', # Other
                        ]

        moreInfo = myContact.getMoreInfo()
        ctsn_num = -1
        if moreInfo != {}:
            for ctsf,ctsf_data in moreInfo.items():
                ctsn_num += 1
                # data section header, WORK, HOME,...
                sectionenum ='ctsn_%02d' % ctsn_num
                myDataList.append( ( sectionenum, ctsf ))
                ctsf_num = -1

                if isinstance(ctsf_data[0],str):
                    ctsf_num += 1
                    # data section
                    subsectionenum = 'ctsf_%02d_%02d_%s' % (ctsn_num, ctsf_num, ctsf_data[0])  # ie. ctsf_00_01_p
                    myDataList.append( (subsectionenum, ctsf_data[1]) )
                else:
                    for info in ctsf_data:
                        if validinfokeys.count(info[0]) > 0:
                            ctsf_num += 1
                            # data section
                            subsectionenum = 'ctsf_%02d_%02d_%s' % (ctsn_num, ctsf_num, info[0])  # ie. ctsf_00_01_p
                            myDataList.append( (subsectionenum, info[1]) )

        myData = urllib.urlencode(myDataList)
        request = urllib2.Request(myURL,
                                  data = myData)
        pageData = self._retrievePage(request)

        if pageData.find("The contact was successfully added") == -1:
            print pageData
            if pageData.find("already has the email address") > 0:
                raise Exception("Someone with same email already exists in Gmail.")
            elif pageData.find("https://www.google.com/accounts/ServiceLogin"):
                raise Exception("Login has expired.")
            return False
        else:
            return True

    def _removeContactById(self, id):
        """
        Attempts to remove the contact that occupies
        id "id" from the gmail address book.
        Returns True if successful,
        False otherwise.

        This is a little dangerous since you don't really
        know who you're deleting. Really,
        this should return the name or something of the
        person we just killed.

        Don't call this method.
        You should be using removeContact instead.
        """
        myURL = _buildURL(search='contacts', ct_id = id, c=id, act='dc', at=self._cookieJar._cookies['GMAIL_AT'], view='up')
        pageData = self._retrievePage(myURL)

        if pageData.find("The contact has been deleted") == -1:
            return False
        else:
            return True

    def removeContact(self, gmailContact):
        """
        Attempts to remove the GmailContact passed in
        Returns True if successful, False otherwise.
        """
        # Let's re-fetch the contact list to make
        # sure we're really deleting the guy
        # we think we're deleting
        newContactList = self.getContacts()
        newVersionOfPersonToDelete = newContactList.getContactById(gmailContact.getId())
        # Ok, now we need to ensure that gmailContact
        # is the same as newVersionOfPersonToDelete
        # and then we can go ahead and delete him/her
        if (gmailContact == newVersionOfPersonToDelete):
            return self._removeContactById(gmailContact.getId())
        else:
            # We have a cache coherency problem -- someone
            # else now occupies this ID slot.
            # TODO: Perhaps signal this in some nice way
            #       to the end user?

            print "Unable to delete."
            print "Has someone else been modifying the contacts list while we have?"
            print "Old version of person:",gmailContact
            print "New version of person:",newVersionOfPersonToDelete
            return False

## Don't remove this. contact stas
##    def _getSpecInfo(self,id):
##        """
##        Return all the notes data.
##        This is currently not used due to the fact that it requests pages in
##        a dos attack manner.
##        """
##        myURL =_buildURL(search='contacts',ct_id=id,c=id,\
##                        at=self._cookieJar._cookies['GMAIL_AT'],view='ct')
##        pageData = self._retrievePage(myURL)
##        myData = self._parsePage(myURL)
##        #print "\nmyData form _getSpecInfo\n",myData
##        rawnotes = myData['cov'][7]
##        return rawnotes

class GmailContact:
    """
    Class for storing a Gmail Contacts list entry
    """
    def __init__(self, name, email, *extra_args):
        """
        Returns a new GmailContact object
        (you can then call addContact on this to commit
         it to the Gmail addressbook, for example)

        Consider calling setNotes() and setMoreInfo()
        to add extended information to this contact
        """
        # Support populating other fields if we're trying
        # to invoke this the old way, with the old constructor
        # whose signature was __init__(self, id, name, email, notes='')
        id = -1
        notes = ''

        if len(extra_args) > 0:
            (id, name) = (name, email)
            email = extra_args[0]
            if len(extra_args) > 1:
                notes = extra_args[1]
            else:
                notes = ''

        self.id = id
        self.name = name
        self.email = email
        self.notes = notes
        self.moreInfo = {}
    def __str__(self):
        return "%s %s %s %s" % (self.id, self.name, self.email, self.notes)
    def __eq__(self, other):
        if not isinstance(other, GmailContact):
            return False
        return (self.getId() == other.getId()) and \
               (self.getName() == other.getName()) and \
               (self.getEmail() == other.getEmail()) and \
               (self.getNotes() == other.getNotes())
    def getId(self):
        return self.id
    def getName(self):
        return self.name
    def getEmail(self):
        return self.email
    def getNotes(self):
        return self.notes
    def setNotes(self, notes):
        """
        Sets the notes field for this GmailContact
        Note that this does NOT change the note
        field on Gmail's end; only adding or removing
        contacts modifies them
        """
        self.notes = notes

    def getMoreInfo(self):
        return self.moreInfo
    def setMoreInfo(self, moreInfo):
        """
        moreInfo format
        ---------------
        Use special key values::
                        'i' =  IM
                        'p' =  Phone
                        'd' =  Company
                        'a' =  ADR
                        'e' =  Email
                        'm' =  Mobile
                        'b' =  Pager
                        'f' =  Fax
                        't' =  Title
                        'o' =  Other

        Simple example::

        moreInfo = {'Home': ( ('a','852 W Barry'),
                              ('p', '1-773-244-1980'),
                              ('i', 'aim:brianray34') ) }

        Complex example::

        moreInfo = {
            'Personal': (('e', 'Home Email'),
                         ('f', 'Home Fax')),
            'Work': (('d', 'Sample Company'),
                     ('t', 'Job Title'),
                     ('o', 'Department: Department1'),
                     ('o', 'Department: Department2'),
                     ('p', 'Work Phone'),
                     ('m', 'Mobile Phone'),
                     ('f', 'Work Fax'),
                     ('b', 'Pager')) }
        """
        self.moreInfo = moreInfo
    def getVCard(self):
        """Returns a vCard 3.0 for this
        contact, as a string"""
        # The \r is is to comply with the RFC2425 section 5.8.1
        vcard = "BEGIN:VCARD\r\n"
        vcard += "VERSION:3.0\r\n"
        ## Deal with multiline notes
        ##vcard += "NOTE:%s\n" % self.getNotes().replace("\n","\\n")
        vcard += "NOTE:%s\r\n" % self.getNotes()
        # Fake-out N by splitting up whatever we get out of getName
        # This might not always do 'the right thing'
        # but it's a *reasonable* compromise
        fullname = self.getName().split()
        fullname.reverse()
        vcard += "N:%s" % ';'.join(fullname) + "\r\n"
        vcard += "FN:%s\r\n" % self.getName()
        vcard += "EMAIL;TYPE=INTERNET:%s\r\n" % self.getEmail()
        vcard += "END:VCARD\r\n\r\n"
        # Final newline in case we want to put more than one in a file
        return vcard

class GmailContactList:
    """
    Class for storing an entire Gmail contacts list
    and retrieving contacts by Id, Email address, and name
    """
    def __init__(self, contactList):
        self.contactList = contactList
    def __str__(self):
        return '\n'.join([str(item) for item in self.contactList])
    def getCount(self):
        """
        Returns number of contacts
        """
        return len(self.contactList)
    def getAllContacts(self):
        """
        Returns an array of all the
        GmailContacts
        """
        return self.contactList
    def getContactByName(self, name):
        """
        Gets the first contact in the
        address book whose name is 'name'.

        Returns False if no contact
        could be found
        """
        nameList = self.getContactListByName(name)
        if len(nameList) > 0:
            return nameList[0]
        else:
            return False
    def getContactByEmail(self, email):
        """
        Gets the first contact in the
        address book whose name is 'email'.
        As of this writing, Gmail insists
        upon a unique email; i.e. two contacts
        cannot share an email address.

        Returns False if no contact
        could be found
        """
        emailList = self.getContactListByEmail(email)
        if len(emailList) > 0:
            return emailList[0]
        else:
            return False
    def getContactById(self, myId):
        """
        Gets the first contact in the
        address book whose id is 'myId'.

        REMEMBER: ID IS A STRING

        Returns False if no contact
        could be found
        """
        idList = self.getContactListById(myId)
        if len(idList) > 0:
            return idList[0]
        else:
            return False
    def getContactListByName(self, name):
        """
        This function returns a LIST
        of GmailContacts whose name is
        'name'.

        Returns an empty list if no contacts
        were found
        """
        nameList = []
        for entry in self.contactList:
            if entry.getName() == name:
                nameList.append(entry)
        return nameList
    def getContactListByEmail(self, email):
        """
        This function returns a LIST
        of GmailContacts whose email is
        'email'. As of this writing, two contacts
        cannot share an email address, so this
        should only return just one item.
        But it doesn't hurt to be prepared?

        Returns an empty list if no contacts
        were found
        """
        emailList = []
        for entry in self.contactList:
            if entry.getEmail() == email:
                emailList.append(entry)
        return emailList
    def getContactListById(self, myId):
        """
        This function returns a LIST
        of GmailContacts whose id is
        'myId'. We expect there only to
        be one, but just in case!

        Remember: ID IS A STRING

        Returns an empty list if no contacts
        were found
        """
        idList = []
        for entry in self.contactList:
            if entry.getId() == myId:
                idList.append(entry)
        return idList

class GmailSearchResult:
    """
    """

    def __init__(self, account, search, threadsInfo):
        """

        `threadsInfo` -- As returned from Gmail but unbunched.
        """
        #print "\nthreadsInfo\n",threadsInfo
        try:
            if not type(threadsInfo[0]) is types.ListType:
                threadsInfo = [threadsInfo]
        except IndexError:
            print "No messages found"

        self._account = account
        self.search = search # TODO: Turn into object + format nicely.
        self._threads = []

        for thread in threadsInfo:
            self._threads.append(GmailThread(self, thread[0]))


    def __iter__(self):
        """
        """
        return iter(self._threads)

    def __len__(self):
        """
        """
        return len(self._threads)

    def __getitem__(self,key):
        """
        """
        return self._threads.__getitem__(key)


class GmailSessionState:
    """
    """

    def __init__(self, account = None, filename = ""):
        """
        """
        if account:
            self.state = (account.name, account._cookieJar)
        elif filename:
            self.state = load(open(filename, "rb"))
        else:
            raise ValueError("GmailSessionState must be instantiated with " \
                             "either GmailAccount object or filename.")


    def save(self, filename):
        """
        """
        dump(self.state, open(filename, "wb"), -1)


class _LabelHandlerMixin(object):
    """

    Note: Because a message id can be used as a thread id this works for
          messages as well as threads.
    """
    def __init__(self):
        self._labels = None

    def _makeLabelList(self, labelList):
        self._labels = labelList

    def addLabel(self, labelName):
        """
        """
        # Note: It appears this also automatically creates new labels.
        result = self._account._doThreadAction(U_ADDCATEGORY_ACTION+labelName,
                                               self)
        if not self._labels:
            self._makeLabelList([])
        # TODO: Caching this seems a little dangerous; suppress duplicates maybe?
        self._labels.append(labelName)
        return result


    def removeLabel(self, labelName):
        """
        """
        # TODO: Check label is already attached?
        # Note: An error is not generated if the label is not already attached.
        result = \
               self._account._doThreadAction(U_REMOVECATEGORY_ACTION+labelName,
                                             self)

        removeLabel = True
        try:
            self._labels.remove(labelName)
        except:
            removeLabel = False
            pass

        # If we don't check both, we might end up in some weird inconsistent state
        return result and removeLabel

    def getLabels(self):
        return self._labels



class GmailThread(_LabelHandlerMixin):
    """
    Note: As far as I can tell, the "canonical" thread id is always the same
          as the id of the last message in the thread. But it appears that
          the id of any message in the thread can be used to retrieve
          the thread information.

    """

    def __init__(self, parent, threadsInfo):
        """
        """
        _LabelHandlerMixin.__init__(self)

        # TODO Handle this better?
        self._parent = parent
        self._account = self._parent._account

        self.id = threadsInfo[T_THREADID] # TODO: Change when canonical updated?
        self.subject = threadsInfo[T_SUBJECT_HTML]

        self.snippet = threadsInfo[T_SNIPPET_HTML]
        #self.extraSummary = threadInfo[T_EXTRA_SNIPPET] #TODO: What is this?

        # TODO: Store other info?
        # Extract number of messages in thread/conversation.

        self._authors = threadsInfo[T_AUTHORS_HTML]
        self.info = threadsInfo

        try:
            # TODO: Find out if this information can be found another way...
            #       (Without another page request.)
            self._length = int(re.search("\((\d+?)\)\Z",
                                         self._authors).group(1))
        except AttributeError,info:
            # If there's no message count then the thread only has one message.
            self._length = 1

        # TODO: Store information known about the last message  (e.g. id)?
        self._messages = []

        # Populate labels
        self._makeLabelList(threadsInfo[T_CATEGORIES])

    def __getattr__(self, name):
        """
        Dynamically dispatch some interesting thread properties.
        """
        attrs = { 'unread': T_UNREAD,
                  'star': T_STAR,
                  'date': T_DATE_HTML,
                  'authors': T_AUTHORS_HTML,
                  'flags': T_FLAGS,
                  'subject': T_SUBJECT_HTML,
                  'snippet': T_SNIPPET_HTML,
                  'categories': T_CATEGORIES,
                  'attach': T_ATTACH_HTML,
                  'matching_msgid': T_MATCHING_MSGID,
                  'extra_snippet': T_EXTRA_SNIPPET }
        if name in attrs:
            return self.info[ attrs[name] ];

        raise AttributeError("no attribute %s" % name)

    def __len__(self):
        """
        """
        return self._length


    def __iter__(self):
        """
        """
        if not self._messages:
            self._messages = self._getMessages(self)

        return iter(self._messages)

    def __getitem__(self, key):
        """
        """
        if not self._messages:
            self._messages = self._getMessages(self)
        try:
            result = self._messages.__getitem__(key)
        except IndexError:
            result = []
        return result

    def _getMessages(self, thread):
        """
        """
        # TODO: Do this better.
        # TODO: Specify the query folder using our specific search?
        items = self._account._parseSearchResult(U_QUERY_SEARCH,
                                                 view = U_CONVERSATION_VIEW,
                                                 th = thread.id,
                                                 q = "in:anywhere")
        result = []
        # TODO: Handle this better?
        # Note: This handles both draft & non-draft messages in a thread...
        for key, isDraft in [(D_MSGINFO, False), (D_DRAFTINFO, True)]:
            try:
                msgsInfo = items[key]
            except KeyError:
                # No messages of this type (e.g. draft or non-draft)
                continue
            else:
                # TODO: Handle special case of only 1 message in thread better?
                if type(msgsInfo[0]) != types.ListType:
                    msgsInfo = [msgsInfo]
                for msg in msgsInfo:
                    result += [GmailMessage(thread, msg, isDraft = isDraft)]


        return result

class GmailMessageStub(_LabelHandlerMixin):
    """

    Intended to be used where not all message information is known/required.

    NOTE: This may go away.
    """

    # TODO: Provide way to convert this to a full `GmailMessage` instance
    #       or allow `GmailMessage` to be created without all info?

    def __init__(self, id = None, _account = None):
        """
        """
        _LabelHandlerMixin.__init__(self)
        self.id = id
        self._account = _account



class GmailMessage(object):
    """
    """

    def __init__(self, parent, msgData, isDraft = False):
        """

        Note: `msgData` can be from either D_MSGINFO or D_DRAFTINFO.
        """
        # TODO: Automatically detect if it's a draft or not?
        # TODO Handle this better?
        self._parent = parent
        self._account = self._parent._account

        self.author = msgData[MI_AUTHORFIRSTNAME]
        self.id = msgData[MI_MSGID]
        self.number = msgData[MI_NUM]
        self.subject = msgData[MI_SUBJECT]
        self.to = msgData[MI_TO]
        self.cc = msgData[MI_CC]
        self.bcc = msgData[MI_BCC]
        self.sender = msgData[MI_AUTHOREMAIL]

        self.attachments = [GmailAttachment(self, attachmentInfo)
                            for attachmentInfo in msgData[MI_ATTACHINFO-1]]

        # TODO: Populate additional fields & cache...(?)

        # TODO: Handle body differently if it's from a draft?
        self.isDraft = isDraft

        self._source = None


    def _getSource(self):
        """
        """
        if not self._source:
            # TODO: Do this more nicely...?
            # TODO: Strip initial white space & fix up last line ending
            #       to make it legal as per RFC?
            self._source = self._account.getRawMessage(self.id)

        return self._source

    source = property(_getSource, doc = "")



class GmailAttachment:
    """
    """

    def __init__(self, parent, attachmentInfo):
        """
        """
        # TODO Handle this better?
        self._parent = parent
        self._account = self._parent._account

        self.id = attachmentInfo[A_ID]
        self.filename = attachmentInfo[A_FILENAME]
        self.mimetype = attachmentInfo[A_MIMETYPE]
        self.filesize = attachmentInfo[A_FILESIZE]

        self._content = None


    def _getContent(self):
        """
        """
        if not self._content:
            # TODO: Do this a more nicely...?
            self._content = self._account._retrievePage(
                _buildURL(view=U_ATTACHMENT_VIEW, disp="attd",
                          attid=self.id, th=self._parent._parent.id))

        return self._content

    content = property(_getContent, doc = "")


    def _getFullId(self):
        """

        Returns the "full path"/"full id" of the attachment. (Used
        to refer to the file when forwarding.)

        The id is of the form: "<thread_id>_<msg_id>_<attachment_id>"

        """
        return "%s_%s_%s" % (self._parent._parent.id,
                             self._parent.id,
                             self.id)

    _fullId = property(_getFullId, doc = "")



class GmailComposedMessage:
    """
    """

    def __init__(self, to, subject, body, cc = None, bcc = None,
                 filenames = None, files = None):
        """

          `filenames` - list of the file paths of the files to attach.
          `files` - list of objects implementing sub-set of
                    `email.Message.Message` interface (`get_filename`,
                    `get_content_type`, `get_payload`). This is to
                    allow use of payloads from Message instances.
                    TODO: Change this to be simpler class we define ourselves?
        """
        self.to = to
        self.subject = subject
        self.body = body
        self.cc = cc
        self.bcc = bcc
        self.filenames = filenames
        self.files = files



if __name__ == "__main__":
    import sys
    from getpass import getpass

    try:
        name = sys.argv[1]
    except IndexError:
        name = raw_input("Gmail account name: ")

    pw = getpass("Password: ")
    domain = raw_input("Domain? [leave blank for Gmail]: ")

    ga = GmailAccount(name, pw, domain=domain)

    print "\nPlease wait, logging in..."

    try:
        ga.login()
    except GmailLoginFailure,e:
        print "\nLogin failed. (%s)" % e.message
    else:
        print "Login successful.\n"

        # TODO: Use properties instead?
        quotaInfo = ga.getQuotaInfo()
        quotaMbUsed = quotaInfo[QU_SPACEUSED]
        quotaMbTotal = quotaInfo[QU_QUOTA]
        quotaPercent = quotaInfo[QU_PERCENT]
        print "%s of %s used. (%s)\n" % (quotaMbUsed, quotaMbTotal, quotaPercent)

        searches = STANDARD_FOLDERS + ga.getLabelNames()
        name = None
        while 1:
            try:
                print "Select folder or label to list: (Ctrl-C to exit)"
                for optionId, optionName in enumerate(searches):
                    print "  %d. %s" % (optionId, optionName)
                while not name:
                    try:
                        name = searches[int(raw_input("Choice: "))]
                    except ValueError,info:
                        print info
                        name = None
                if name in STANDARD_FOLDERS:
                    result = ga.getMessagesByFolder(name, True)
                else:
                    result = ga.getMessagesByLabel(name, True)

                if not len(result):
                    print "No threads found in `%s`." % name
                    break
                name = None
                tot = len(result)

                i = 0
                for thread in result:
                    print "%s messages in thread" % len(thread)
                    print thread.id, len(thread), thread.subject
                    for msg in thread:
                        print "\n ", msg.id, msg.number, msg.author,msg.subject
                        # Just as an example of other usefull things
                        #print " ", msg.cc, msg.bcc,msg.sender
                        i += 1
                print
                print "number of threads:",tot
                print "number of messages:",i
            except KeyboardInterrupt:
                break

    print "\n\nDone."

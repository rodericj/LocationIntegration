#!/usr/bin/env python
#
# Copyright 2008-2009 TripIt, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
  Methods to interact with the TripIt v1 API
"""

import base64
import datetime
import hmac
import md5
import random
import re
import sys
import time
import urllib
import urllib2

import xml.sax

from xml.sax import make_parser

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

VERSION='$Id: tripit.py 17689 2009-07-29 23:26:38Z denmark $'

class WebAuthCredential():
    def __init__(self, username, password):
        self._username = username
        self._password = password

    def getUsername(self):
        return self._username

    def getPassword(self):
        return self._password

# } class:WebAuthCredential

class OAuthConsumerCredential():
    def __init__(self, oauth_consumer_key, oauth_consumer_secret, oauth_token='', oauth_token_secret=''):
        self._oauth_consumer_key    = oauth_consumer_key
        self._oauth_consumer_secret = oauth_consumer_secret
        self._oauth_oauth_token     = oauth_token
        self._oauth_token_secret    = oauth_token_secret

    def getOAuthConsumerKey(self):
        return self._oauth_consumer_key
    
    def getOAuthConsumerSecret(self):
        return self._oauth_consumer_secret

    def getOAuthToken(self):
        return self._oauth_oauth_token

    def getOAuthTokenSecret(self):
        return self._oauth_token_secret

# } class:OAuthConsumerCredential

class OAuthConsumer():
    def __init__(self, oauth_consumer_credentials):
        self._oauth_signature_method     = 'HMAC-SHA1'
        self._oauth_version              = '1.0'
        self._oauth_parameters           = {}
        self._oauth_consumer_credentials = oauth_consumer_credentials

    def _escape(self, s):
        return urllib.quote(s, safe='~')

    def _generate_nonce(self):
        random_number = ''.join(str(random.randint(0, 9)) for i in range(40))
        m = md5.new(str(time.time()) + str(random_number))
        return m.hexdigest()

    def generate_oauth_parameters(self, http_method, base_url, url_args=None, post_args=None):
        normalized_http_method = http_method.upper()

        normalized_http_url = self._escape(base_url)

        self._oauth_parameters = {
            'oauth_consumer_key'     : self._oauth_consumer_credentials.getOAuthConsumerKey(),
            'oauth_nonce'            : self._generate_nonce(),
            'oauth_timestamp'        : str(int(time.time())),
            'oauth_signature_method' : self._oauth_signature_method,
            'oauth_version'          : self._oauth_version
            }
        if self._oauth_consumer_credentials.getOAuthToken() != '':
            self._oauth_parameters['oauth_token'] = self._oauth_consumer_credentials.getOAuthToken()

        if self._oauth_consumer_credentials.getOAuthTokenSecret() != '':
            self._oauth_parameters['oauth_token_secret'] = self._oauth_consumer_credentials.getOAuthTokenSecret()

        parameters = self._oauth_parameters

        if url_args is not None:
            parameters.update(url_args)

        if post_args is not None:
            parameters.update(post_args)

        normalized_parameters = self._escape('&'.join(['%s=%s' % (self._escape(str(k)), self._escape(str(parameters[k]))) for k in sorted(parameters)]))

        signature_base_string = '&'.join([normalized_http_method, normalized_http_url, normalized_parameters])

        key = self._oauth_consumer_credentials.getOAuthConsumerSecret() + '&' + self._oauth_consumer_credentials.getOAuthTokenSecret()

        try:
            import hashlib
            hashed = hmac.new(key, signature_base_string, hashlib.sha1)
        except:
            import sha
            hashed = hmac.new(key, signature_base_string, sha)

        self._oauth_parameters['oauth_signature'] = base64.b64encode(hashed.digest())

        return self._oauth_parameters

    def generate_authorization_header(self, realm=None):
        authorization_header = 'OAuth'

        if realm is not None:
            authorization_header += ' realm="%s",' % (realm)

        authorization_header += ','.join(['%s="%s"' % (self._escape(k), self._escape(self._oauth_parameters[k])) for k in self._oauth_parameters])
        return authorization_header

# } class:OAuthConsumer

class ResponseHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self._element_stack = []
        self._current_content = None
        self._root_obj = None

    def get_response_obj(self):
        return self._root_obj

    def startElement(self, name, attrs):
        if re.match('[A-Z]', name):
            type_name = str(name)
            data_node = TravelObj(type_name, (), { '_attributes' : { }, '_children' : [] })
            if len(self._element_stack) > 0:
                self._element_stack[-1].add_child(data_node)
            self._element_stack.append(data_node)
            if self._root_obj is None:
                self._root_obj = self._element_stack[0]

    def endElement(self, name):
        if self._current_content is not None:
            if name.endswith('date'):
                self._current_content = datetime.date(*(time.strptime(self._current_content, '%Y-%m-%d')[0:3]))
            elif name.endswith('time'):
                self._current_content = datetime.time(*(time.strptime(self._current_content, '%H:%M:%S')[3:6]))

            self._element_stack[-1]._attributes.update({ name : self._current_content })
            self._current_content = None

        if re.match('[A-Z]', name):
            self._element_stack.pop()

    def characters(self, content):
        if self._current_content is not None:
            self._current_content = '%s%s' % (self._current_content, content)
        else:
            self._current_content = content

# } class:ResponseHandler

class TravelObj(type):
    def __new__(cls, name, bases, dict):
        return type.__new__(cls, name, bases, dict)

    def __init__(cls, name, bases, dict):
        super(TravelObj, cls).__init__(name, bases, dict)

    def __getattr__(cls, name):
        return cls.get_attribute_value(name)

    def __cmp__(cls, other):
        # start_date
        try:
            if cls.start_date and other.start_date:
                return cmp(cls.start_date, other.start_date)
        except AttributeError:
            pass

        # StartDateTime or DateTime
        try:
            cls_start_datetime_obj = None
            other_start_datetime_obj = None
            for child in cls.get_children():
                if child.__name__ == 'StartDateTime' or child.__name__ == 'DateTime':
                    cls_start_datetime_obj = datetime.datetime.combine(child.date, child.time)
                    break

            for child in other.get_children():
                if child.__name__ == 'StartDateTime' or child.__name__ == 'DateTime':
                    other_start_datetime_obj = datetime.datetime.combine(child.date, child.time)
                    break
            return cmp(cls_start_datetime_obj, other_start_datetime_obj)
        except:
            pass

    def add_child(cls, child):
        cls._children.append(child)

    def get_attribute_names(cls):
        return cls._attributes.keys()

    def get_attribute_value(cls, name):
        if name in cls._attributes:
            return cls._attributes[name]
        else:
            raise AttributeError("'TravelObj' has no attribute '%s'" % name)

    def get_children(cls):
        return cls._children

    def has_error(self):
        for o in self._children:
            if o.__name__ == 'Error':
                return True
        return False

    def has_warning(self):
        for o in self._children:
            if o.__name__ == 'Warning':
                return True
        return False

# } class:TripItData

class TripIt(object):
    def __init__(self, webauth_credentials=None, oauth_credentials=None, api_url=None):
        self._api_url             = api_url or 'https://api.tripit.com'
        self._api_version         = 'v1'
        self._webauth_credentials = webauth_credentials
        self._oauth_credentials   = oauth_credentials

        self.resource  = None
        self.response  = None
        self.http_code = None

    def _do_request(self, verb, entity=None, url_args=None, post_args=None):
        """
        Makes a request POST/GET to the API and returns the response
          from the server.
        """
        if verb in ['/oauth/request_token', '/oauth/access_token']:
            base_url = self._api_url + verb
        else:
            if entity is not None:
                base_url = '/'.join([self._api_url, self._api_version, verb, entity])
            else:
                base_url = '/'.join([self._api_url, self._api_version, verb])

        if url_args is not None:
            url = base_url + '?' + urllib.urlencode(url_args)
        else:
            url = base_url

        self.resource = url

        if post_args is not None:
            request = urllib2.Request(url, urllib.urlencode(post_args))
        else:
            request = urllib2.Request(url)

        if self._oauth_credentials is not None:
            oauth_consumer = OAuthConsumer(self._oauth_credentials)
            if post_args is not None:
                http_method = 'POST'
            else:
                http_method = 'GET'

            oauth_parameters = oauth_consumer.generate_oauth_parameters(http_method, base_url, url_args, post_args)
            
            authorization_header = oauth_consumer.generate_authorization_header(self._api_url)

            request.add_header('Authorization', authorization_header)
        elif self._webauth_credentials is not None:
            pair = "%s:%s" % (self._webauth_credentials.getUsername(), self._webauth_credentials.getPassword())
            token = base64.b64encode(pair)
            request.add_header('Authorization', 'Basic %s' % token)
        else:
            raise Exception('Unable to authenticate request, no credentials provided')

        stream = None
        try:
            stream = urllib2.urlopen(request)
            self.http_code = 200
        except urllib2.HTTPError, http_error:
            self.http_code = http_error.code
            stream = http_error

        data = stream.read()
        stream.close()
        self.response = data
        return data

    def _parse_command(self, command, params=None, post_args=None):
        try:
            (verb, entity) = command.split('_')
        except ValueError:
            verb = command
            entity = None

        response_data = self._do_request(verb, entity, params, post_args)
        return self.xml_to_py(response_data)

    def _parse_qs(self, qs):
        request_params = {}

        for param in qs.split('&'):
            (request_param, request_param_value) = param.split('=')
            request_params[request_param] = request_param_value

        return request_params

    def xml_to_py(self, data):
        self._parser = xml.sax.make_parser()
        handler = ResponseHandler()
        self._parser.setContentHandler(handler)
        self._parser.parse(StringIO(data))
        return handler.get_response_obj()

    def get_trip(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def get_air(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def get_lodging(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def get_car(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def get_profile(self):
        return self._parse_command(sys._getframe().f_code.co_name)

    def get_rail(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def get_transport(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def get_cruise(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def get_restaurant(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def get_activity(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def get_note(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def get_map(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def get_directions(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def delete_trip(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def delete_air(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def delete_lodging(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def delete_car(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def delete_rail(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def delete_transport(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def delete_cruise(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def delete_restaurant(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def delete_activity(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def delete_note(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def delete_map(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def delete_directions(self, id):
        return self._parse_command(sys._getframe().f_code.co_name, { 'id' : id })

    def list_trip(self, filter=None):
        return self._parse_command(sys._getframe().f_code.co_name, filter)

    def list_object(self, filter=None):
        return self._parse_command(sys._getframe().f_code.co_name, filter)

    def create(self, xml):
        return self._parse_command(sys._getframe().f_code.co_name, None, { 'xml' : xml })

    def get_request_token(self):
        response = self._do_request('/oauth/request_token')

        if self.http_code == 200:
            return self._parse_qs(response)
        else:
            return response

    def get_access_token(self):
        response = self._do_request('/oauth/access_token')

        if self.http_code == 200:
            return self._parse_qs(response)
        else:
            return response

# } class:TripIt

## EXAMPLE CODE

def _recurse_children(obj):
    children = obj.get_children()

    if children == []:
        return

    for child in children:
        print "child: ", child
        print "child attribute names: ", child.get_attribute_names()
        for attr in child.get_attribute_names():
            print "attrs: %s => %s" % (attr, child.get_attribute_value(attr))
        _recurse_children(child)

def _run_example(argv):
    """
    Pass in your username and password on the command line like so:

      python tripit.py <oauth_consumer_key> <oauth_consumer_secret> <oauth_access_token> <oauth_access_token_secret>

    """
    if len(argv) < 4:
        print "python tripit.py <oauth_consumer_key> <oauth_consumer_secret> <oauth_access_token> <oauth_access_token_secret>"
        return 1

    oauth_consumer_key = argv[0]
    oauth_consumer_secret = argv[1]
    oauth_access_token = argv[2]
    oauth_access_token_secret = argv[3]

    oauth_credential = OAuthConsumerCredential(oauth_consumer_key=oauth_consumer_key, oauth_consumer_secret=oauth_consumer_secret, oauth_token=oauth_access_token, oauth_token_secret=oauth_access_token_secret)
    oauth_consumer = OAuthConsumer(oauth_credential)

    t = TripIt(oauth_credentials=oauth_credential)
    print "Get my list of upcoming trips: "
    response = t.list_trip()
    _recurse_children(response)

    print "Get my list of travel objects in upcoming trips: "
    response = t.list_trip()
    _recurse_children(response)

    print "Create a new trip to New York: "
    xml="<Request><Trip><start_date>2009-12-17</start_date><end_date>2009-12-27</end_date><display_name>Test: New York, NY, December 2009</display_name><is_private>true</is_private><is_traveler>true</is_traveler><primary_location>New York, NY</primary_location></Trip></Request>"
    response = t.create(xml=xml)
    return

if __name__ == "__main__":
    sys.exit(_run_example(sys.argv[1:]))

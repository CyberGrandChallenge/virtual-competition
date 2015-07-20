#!/usr/bin/python

"""
CGC - Team Interface Library

Copyright (C) 2015 - Brian Caswell <bmc@lungetech.com>
Copyright (C) 2015 - Tim <tim@0x90labs.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


import binascii
import hashlib
import httplib
import json
import logging
import os
import socket
import operator


class TiError(Exception):
    pass


class TiClient(object):
    """
    Very basic example client demonstrating the CGC Team Interface
    """

    good_http = [200, 301]

    def __init__(self, ti_server, ti_port, user, password):
        self.ti_server = ti_server
        self.ti_port = ti_port
        self.user = user
        self.password = password

    def getTeams(self):
        """ get list of teams"""
        status = self.getStatus()

        ret = []
        for team_t in status['scores']:
            ret.append(team_t['team'])

        ret.sort()
        return ret

    def getRound(self):
        """ get the current round """

        status = self.getStatus()
        return status['round']

    def getCounts(self):
        """ get dict of counts """
        ret = {}

        status = self.getStatus()

        ret['team'] = len(status['scores'])
        ret['round'] = status['round']

        pov_feedback = self.getFeedback('pov', status['round'])
        ret['pov'] = len(pov_feedback)

        poll_feedback = self.getFeedback('poll', status['round'])
        ret['poll'] = len(poll_feedback)

        cb_feedback = self.getFeedback('cb', status['round'])
        ret['cb'] = len(cb_feedback)

        return ret

    def validate_round(self, round_id):
        try:
            round_id = int(round_id)
        except ValueError:
            raise TiError('invalid round')

        if round_id < 0 or round_id > self.getRound():
            raise TiError('invalid round')

        return round_id

    def getEvaluation(self, type_id, round_id, team):
        """ get feedback dict for type (cb,pov,poll) """

        if type_id not in ['cb', 'ids']:
            raise TiError('invalid evaluation type: %s' % type_id)

        round_id = self.validate_round(round_id)

        uri = "/round/%d/evaluation/%s/%s" % (round_id, type_id, team)
        status, reason, body = self._make_request(uri)
 
        try:
            data = json.loads(body)
        except ValueError:
            raise TiError('unable to parse server response')

        return data[type_id]

    def getFeedback(self, feedback_type, round_id):
        """ get feedback dict for type (cb,pov,poll) """
        
        round_id = self.validate_round(round_id)
        if feedback_type not in ['pov', 'cb', 'poll']:
            raise TiError('invalid feedback type: %s' % feedback_type)

        uri = "/round/%d/feedback/%s" % (round_id, feedback_type)

        status, reason, body = self._make_request(uri)

        try:
            data = json.loads(body)
        except ValueError:
            raise TiError('unable to parse server response')
        
        return data[feedback_type]

    def getScores(self, byscore=True):
        """ get list of scores """
        status = self.getStatus()
        data = {}

        for team in status['scores']:
            data[team['team']] = team['score']

        if byscore:
            ret = sorted(data.items(), key=operator.itemgetter(1), reverse=True)
        else:
            ret = sorted(data.items(), key=operator.itemgetter(0))

        return ret

    def _make_request(self, uri, fields=None, files=None):
        """
        issues HTTP POST as multipart form data
        uri -- the uri location for POST
        fields -- sequence of (name,value) to encode into the form
        files -- sequence of (name,filename,filedata) into the form
        """

        if fields is None:
            method = 'GET'
            content_type = None
            sendbody = None
            headers = {}
        else:
            method = 'POST'
            content_type, sendbody = self._get_multipart_formdata(fields, files)
            headers = {'User-Agent': 'ti-client', 'Content-Type': content_type}

        try:
            conn = httplib.HTTPConnection(self.ti_server, self.ti_port)
            conn.request(method, uri)
            rsp = conn.getresponse()
        except socket.error as err:
            print repr(err)
            raise TiError('unable to connect to server: %s:%s' % (self.ti_server, self.ti_port))

        logging.debug("%s - %s", rsp.status, rsp.reason)
        if rsp.status != 401:
            raise TiError('server did not return digest auth information')

        rsp.read()  # ugh

        parts = self._www_auth_parts(rsp.getheader('www-authenticate'))

        authorization = {}
        if 'algorithm' in parts and parts['algorithm'].lower() != 'md5':
            raise TiError('unsupported digest algorithm')

        for field in ['realm', 'nonce', 'qop']:
            authorization[field] = parts[field]
      
        # optional parts that should be copied
        for field in ['opaque']:
            if field in parts:
                authorization[field] = parts[field]

        authorization['username'] = self.user
        authorization['uri'] = uri
        authorization['nc'] = "00000001"
        authorization['cnonce'] = self._rand_str(4)
        
        authorization['response'] = self._gen_response(authorization, method)

        auth_string = "Digest " + ', '.join(['%s="%s"' % (k, v) for k, v in authorization.iteritems()])

        logging.debug("# %s #", auth_string)

        headers = {'User-Agent': 'ti-client', 'Content-Type': content_type,
                   'Authorization': '%s' % (auth_string)}

        try:
            conn.request(method, uri, sendbody, headers)
            rsp = conn.getresponse()
            data = rsp.read()
        except socket.error as err:
            raise TiError('unable to make request')
        except httplib.BadStatusLine:
            raise TiError('unknown error from server')

        logging.debug("%s - %s", rsp.status, rsp.reason)

        conn.close()

        return rsp.status, rsp.reason, data

    def _get_multipart_formdata(self, fields, files):
        BOUNDARY = '------------------%s-cgc' % self._rand_str(8)
        builder = []
        for (name, value) in fields:
            builder.append('--' + BOUNDARY)
            builder.append('Content-Disposition: form-data; name="%s"' % name)
            builder.append('')
            builder.append(value)
        for (name, filename, value) in files:
            builder.append('--' + BOUNDARY)
            builder.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (name, filename))
            builder.append('Content-Type: application/octet-stream')
            builder.append('')
            builder.append(value)
        builder.append('--' + BOUNDARY + '--')
        builder.append('')
        body = '\r\n'.join(builder)

        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY

        logging.debug("type:%s, bodysize:%d", content_type, len(body))

        return content_type, body

    def uploadRCB(self, csid, files):
        """
        issues HTTP POST of a CS (single or multi-CB)
        csid -- CSID for the CS
        files -- sequence of (CBID,filename) where filename is on the local filesystem
        """

        uri = "/rcb"

        fields = [("csid", csid)]
        uploads = []
       
        expected = {}

        for cbid, filename in files:
            try:
                with open(filename, 'rb') as f:
                    filedata = f.read()
            except IOError:
                raise TiError('unable to open file: %s' % filename)

            uploads.append((cbid, os.path.basename(filename), filedata))
            expected[cbid] = hashlib.sha256(filedata).hexdigest()

        status, reason, body = self._make_request('/rcb', fields, uploads)
        
        try:
            response = json.loads(body)
        except ValueError:
            raise TiError('unable to parse response from server')

        if status != 200:
            raise TiError(', '.join(response['error']))

        if len(expected.keys()) != len(response['files']):
            print repr(response['files'])
            raise TiError('uploaded %d files, only %d processed' % (len(expected.keys()), len(response['files'])))

        for entry in response['files']:
            if entry['file'] not in expected:
                raise TiError('invalid file upload: %s' % entry['file'])

            if entry['hash'] != expected[entry['file']]:
                raise TiError('upload corrupted.  Expected: %s Got: %s' % (expected[entry['file']], entry['hash']))
       
        return response['round']

    def uploadIDS(self, csid, filename):
        fields = [("csid", csid)]
        uploads = []

        if not os.path.isfile(filename):
            raise TiError('invalid filename: %s' % filename)

        with open(filename, 'rb') as f:
            filedata = f.read()
            uploads.append(('file', os.path.basename(filename), filedata))
        
        status, reason, body = self._make_request('/ids', fields, uploads)
        
        expected = hashlib.sha256(filedata).hexdigest()
        
        try:
            response = json.loads(body)
        except ValueError:
            raise TiError('unable to parse response from server')
        
        if status == 200:
            if expected != response['hash']:
                raise TiError('uploaded hash does not match.  '
                              'Expected: %s Got: %s' % (expected,
                              response['hash']))
        else:
            raise TiError(', '.join(response['error']))
        
        return response['round']

    def uploadPOV(self, csid, team, throws, filename):
        fields = [("csid", csid), ('team', team), ('throws', throws)]
        uploads = []

        if not os.path.isfile(filename):
            raise TiError('invalid filename: %s' % filename)

        with open(filename, 'rb') as f:
            filedata = f.read()
            uploads.append(('file', os.path.basename(filename), filedata))
        
        status, reason, body = self._make_request('/pov', fields, uploads)
        
        expected = hashlib.sha256(filedata).hexdigest()
        
        try:
            response = json.loads(body)
        except ValueError:
            raise TiError('unable to parse response from server')
        
        if status == 200:
            if expected != response['hash']:
                raise TiError('uploaded hash does not match.  '
                              'Expected: %s Got: %s' % (expected,
                              response['hash']))
        else:
            raise TiError(', '.join(response['error']))
        
        return response['round']

    def getConsensus(self, csid, data_type, team, round_id, output_dir):
        if not os.path.isdir(output_dir):
            raise TiError('output directory is not a directory')

        types = ['cb', 'ids']
        if data_type not in types:
            raise TiError('invalid consensus type')

        response = self.getEvaluation(data_type, round_id, team)

        paths = []

        for entry in response:
            if csid != entry['csid']:
                continue
            if data_type == 'cb':
                paths.append((entry['cbid'], entry['uri'], entry['hash']))
            else:
                paths.append((csid, entry['uri'], entry['hash']))

        if not len(paths):
            raise TiError('invalid csid')

        files = []

        for entry in paths:
            cbid, uri, checksum = entry
            filename = '%s-%s-%s.%s' % (cbid, team, round_id, data_type)
            path = os.path.join(output_dir, filename)
            self._get_dl(uri, path, checksum)
            files.append(path)

        files.sort()

        return files

    def _get_dl(self, dlpath, filename, expected_checksum):
        """
        issues HTTP GET to retreive an eval item for a team
        dlpath - the uri for the file to download (e.g. /dl/2/cb/...)
        """

        assert dlpath.startswith("/dl/"), "bad download path"
        
        status, reason, body = self._make_request(dlpath)
                
        checksum = hashlib.sha256(body).hexdigest()

        if expected_checksum != checksum:
            raise TiError('invalid download checksum.  Expected: %s Got: %s' % (expected_checksum, checksum))

        try:
            with open(filename, "wb") as w:
                w.write(body)
        except IOError as err:
            raise TiError('unable to write downloaded file')

    def getStatus(self):
        """
        issues HTTP GET to retreive CGC CFE status (teams, scores, current round id)
        """

        uri = "/status"

        status, reason, body = self._make_request(uri)

        try:
            status = json.loads(body)
        except ValueError:
            raise TiError('unable to parse server response')

        return status

    def _www_auth_parts(self, www_auth):
        """
        splits apart the www-authenticate parts for digest auth
        www_auth -- the www-authentication string to split
        """
        header = 'Digest '
        if not www_auth.startswith(header):
            raise TiError('invalid authentication response from server')

        www_auth = www_auth[len(header):]
        results = {}
        for item in www_auth.split(','):
            key, value = item.split('=')
            key = key.strip()
            value = value.strip('"')
            results[key] = value 

        return results

    def _rand_str(self, string_len):
        """
        returns string of random bytes
        n -- number of bytes
        """
        return binascii.hexlify(os.urandom(string_len))

    def _gen_response(self, auth_d, method):
        """
        calculates HTTP digest auth respose
        auth_d -- dictionary of auth components required for response generation
        method -- the HTTP method (one of GET, POST)
        """
        ha1 = hashlib.md5("%s:%s:%s" % (auth_d['username'],
                                        auth_d['realm'],
                                        self.password)).hexdigest()

        ha2 = hashlib.md5("%s:%s" % (method, auth_d['uri'])).hexdigest()

        return hashlib.md5("%s:%s:%s:%s:%s:%s" % (ha1, auth_d['nonce'], auth_d['nc'],
                                                  auth_d['cnonce'],
                                                  auth_d['qop'],
                                                  ha2)).hexdigest()

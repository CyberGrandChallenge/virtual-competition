#!/usr/bin/python

import json
import random
import shutil
import hashlib
import os
import sys
import unittest
import time
import tempfile
import subprocess

sys.path.append('tests')
import base_vc_test

class VirtualCompetition(base_vc_test.VirtualCompetitionBase, unittest.TestCase):
    maxDiff = None

    def _test_get_url(self, auth, url):
        """ tests URLs are avaialble and return JSON """
        cmd = ['/usr/bin/curl', '-f', '--digest', '-u', auth, 'http://localhost:%d%s' % (self.port, url)]
        print ' '.join(cmd)
        result = subprocess.check_output(cmd)
        return result
         
    def test_curl_status(self):
        """ tests /status is accessible (and auth) on default user/pass and port"""
        result = self._test_get_url('vagrant:vagrant', '/status')

        status = json.loads(result)
        status_keys = status.keys()
        status_keys.sort()
        self.assertEqual(['round', 'scores'], status_keys)
        self.assertIsInstance(status['round'], int)

        for score in status['scores']:
            score_keys = score.keys()
            score_keys.sort()
            self.assertEqual(['rank', 'score', 'team'], score_keys)
            self.assertIsInstance(score['rank'], int)
            self.assertIsInstance(score['score'], int)

    def test_curl_feedback_cb(self):
        result = self._test_get_url('vagrant:vagrant', '/round/1/feedback/cb')

        status = json.loads(result)
        self.assertEqual(['cb'], status.keys())
        self.assertIsInstance(status['cb'], list)

        for cb in status['cb']:
            cb_keys = cb.keys()
            cb_keys.sort()
            self.assertEqual(cb_keys, ['cbid', 'signal', 'timestamp'])
            self.assertIsInstance(cb['cbid'], unicode)
            self.assertIsInstance(cb['signal'], int)
            self.assertIsInstance(cb['timestamp'], int)

    def test_curl_feedback_poll(self):
        result = self._test_get_url('vagrant:vagrant', '/round/1/feedback/poll')

        status = json.loads(result)
        self.assertEqual(['poll'], status.keys())
        self.assertIsInstance(status['poll'], list)

        for cb in status['poll']:
            cb_keys = cb.keys()
            cb_keys.sort()
            self.assertEqual(cb_keys, ['csid', 'functionality', 'performance'])

            self.assertIsInstance(cb['performance'], dict)
            self.assertIsInstance(cb['functionality'], dict)
            self.assertIsInstance(cb['csid'], unicode)

            performance_keys = cb['performance'].keys()
            performance_keys.sort()
            self.assertEqual(performance_keys, ['memory', 'time'])

            self.assertIsInstance(cb['performance']['memory'], int)
            self.assertIsInstance(cb['performance']['time'], int)
            
            functionality_keys = cb['functionality'].keys()
            functionality_keys.sort()
            self.assertEqual(functionality_keys, ['connect', 'success', 'timeout'])

            self.assertIsInstance(cb['functionality']['connect'], int)
            self.assertIsInstance(cb['functionality']['success'], int)
            self.assertIsInstance(cb['functionality']['timeout'], int)

    def test_curl_feedback_pov(self):
        result = self._test_get_url('vagrant:vagrant', '/round/1/feedback/pov')

        status = json.loads(result)
        self.assertEqual(['pov'], status.keys())
        self.assertIsInstance(status['pov'], list)
       
        # ... would be nice if we had a way to test these
        # self.assertGreater(len(status['pov']), 0)

        for pov in status['pov']:
            pov_keys = pov.keys()
            pov_keys.sort()

            # {"csid":"CSID","team":"TEAMID","throw":"NN","result":"RESULT"},
            self.assertEqual(pov_keys, ['csid', 'team', 'throw', 'result'])
            
            self.assertIn(pov['result'], ['success', 'fail'])
            self.assertIsInstance(pov['csid'], unicode)
            self.assertIsInstance(pov['team'], int)
            self.assertIsInstance(pov['throw'], int)

    def test_curl_evaluation_ids(self):
        result = self._test_get_url('vagrant:vagrant', '/round/1/evaluation/ids/1')

        status = json.loads(result)
        self.assertEqual(['ids'], status.keys())
        self.assertIsInstance(status['ids'], list)
        
        self.assertGreater(len(status['ids']), 0)

        for ids in status['ids']:
            ids_keys = ids.keys()
            ids_keys.sort()

            self.assertEqual(ids_keys, ['csid', 'hash', 'uri'])

            self.assertIsInstance(ids['csid'], unicode)
            self.assertIsInstance(ids['hash'], unicode)
            self.assertEqual(len(ids['hash']), 64)
            
            self.assertIsInstance(ids['uri'], unicode)
            self.assertRegexpMatches(ids['uri'], r'^\/.*ids')

    def test_curl_evaluation_cb(self):
        result = self._test_get_url('vagrant:vagrant', '/round/1/evaluation/cb/1')

        status = json.loads(result)
        self.assertEqual(['cb'], status.keys())
        self.assertIsInstance(status['cb'], list)

        self.assertGreater(len(status['cb']), 0)

        for cb in status['cb']:
            cb_keys = cb.keys()
            cb_keys.sort()

            self.assertEqual(cb_keys, ['cbid', 'csid', 'hash', 'uri'])

            self.assertIsInstance(cb['cbid'], unicode)
            self.assertIsInstance(cb['csid'], unicode)
            self.assertIsInstance(cb['hash'], unicode)
            self.assertEqual(len(cb['hash']), 64)
            
            self.assertIsInstance(cb['uri'], unicode)
            self.assertRegexpMatches(cb['uri'], r'^\/.*')

    def _test_upload(self, auth, url, **fields):
        """ tests URLs are avaialble and return JSON """
        args = []
        for key in fields:
            if key == 'fail':
                continue
            args.append('-F')
            args.append('%s=%s' % (key, fields[key]))

        if 'fail' in fields and fields['fail'] == True:
            args.append('-f')
       
        cmd = ['/usr/bin/curl', '--digest', '-u', auth] + args + ['http://localhost:%d%s' % (self.port, url)]
        print ' '.join(cmd)
        result = subprocess.check_output(cmd)
        return json.loads(result)

    def test_curl_upload_ids(self):
        path = os.path.join(self.cbdir, 'CADET_00003', 'ids', 'CADET_00003.rules')

        checksum = unicode(self.checksum(path))
        response = self._test_upload('vagrant:vagrant', '/ids', file='@%s' % path, csid='CADET_00003')
        expected = {'hash': checksum, 'round': 1, 'file': 'CADET_00003.rules'}
        self.assertEqual(response, expected)

    def test_curl_upload_ids_bad(self):
        # invalid file
        path = '/etc/hosts'  # a file that we know isn't an IDS file
        checksum = unicode(self.checksum(path))
        response = self._test_upload('vagrant:vagrant', '/ids', file='@%s' % path, fail=False, csid='CADET_00003')
        expected = {'hash': checksum, 'file': 'hosts', 'error': ['invalid format']}
        self.assertEqual(response, expected)

        # invalid CSID
        path = os.path.join(self.cbdir, 'CADET_00003', 'ids', 'CADET_00003.rules')
        checksum = unicode(self.checksum(path))
        response = self._test_upload('vagrant:vagrant', '/ids', file='@%s' % path, fail=False, csid='CADET_0003')
        expected = {'error': ['invalid csid'], 'hash': checksum, 'file': 'CADET_00003.rules'}
        self.assertEqual(response, expected)

        # no CSID
        path = os.path.join(self.cbdir, 'CADET_00003', 'ids', 'CADET_00003.rules')
        checksum = unicode(self.checksum(path))
        response = self._test_upload('vagrant:vagrant', '/ids', file='@%s' % path, fail=False)
        expected = {'error': ['invalid csid'], 'hash': checksum, 'file': 'CADET_00003.rules'}
        
        # no file
        response = self._test_upload('vagrant:vagrant', '/ids', fail=False, csid='CADET_00003')
        expected = {'error': ['malformed request']}
        self.assertEqual(response, expected)
    
    def test_curl_upload_cb(self):
        # single CB
        path = os.path.join(self.cbdir, 'CADET_00003', 'bin', 'CADET_00003_patched')
        checksum = unicode(self.checksum(path))
        response = self._test_upload('vagrant:vagrant', '/rcb', CADET_00003='@%s' % path, csid='CADET_00003')
        expected = {'files': [{'valid': 'yes', 'hash': checksum, 'file': 'CADET_00003'}], 'round': 1}
        self.assertEqual(response, expected)

        # multiple CB, only one
        path = os.path.join(self.cbdir, 'LUNGE_00005', 'bin', 'LUNGE_00005_1_patched')
        checksum = unicode(self.checksum(path))
        response = self._test_upload('vagrant:vagrant', '/rcb', LUNGE_00005_1='@%s' % path, csid='LUNGE_00005')
        expected = {'files': [{'valid': 'yes', 'hash': checksum, 'file': 'LUNGE_00005_1'}], 'round': 1}
        self.assertEqual(response, expected)

        # multiple CBs at once
        path_1 = os.path.join(self.cbdir, 'LUNGE_00005', 'bin', 'LUNGE_00005_1_patched')
        path_2 = os.path.join(self.cbdir, 'LUNGE_00005', 'bin', 'LUNGE_00005_2_patched')
        checksum_1 = unicode(self.checksum(path_1))
        checksum_2 = unicode(self.checksum(path_2))
        response = self._test_upload('vagrant:vagrant', '/rcb', LUNGE_00005_1='@%s' % path_1, LUNGE_00005_2='@%s' % path_2, csid='LUNGE_00005')

        expected = {'files': [
            {'valid': 'yes', 'hash': checksum_1, 'file': 'LUNGE_00005_1'}, 
            {'valid': 'yes', 'hash': checksum_2, 'file': 'LUNGE_00005_2'}], 
            'round': 1}
        self.assertEqual(response, expected)
    
    def test_curl_upload_cb_bad_args(self):
        # single CB - invalid csid
        path = os.path.join(self.cbdir, 'CADET_00003', 'bin', 'CADET_00003_patched')
        checksum = unicode(self.checksum(path))
        response = self._test_upload('vagrant:vagrant', '/rcb', CADET_0003='@%s' % path, csid='CADET_0003', fail=False)
        expected = {'files': [{'valid': 'yes', 'hash': checksum, 'file': 'CADET_0003'}], 'error': ['invalid csid']}
        self.assertEqual(response, expected)

        # single CB - invalid cbid
        path = os.path.join(self.cbdir, 'CADET_00003', 'bin', 'CADET_00003_patched')
        checksum = unicode(self.checksum(path))
        response = self._test_upload('vagrant:vagrant', '/rcb', CADET_00004='@%s' % path, csid='CADET_00003', fail=False)
        expected = {'files': [{'valid': 'yes', 'hash': checksum, 'file': 'CADET_00004'}], 'error': ['invalid cbid']}
        self.assertEqual(response, expected)

        # No CBs
        path = os.path.join(self.cbdir, 'CADET_00003', 'bin', 'CADET_00003_patched')
        checksum = unicode(self.checksum(path))
        response = self._test_upload('vagrant:vagrant', '/rcb', csid='CADET_00003', fail=False)
        expected = {'files': [], 'error': ['malformed request']}
        self.assertEqual(response, expected)

    def test_curl_upload_cb_bad_files(self):
        # single CB
        path = os.path.join('/etc/hosts')
        checksum = unicode(self.checksum(path))
        response = self._test_upload('vagrant:vagrant', '/rcb', CADET_00003='@%s' % path, csid='CADET_00003', fail=False)
        expected = {'files': [{'valid': 'no', 'hash': checksum, 'file': 'CADET_00003'}], 'error': ['invalid format']}
        self.assertEqual(response, expected)

        # multiple CB, only one
        response = self._test_upload('vagrant:vagrant', '/rcb', LUNGE_00005_1='@%s' % path, csid='LUNGE_00005')
        expected = {'files': [{'valid': 'no', 'hash': checksum, 'file': 'LUNGE_00005_1'}], 'error': ['invalid format']}
        self.assertEqual(response, expected)

         # multiple CBs at once, one good, one bad.
        path_1 = os.path.join(self.cbdir, 'LUNGE_00005', 'bin', 'LUNGE_00005_1_patched')
        path_2 = '/etc/hosts'
        checksum_1 = unicode(self.checksum(path_1))
        checksum_2 = unicode(self.checksum(path_2))
        response = self._test_upload('vagrant:vagrant', '/rcb', LUNGE_00005_1='@%s' % path_1, LUNGE_00005_2='@%s' % path_2, csid='LUNGE_00005')

        expected = {'files': [
            {'valid': 'yes', 'hash': checksum_1, 'file': 'LUNGE_00005_1'}, 
            {'valid': 'no', 'hash': checksum_2, 'file': 'LUNGE_00005_2'}], 
            'error': ['invalid format']}

        self.assertEqual(response, expected)

         # multiple CBs at once, both bad
        path_1 = '/etc/passwd'
        path_2 = '/etc/hosts'
        checksum_1 = unicode(self.checksum(path_1))
        checksum_2 = unicode(self.checksum(path_2))
        response = self._test_upload('vagrant:vagrant', '/rcb', LUNGE_00005_1='@%s' % path_1, LUNGE_00005_2='@%s' % path_2, csid='LUNGE_00005')

        expected = {'files': [
            {'valid': 'no', 'hash': checksum_1, 'file': 'LUNGE_00005_1'}, 
            {'valid': 'no', 'hash': checksum_2, 'file': 'LUNGE_00005_2'}], 
            'error': ['invalid format']}
        self.assertEqual(response, expected)

    def test_curl_upload_pov(self):
        # POVs are CBs for CFE, so... for now, just upload the patched CB as the POV

        path = os.path.join(self.cbdir, 'LUNGE_00005', 'bin', 'LUNGE_00005_1_patched')
        checksum = unicode(self.checksum(path))
        response = self._test_upload('vagrant:vagrant', '/pov', file='@%s' % path, csid='CADET_00003', team=2, throws=10)
        expected = {"hash": checksum, "round": 1, "file": "LUNGE_00005_1_patched"}
        self.assertEqual(response, expected)

    def test_curl_upload_pov_bad_args(self):
        # POVs are CBs for CFE, so... for now, just upload the patched CB as the POV
        path = os.path.join(self.cbdir, 'LUNGE_00005', 'bin', 'LUNGE_00005_1_patched')
        checksum = unicode(self.checksum(path))

        # team is too low
        response = self._test_upload('vagrant:vagrant', '/pov', file='@%s' % path, csid='CADET_00003', team=0, throws=10, fail=False)
        expected = {'hash': checksum, 'file': 'LUNGE_00005_1_patched', 'error': ['invalid team']}
        self.assertEqual(response, expected)

        # team is too high
        response = self._test_upload('vagrant:vagrant', '/pov', file='@%s' % path, csid='CADET_00003', team=100, throws=10, fail=False)
        expected = {'hash': checksum, 'file': 'LUNGE_00005_1_patched', 'error': ['invalid team']}
        self.assertEqual(response, expected)

        # can't throw against ourselves
        response = self._test_upload('vagrant:vagrant', '/pov', file='@%s' % path, csid='CADET_00003', team=1, throws=10, fail=False)
        expected = {'hash': checksum, 'file': 'LUNGE_00005_1_patched', 'error': ['invalid team']}
        self.assertEqual(response, expected)

        # too many throws
        response = self._test_upload('vagrant:vagrant', '/pov', file='@%s' % path, csid='CADET_00003', team=2, throws=15, fail=False)
        expected = {'hash': checksum, 'file': 'LUNGE_00005_1_patched', 'error': ['invalid throws']}
        self.assertEqual(response, expected)

        # too few throws
        response = self._test_upload('vagrant:vagrant', '/pov', file='@%s' % path, csid='CADET_00003', team=2, throws=-1, fail=False)
        expected = {'hash': checksum, 'file': 'LUNGE_00005_1_patched', 'error': ['invalid throws']}
        self.assertEqual(response, expected)

        # no throws
        response = self._test_upload('vagrant:vagrant', '/pov', file='@%s' % path, csid='CADET_00003', team=2, fail=False)
        expected = {'hash': checksum, 'file': 'LUNGE_00005_1_patched', 'error': ['invalid throws']}
        self.assertEqual(response, expected)

        # no teams
        response = self._test_upload('vagrant:vagrant', '/pov', file='@%s' % path, csid='CADET_00003', throws=10, fail=False)
        expected = {'hash': checksum, 'file': 'LUNGE_00005_1_patched', 'error': ['invalid team']}
        self.assertEqual(response, expected)

        # no file
        response = self._test_upload('vagrant:vagrant', '/pov', csid='CADET_00003', team=2, throws=10, fail=False)
        expected = {'error': ['malformed request']}
        self.assertEqual(response, expected)
        
        # no csid
        response = self._test_upload('vagrant:vagrant', '/pov', file='@%s' % path, team=2, throws=1, fail=False)
        expected = {'hash': checksum, 'file': 'LUNGE_00005_1_patched', 'error': ['invalid csid']}
        self.assertEqual(response, expected)
       
        # no csid & invalid throws.
        response = self._test_upload('vagrant:vagrant', '/pov', file='@%s' % path, team=2, throws=-1, fail=False)
        expected = {'hash': checksum, 'file': 'LUNGE_00005_1_patched', 'error': ['invalid csid', 'invalid throws']}
        self.assertEqual(response, expected)
        
        # POVs are CBs for CFE, so... for now, just upload the patched CB as the POV
        path = os.path.join('/etc/hosts')
        checksum = unicode(self.checksum(path))
        response = self._test_upload('vagrant:vagrant', '/pov', file='@%s' % path, csid='CADET_00003', team=2, throws=10, fail=False)
        expected = {'hash': checksum, 'file': 'hosts', 'error': ['invalid format']}
        self.assertEqual(response, expected)

if __name__ == '__main__':
    unittest.main()

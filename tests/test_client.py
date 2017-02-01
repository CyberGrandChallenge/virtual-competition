#!/usr/bin/python

import os
import sys
import unittest
import tempfile
import subprocess

sys.path.append('tests')
import base_vc_test

class TestClient(base_vc_test.VirtualCompetitionBase, unittest.TestCase):

    def launch(self):
        cmd = ['bin/ti-client', '--port', '%d' % self.port]
        print ' '.join(cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)
        return proc

    def get_round(self):
        prompt = 'ti-client> '
        cmd = self.launch()
        
        cmd.stdin.write('round\n')
        cmd.stdin.write('exit\n')

        self.assertEqual('', self.get_response(cmd))
        return int(cmd.stdout.readline())

    def get_response(self, cmd):
        prompt = 'ti-client> '
        data = ''
        while prompt not in data:
            got = cmd.stdout.read(1)
            if len(got) == 0:
                raise Exception('error reading.  got: %s' % repr(data))
            data += got

        offset = -1 * len(prompt)
        return data[:offset]

    def test_feedback(self):
        """ check the syntax of the various feedback output """

        round_id = self.get_round()

        cmd = self.launch()
        cmd.stdin.write('feedback cb\n')
        cmd.stdin.write('feedback cb %d\n' % (round_id - 1))
        cmd.stdin.write('feedback pov\n')
        cmd.stdin.write('feedback pov %d\n' % (round_id - 1))
        cmd.stdin.write('feedback poll\n')
        cmd.stdin.write('feedback poll %d\n' % (round_id - 1))
        cmd.stdin.write('exit\n')
        
        self.assertEqual('', self.get_response(cmd))

        # we do 'cb' twice
        for _ in range(2):
            response = self.get_response(cmd)
            for line in response.split('\n')[:-1]:
                self.assertRegexpMatches(line, r'^\d+ [\w_]+ - signal: \d+$')
        
        # we do 'pov' twice
        for _ in range(2):
            response = self.get_response(cmd)
            # XXX - we don't actually have anything to validate at the moment.  *BAH*
        
        # we do 'poll' twice
        for _ in range(2):
            response = self.get_response(cmd)
            for line in response.split('\n')[:-1]:
                self.assertRegexpMatches(line, r'^[\w_]+ - success: \d+, timeout: \d+, connect: \d+, function: \d+, time: \d+, memory: \d+$')

        self.assertEqual(cmd.stdout.read(1), '')
    
    def test_feedback_invalid_round(self):
        """ verify feedback doesn't handle invalid rounds """

        round_id = self.get_round()
        
        round_value = round_id + 10000
        cmd = self.launch()

        for feedback_type in ['cb', 'pov', 'poll']:
            cmd.stdin.write('feedback %s %d\n' % (feedback_type, round_value))
            cmd.stdin.write('feedback %s a\n' % (feedback_type))
        cmd.stdin.write('exit\n')
        
        self.assertEqual('', self.get_response(cmd))

        for _ in range(3):
            self.assertEqual('error: feedback is only available after the specified round completes\n', self.get_response(cmd))
            self.assertEqual('error: invalid round (\'a\')\n', self.get_response(cmd))

        self.assertEqual(cmd.stdout.read(1), '')

    def test_rounds(self):
        cmd = self.launch()
        
        cmd.stdin.write('round\n')
        cmd.stdin.write('exit\n')
        
        self.assertEqual('', self.get_response(cmd))
        response = self.get_response(cmd)
        self.assertRegexpMatches(response, r'^\d+\n')
        self.assertEqual(cmd.stdout.read(1), '')

    def test_teams(self):

        cmd = self.launch()
        
        cmd.stdin.write('teams\n')
        cmd.stdin.write('exit\n')

        self.assertEqual('', self.get_response(cmd))
        expected = ', '.join('%d' % i for i in range(1, 8)) + '\n'

        self.assertEqual(expected, self.get_response(cmd))
        
        self.assertEqual(cmd.stdout.read(1), '')

    def test_counts(self):
        cmd = self.launch()
        
        cmd.stdin.write('counts\n')
        cmd.stdin.write('exit\n')
       
        self.assertEqual('', self.get_response(cmd))

        response = self.get_response(cmd)
        pov, cb, poll, round_id, team, x = response.split('\n')

        self.assertRegexpMatches(pov, r'^pov: \d+$')
        self.assertRegexpMatches(cb, r'^cb: \d+$')
        self.assertRegexpMatches(poll, r'^poll: \d+$')
        self.assertRegexpMatches(round_id, r'^round: \d+$')
        self.assertRegexpMatches(team, r'^team: \d+$')
        self.assertEqual(x, '')

        self.assertEqual(cmd.stdout.read(1), '')

    def test_scoreboard(self):
        cmd = self.launch()
        
        cmd.stdin.write('scoreboard\n')
        cmd.stdin.write('exit\n')
        
        self.assertEqual('', self.get_response(cmd))

        response = self.get_response(cmd)
        seen = []
        last_score = None

        for line in response[:-1].split('\n'):
            # team, score = cmd.stdout.readline().split(': ')
            team, score = line.split(': ')
            team = int(team)
            score = int(score)

            self.assertGreater(team, 0)
            self.assertGreater(8, team)
            self.assertGreater(score, -1)
            if last_score is not None:
                self.assertGreaterEqual(last_score, score)
            last_score = score
            self.assertNotIn(team, seen)
            seen.append(team)

        self.assertEqual(len(seen), 7)

        self.assertEqual(cmd.stdout.read(1), '')

    def test_upload_rcb(self):
        cmd = self.launch()
        cmd.stdin.write('upload_rcb CADET_00003 CADET_00003:%s\n' % os.path.join(self.cbdir, 'CADET_00003', 'bin', 'CADET_00003'))
        cmd.stdin.write('upload_rcb LUNGE_00005 LUNGE_00005_1:%s LUNGE_00005_3:%s\n' % (os.path.join(self.cbdir, 'CADET_00003', 'bin', 'CADET_00003'), os.path.join(self.cbdir, 'CADET_00003', 'bin', 'CADET_00003')))
        cmd.stdin.write('upload_rcb CADET_00003 CADET_00003:%s\n' % '/etc/passwd')
        cmd.stdin.write('upload_rcb CADET_00003 CADET_00003:%s\n' % '/etc/no_such_file_exists_here')
        cmd.stdin.write('upload_rcb CADET_00003 NONEXISTANTCBID:%s\n' % os.path.join(self.cbdir, 'CADET_00003', 'bin', 'CADET_00003'))
        cmd.stdin.write('upload_rcb CADET_00003 NONEXISTANT_3:%s\n' % os.path.join(self.cbdir, 'CADET_00003', 'bin', 'CADET_00003'))
        cmd.stdin.write('upload_rcb NONEXISTANTCSID CADET_00003:%s\n' % os.path.join(self.cbdir, 'CADET_00003', 'bin', 'CADET_00003'))
        cmd.stdin.write('exit\n')
        
        self.assertEqual('', self.get_response(cmd))
        
        response = self.get_response(cmd)
        self.assertRegexpMatches(response, r'^upload completed during round: \d+$')

        response = self.get_response(cmd)
        self.assertRegexpMatches(response, r'^upload completed during round: \d+$')

        self.assertEqual('error: invalid format\n', self.get_response(cmd))
        self.assertEqual('error: unable to open file: /etc/no_such_file_exists_here\n', self.get_response(cmd))
        self.assertEqual('error: invalid cbid\n', self.get_response(cmd))
        self.assertEqual('error: invalid cbid\n', self.get_response(cmd))
        self.assertEqual('error: invalid csid\n', self.get_response(cmd))
        self.assertEqual(cmd.stdout.read(1), '')
        
    def test_upload_pov(self):
        valid_cb = os.path.join(self.cbdir, 'CADET_00003', 'bin', 'CADET_00003')

        cmd = self.launch()
        cmd.stdin.write('upload_pov CADET_00003 2 %s\n' % valid_cb)
        cmd.stdin.write('upload_pov CADET_00003 3 %s 10\n' % valid_cb) # with throws
       
        # errors
        cmd.stdin.write('upload_pov CADET_00003 1 %s\n' % valid_cb)  # against myself
        cmd.stdin.write('upload_pov CADET_00003 2 %s 1000\n' % valid_cb)  # invalid throws
        cmd.stdin.write('upload_pov CADET_00003 1 %s 1000\n' % valid_cb)  # invalid throws
        cmd.stdin.write('upload_pov CADET_00003 0 %s\n' % valid_cb)  # non-existant team
        cmd.stdin.write('upload_pov NONCENSECSID 2 %s\n' % valid_cb)  # invalid csid
        cmd.stdin.write('upload_pov CADET_00003 2 /etc/passwd\n')  # invalid file
        cmd.stdin.write('upload_pov CADET_00003 2 /etc/no_such_file_exists_here\n')  # non-existant file
        cmd.stdin.write('exit\n')

        self.assertEqual('', self.get_response(cmd))
        response = self.get_response(cmd)
        self.assertRegexpMatches(response, r'^upload completed during round: \d+$')
        response = self.get_response(cmd)
        self.assertRegexpMatches(response, r'^upload completed during round: \d+$')
        self.assertEqual('error: invalid team\n', self.get_response(cmd))
        self.assertEqual('error: invalid throws\n', self.get_response(cmd))
        self.assertEqual('error: invalid team, invalid throws\n', self.get_response(cmd))
        self.assertEqual('error: invalid team\n', self.get_response(cmd))
        self.assertEqual('error: invalid csid\n', self.get_response(cmd))
        self.assertEqual('error: invalid format\n', self.get_response(cmd))
        self.assertEqual('error: invalid filename: /etc/no_such_file_exists_here\n', self.get_response(cmd))
        self.assertEqual(cmd.stdout.read(1), '')

    def test_upload_ids(self):
        valid_file = os.path.join(self.cbdir, 'CADET_00003', 'ids', 'CADET_00003.rules')

        cmd = self.launch()
        cmd.stdin.write('upload_ids CADET_00003 %s\n' % valid_file)
        cmd.stdin.write('upload_ids CADET00003 %s\n' % valid_file)
        cmd.stdin.write('upload_ids CADET_00003 %s\n' % '/etc/passwd')
        cmd.stdin.write('upload_ids CADET_00003 %s\n' % '/etc/no_such_file_exists_here')
        cmd.stdin.write('exit\n')
        
        self.assertEqual('', self.get_response(cmd))
        
        response = self.get_response(cmd)
        self.assertRegexpMatches(response, r'^upload completed during round: \d+$')

        self.assertEqual('error: invalid csid\n', self.get_response(cmd))
        self.assertEqual('error: invalid format\n', self.get_response(cmd))
        self.assertEqual('error: invalid filename: /etc/no_such_file_exists_here\n', self.get_response(cmd))
        self.assertEqual(cmd.stdout.read(1), '')

    def test_consensus(self):
        base_dir = tempfile.mkdtemp(dir=self.tmp_dir)
    
        ids_path = os.path.join(base_dir, 'ids')
        os.mkdir(ids_path)
        
        cb1_path = os.path.join(base_dir, 'cb1')
        os.mkdir(cb1_path)

        cb2_path = os.path.join(base_dir, 'cb2')
        os.mkdir(cb2_path)

        cmd = self.launch()
        cmd.stdin.write('consensus CADET_00003 ids 1 1 %s\n' % ids_path)
        cmd.stdin.write('consensus CADET_00003 cb 1 1 %s\n' % cb1_path)
        cmd.stdin.write('consensus LUNGE_00005 cb 1 1 %s\n' % cb2_path)

        # invalid commands
        cmd.stdin.write('consensus INVALIDCSID cb 1 1 %s\n' % base_dir)
        cmd.stdin.write('consensus CADET_00003 foo 1 1 %s\n' % base_dir)
        cmd.stdin.write('consensus CADET_00003 cb 0 -1 %s\n' % base_dir)
        cmd.stdin.write('consensus CADET_00003 cb 1 1 /etc/no_such_path\n')
        cmd.stdin.write('consensus CADET_00003 cb 1 1 /etc/\n') # unwritable path
        cmd.stdin.write('exit\n')

        self.assertEqual('', self.get_response(cmd))

        #  downloaded: /tmp/tmps0VNpE/tmpuaZ7kv/ids/CADET_00003-1-1.ids\n
        response = self.get_response(cmd)
        self.assertEqual('downloaded: %s/CADET_00003-1-1.ids\n' % ids_path, response)

        response = self.get_response(cmd)
        download_path = "%s/CADET_00003-1-1.cb" % cb1_path
        subprocess.check_output(['cgcef_verify', download_path])
        self.assertEqual('downloaded: %s\n' % download_path, response)
   
        expected = ''
        for i in range(1, 7):
            download_path = '%s/LUNGE_00005_%d-1-1.cb' % (cb2_path, i)
            expected += 'downloaded: %s\n' % (download_path)
            subprocess.check_output(['cgcef_verify', download_path])

        response = self.get_response(cmd)
        self.assertEqual(expected, response)
        
        self.assertEqual('error: invalid csid\n', self.get_response(cmd))
        self.assertEqual('error: invalid consensus type\n', self.get_response(cmd))
        self.assertEqual('error: invalid round\n', self.get_response(cmd))
        self.assertEqual('error: output directory is not a directory\n', self.get_response(cmd))
        self.assertEqual('error: unable to write downloaded file\n', self.get_response(cmd))

        self.assertEqual(cmd.stdout.read(1), '')


if __name__ == '__main__':
    unittest.main()

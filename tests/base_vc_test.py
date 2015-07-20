#!/usr/bin/python

# import json
import random
import shutil
import hashlib
import os
import sys
# import unittest
import time
import tempfile
import subprocess

class VirtualCompetitionBase(object):
    def build_cb(self):
        c = os.getcwd()
        for cb in ['LUNGE_00005', 'CADET_00003']:
            subprocess.check_output(['cp', '-r', '/usr/share/cgc-sample-challenges/examples/%s' % cb, self.tmp_dir])
            os.chdir("%s/%s" % (self.tmp_dir, cb))
            subprocess.check_output(['make', 'build', 'generate-polls'])
            subprocess.check_output(['make', 'install', 'CB_INSTALL_DIR=%s/%s' % (self.cbdir, cb)])
        os.chdir(c)

    def setUp(self):
        self.port = random.randint(2001, 3000)  # empty port range on decree
        self.tmp_dir = tempfile.mkdtemp()
        self.cbdir = '%s/challenges' % self.tmp_dir
        self.webroot = '%s/webroot' % self.tmp_dir

        for i in [self.cbdir, self.webroot]:
            if not os.path.isdir(i):
                os.mkdir(i)
        
        self.build_cb()
       
        self.rotate_process = self.background(['python', 'bin/ti-rotate', '--webroot', self.webroot, '--roundlen=1', '--cbdir', self.cbdir, '--rounds', '2'])
        self.server_process = self.background(['python', 'bin/ti-server', '--port', '%d' % self.port, '--webroot', self.webroot, '--cbdir', self.cbdir])
        if self.rotate_process.poll():
            self.fail("unable to run ti-rotate")
        self.rotate_process.communicate()
        if self.server_process.poll():
            print repr(self.server_process.communicate())
            self.fail("unable to run ti-server")

    def tearDown(self):
        if self.server_process.poll() is None:
            self.server_process.terminate()

        if self.rotate_process.poll() is None:
            self.rotate_process.terminate()

        shutil.rmtree(self.tmp_dir)

    def background(self, cmd):
        # print 'running: %s' % ' '.join(cmd)
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def checksum(self, filename):
        with open(filename, 'r') as filehandle:
            return hashlib.sha256(filehandle.read()).hexdigest()

    def foreground(self, cmd):
        p = self.background(cmd)
        return p.communicate()

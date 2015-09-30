#!/usr/bin/python

import shutil
import hashlib
import os
import select
import tempfile
import subprocess


class VirtualCompetitionBase(object):
    virtual = True
    port = 1996

    @classmethod
    def build_cb(cls):
        c = os.getcwd()
        for cb in ['LUNGE_00005', 'CADET_00003']:
            if os.path.isdir(os.path.join(cls.cbdir, cb)):
                continue

            subprocess.check_output(['cp', '-r', '/usr/share/cgc-sample-challenges/examples/%s' % cb, cls.tmp_dir])
            os.chdir("%s/%s" % (cls.tmp_dir, cb))
            subprocess.check_output(['make', 'build', 'generate-polls'])
            subprocess.check_output(['make', 'install', 'CB_INSTALL_DIR=%s/%s' % (cls.cbdir, cb)])
        os.chdir(c)

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.mkdtemp()
        
        if cls.virtual:
            cls.cbdir = '%s/challenges' % cls.tmp_dir
            cls.webroot = '%s/webroot' % cls.tmp_dir
        else:
            cls.cbdir = '/usr/share/cgc-challenges'
            cls.webroot = '/tmp/virtual-competition/webroot'
        
        for i in [cls.cbdir, cls.webroot]:
            if not os.path.isdir(i):
                os.mkdir(i)
        
        cls.build_cb()

        subprocess.check_output(['python', 'bin/ti-rotate', '--webroot', cls.webroot, '--roundlen=1', '--cbdir', cls.cbdir, '--rounds', '2'])

        if cls.virtual:
            cmd = ['python', 'bin/ti-server', '--port', '%d' % cls.port, '--webroot', cls.webroot, '--cbdir', cls.cbdir]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            handles = select.select([p.stdout, p.stderr], [], [])[0]
            cls.server_process = p
        else:
            cls.server_process = None

    @classmethod
    def tearDownClass(cls):
        if cls.server_process is not None and cls.server_process.poll() is None:
            cls.server_process.terminate()

        shutil.rmtree(cls.tmp_dir)

    def checksum(self, filename):
        with open(filename, 'r') as filehandle:
            return hashlib.sha256(filehandle.read()).hexdigest()

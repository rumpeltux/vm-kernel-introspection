#!/usr/bin/python

# ! very hacky ;-)

import sys, os, time, subprocess, re, bz2
from threading import Thread
from Queue import *
import signal

qemu_bin = "/home/domi/kvm-install/bin/qemu-system-x86_64"
qemu_mem = 512
qemu_refimage = "/home/domi/kvm/playground/ubuntu_x64_kvm_ref.qcow2.bz2"
qemu_diskimage = "/home/domi/kvm/playground/ubuntu_x64_kvm_automated.qcow2"
qemu_ssh_redirport = 5000
qemu_signal_redirport = 10000
qemu_vnc_display = 0

jobdir = "jobs"
outdir = "outfiles"

memimage_before = "memdump_before"
memimage_after = "memdump_after"
cmpscript = "/home/domi/kvm/fanalysis/memory/diff.py"

class CleanSignalCallbackThread(Thread):
	"""Creates a thread that responds to signals, not like
	the stupid python default threads ..."""
	def __init__(self, func):
		Thread.__init__(self)
		self.func = func
		for sig in range(1, signal.NSIG):
			try:
				signal.signal(sig, signal.SIG_DFL)
			except RuntimeError, e:
				pass
			pass
	def run(self):
		if not self.func is None:
			self.func()

class TimeoutError(RuntimeError):
	pass

class Pipe(object):
	"""A wrapper around a pipe opened for reading"""
	def __init__(o, pipe):
		o.pipe = pipe
		o.queue = Queue()
		o.thread = CleanSignalCallbackThread(o._loop)
		o.thread.start()
	def readline (o,timeout = None):
		"A non blocking readline function with a timeout"
		try:
			return o.queue.get(True, timeout)
		except Empty:
			raise TimeoutError
	def _loop(o):
		try:
			while True:
				line = o.pipe.readline()
				time.sleep(1)
				o.queue.put(line)
		except (ValueError, IOError): # pipe was closed
			pass
	def close(o):
		o.pipe.close()
		o.thread.join()

class Job():
	def __init__(self):
		self.file = ""
		self.commands = []
		self.name = ""

def waitready():
	isready = False
	while not isready:
		netcat = subprocess.Popen(["nc", "localhost", str(qemu_signal_redirport)], executable="nc", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		ncpipe = Pipe(netcat.stdout)
		try:
			line = ncpipe.readline(5)
			if line.find("ready") > -1:
				isready = True
				netcat.terminate()
				time.sleep(1)
				if netcat.poll() is None:
					netcat.kill()
				break
			time.sleep(5)
		except TimeoutError, e:
			netcat.terminate()
			time.sleep(1)
			if netcat.poll() is None:
				netcat.kill()



def parse_jobfiles(jobdir, onlyjob):
	jobs = []
	jobfiles = os.listdir(jobdir)

	fname_pat = re.compile('^file: (.*)$')
	command_pat = re.compile('^command: (.*)$')

	for file in jobfiles:
		job = Job()
		f = open(jobdir + "/" + file)
		if onlyjob:
			if file != onlyjob:
				continue
		for line in f:
			ret = fname_pat.search(line)
			if not ret:
				ret = command_pat.search(line)
				if not ret:
					continue
				else:
					lcommand = ret.groups()[0]
					job.commands.append(lcommand)
			else:
				lfile = ret.groups()[0]
				job.file = lfile
				job.name = file
		if job.file == "" or len(job.commands) <= 0:
			continue
		else:
			jobs.append(job)


	return jobs

if __name__ == '__main__':
	onlyjob = None
	if len(sys.argv) > 1:
		onlyjob = sys.argv[1] 

	jobs = parse_jobfiles(jobdir, onlyjob)

	if len(jobs) <= 0:
		print "no jobs found in ", jobdir
		sys.exit(1)

	print "jobs found:"
	for i in jobs:
		print i.file
		for j in i.commands:
			print "-> ", j

	print ""

	for job in jobs:
		douncompress = True
		if os.path.exists(qemu_diskimage):
			print qemu_diskimage, "already exists ... will be overwritten"
			douncompress = True

		if douncompress:	
			print "decompressing reference disk image ", qemu_refimage, " to ", qemu_diskimage

			rfile = bz2.BZ2File(qemu_refimage, "r")
			wfile = open(qemu_diskimage, "w")
			written = 0
			while True:
				tmp = rfile.read(1024*1024)
				if not tmp:
					break
				wfile.write(tmp)
				written += 1024*1024
				print written, "\r",
			wfile.close()
			rfile.close()

		print ""
		print "starting qemu ..."

		startqvnc = False
		if len(sys.argv) > 1:
			if sys.argv[1] == "-v":
				startqvnc = True
			if sys.argv[1] == "-h" or sys.argv[1] == "--help":
				print "usage: ", sys.argv[0], " [-v]"
				sys.exit(1)
		qemu_args = [str(qemu_bin), "-k", "de", "-m", str(qemu_mem), "-vnc", "127.0.0.1:" + str(qemu_vnc_display), str(qemu_diskimage), "-net", "nic,vlan=0", "-net", "user,vlan=0", "-redir", "tcp:"  + str(qemu_ssh_redirport) + "::22", "-redir", "tcp:" + str(qemu_signal_redirport) + "::10000", "-monitor", "stdio"]

		# start kvm
		kvm = subprocess.Popen(qemu_args, executable=qemu_bin, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

		firstline = kvm.stdout.readline()

		if firstline[:4] != "QEMU":
			print "qemu fail: ", firstline
			kvm.terminate()
			time.sleep(1)
			if kvm.poll() is None:
				kvm.kill()
			sys.exit(1)
		
		# start vnc graphics connection
		qvnc = None
		if startqvnc:
			qvnc = subprocess.Popen(["gvncviewer", "127.0.0.1:" + str(qemu_vnc_display)], executable="gvncviewer", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

		# wait until the ready script in virtual machine signals
		waitready()
		print "ready"
		print "pausing qemu ..."
		print >>kvm.stdin, "stop\n"
		print "saving memory to ", memimage_before, " and continuing ... ",
		print >>kvm.stdin, "pmemsave 0 600000000 ", memimage_before, "\n"
		print >>kvm.stdin, "c\n"
		waitready()
		print "ready"

		print "copying ", job.file, "...",
		sshcpy = subprocess.Popen(["scp", "-P", str(qemu_ssh_redirport), job.file, "root@localhost:"], executable="scp")
		sshcpy.wait()
		print " done"
		for cmd in job.commands:
			print "executing ", cmd, "... ",
			sshcmd = subprocess.Popen(["ssh", "-p", str(qemu_ssh_redirport), "root@localhost", cmd], executable="ssh")
			sshcmd.wait()
			print "done"

		print "waiting 10 secs ..."
		time.sleep(10)

		print "pausing qemu ..."
		print >>kvm.stdin, "stop\n"
		print "saving memory to ", memimage_after, " and continuing ... ",
		print >>kvm.stdin, "pmemsave 0 600000000 ", memimage_after, "\n"
		print >>kvm.stdin, "c\n"
		waitready()
		print "ready"

		kvm.terminate()
		time.sleep(1)
		if kvm.poll() is None:
			kvm.kill()

		if qvnc is not None:
			qvnc.kill()

		print "kvm terminated"
	
		print "running compare script..."

		cmpproc = os.system("python "+cmpscript+" "+memimage_before+" "+memimage_after+" > "+outdir+"/"+job.name)

		print "finished\n\nnextjob"
	
#	raw_input("inspect ... then press key")

#	print "shutting down"

#	sshshutdown = subprocess.Popen(["ssh", "-p", str(qemu_ssh_redirport), "root@localhost", "shutdown -h now"], executable="ssh")

#	kvm.wait()


	sys.exit(0)



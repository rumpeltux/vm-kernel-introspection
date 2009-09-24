#!/usr/bin/python

import sys, os, time, subprocess
from threading import Thread
from Queue import *
import signal

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

if __name__ == '__main__':
	startqvnc = False
	if len(sys.argv) > 1:
		if sys.argv[1] == "-v":
			startqvnc = True
		if sys.argv[1] == "-h" or sys.argv[1] == "--help":
			print "usage: ", sys.argv[0], " [-v]"
			sys.exit(1)
	qemu_bin = "/home/domi/kvm-install/bin/qemu-system-x86_64"
	#qemu_bin = "/home/domi/kvm/argdumper.sh"
	qemu_mem = 512
	qemu_diskimage = "/home/domi/ubuntu_x64_kvm.qcow2"
	qemu_ssh_redirport = 5000
	qemu_signal_redirport = 10000
	qemu_vnc_display = 0
	qemu_args = [str(qemu_bin), "-k", "de", "-m", str(qemu_mem), "-vnc", "127.0.0.1:" + str(qemu_vnc_display), str(qemu_diskimage), "-net", "nic,vlan=0", "-net", "user,vlan=0", "-redir", "tcp:"  + str(qemu_ssh_redirport) + "::22", "-redir", "tcp:" + str(qemu_signal_redirport) + "::10000", "-monitor", "stdio"]

	kvm = subprocess.Popen(qemu_args, executable=qemu_bin, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

	firstline = kvm.stdout.readline()

	if firstline[:4] != "QEMU":
		print "qemu fail: ", firstline
		kvm.terminate()
		time.sleep(1)
		if kvm.poll() is None:
			kvm.kill()
		sys.exit(1)

	qvnc = None
	if startqvnc:
		qvnc = subprocess.Popen(["gvncviewer", "127.0.0.1:" + str(qemu_vnc_display)], executable="gvncviewer")

	isready = False
	while not isready:
		netcat = subprocess.Popen(["nc", "localhost", str(qemu_signal_redirport)], executable="nc", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		ncpipe = Pipe(netcat.stdout)
		try:
			line = ncpipe.readline(5)
			print "netcat: ", line
			if line.find("ready") > -1:
				isready = True
				netcat.terminate()
				time.sleep(1)
				if netcat.poll() is None:
					netcat.kill()
				break
			time.sleep(5)
		except TimeoutError, e:
			print "noting read via netcat"
			netcat.terminate()
			time.sleep(1)
			if netcat.poll() is None:
				netcat.kill()

	print "ready"

	time.sleep(10)

	print "shutting down"

	sshshutdown = subprocess.Popen(["ssh", "-p", str(qemu_ssh_redirport), "root@localhost", "shutdown -h now"], executable="ssh")

	kvm.wait()
	if qvnc is not None:
		qvnc.kill()

	print "kvm terminated"
	
	sys.exit(0)



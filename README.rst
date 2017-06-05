NamedAtomicLock
===============

Python module for an atomic named interprocess lock which is local to the machine.

This means that this lock works across process boundries, so you can use it to lock objects that multiple processes would use.


NamedAtomicLock works by taking advantage of the fact that POSIX defines mkdir to be an atomic operation. So a directory is used as the name.

All UNIX systems are supported, overhead is light, and the lock is global to the system.


The NamedAtomicLock module provides a class NamedAtomicLock which implements the "lock" interface, with familiar "acquire" and "release" methods.

Documentation
-------------

See http://htmlpreview.github.io/?https://github.com/kata198/NamedAtomicLock/blob/master/doc/NamedAtomicLock.html 


Example
-------

A basic usage example

	from NamedAtomicLock import NamedAtomicLock


	myLock = NamedAtomicLock('myLock')


	if myLock.acquire(timeout=15):

		doWork()

		myLock.release()





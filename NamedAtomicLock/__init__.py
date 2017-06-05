'''
    Copyright (c) 2016 Timothy Savannah All Rights Reserved under terms of LGPLv3.
    You should have received a copy of this as LICENSE with the source distribution, or it is always available at
    http://www.gnu.org/licenses/lgpl-3.0.en.html

    See https://github.com/kata198/NamedAtomicLock for latest version

    NamedAtomicLock - A Named atomic lock local to the machine

'''
import os
import tempfile
import time

# vim: set ts=4 sw=4 expandtab :

__all__ = ('NamedAtomicLock',)

__version__ = '1.1.1'

__version_tuple__ = (1, 1, 1)

DEFAULT_POLL_TIME = .1

try:
    FileNotFoundError
except:
    FileNotFoundError = OSError

class NamedAtomicLock(object):

    def __init__(self, name, lockDir=None, maxLockAge=None):
        '''
            NamedAtomicLock - Create a NamedAtomicLock.
                This uses a named directory, which is defined by POSIX as an atomic operation.

            @param name <str> - The lock name, Cannot contain directory seperator (like '/')
            @param lockDir <None/str> - Directory in which to store locks. Defaults to tempdir
            @param maxLockAge <None/float> - Maximum number of seconds lock can be held before it is considered "too old" and fair game to be taken.
                You should likely define this as a reasonable number, maybe 4x as long as you think the operation will take, so that the lock doesn't get
                held by a dead process.
        '''
        self.name = name
        self.maxLockAge = maxLockAge

        if os.sep in name:
            raise ValueError('Name cannot contain "%s"' %(os.sep,))

        if lockDir:
            if lockDir[-1] == os.sep:
                lockDir = lockDir[:-1]
                if not lockDir:
                    raise ValueError('lockDir cannot be ' + os.sep)
        else:
            lockDir = tempfile.gettempdir()

        self.lockDir = lockDir

        if not os.path.isdir(lockDir):
            raise ValueError('lockDir %s either does not exist or is not a directory.' %(lockDir,))

        if not os.access(lockDir, os.W_OK):
            raise ValueError('Cannot write to lock directory: %s' %(lockDir,))
        self.lockPath = lockDir + os.sep + name
        
        self.held = False
        self.acquiredAt = None

    def acquire(self, timeout=None):
        '''
            acquire - Acquire given lock. Can be blocking or nonblocking by providing a timeout.
              Returns "True" if you got the lock, otherwise "False"

            @param timeout <None/float> - Max number of seconds to wait, or None to block until we can acquire it.

            @return  <bool> - True if you got the lock, otherwise False.
        '''
        # If we aren't going to poll at least 5 times, give us a smaller interval
        if self.held is True:
            if os.path.exists(self.lockPath):
                return True
            # Someone removed our lock
            self.held = False

        if timeout:
            if timeout / 5.0 < DEFAULT_POLL_TIME:
                pollTime = timeout / 10.0
            else:
                pollTime = DEFAULT_POLL_TIME
            
            endTime = time.time() + timeout
            keepGoing = lambda : bool(time.time() < endTime)
        else:
            pollTime = DEFAULT_POLL_TIME
            keepGoing = lambda : True

                    

        success = False
        while keepGoing():
            try:
                os.mkdir(self.lockPath) 
                success = True
                break
            except:
                time.sleep(pollTime)
                if self.maxLockAge:
                    if os.path.exists(self.lockPath) and os.stat(self.lockPath).st_mtime < time.time() - self.maxLockAge:
                        try:
                            os.rmdir(self.lockPath)
                        except:
                            # If we did not remove the lock, someone else is at the same point and contending. Let them win.
                            time.sleep(pollTime)
        
        if success is True:
            self.acquiredAt = time.time()

        self.held = success
        return success

    def release(self, forceRelease=False):
        '''
            release - Release the lock.

            @param forceRelease <bool> - If True, will release the lock even if we don't hold it.

            @return - True if lock is released, otherwise False
        '''
        if not self.held:
            if forceRelease is False:
                return False # We were not holding the lock
            else:
                self.held = True # If we have force release set, pretend like we held its
        
        if not os.path.exists(self.lockPath):
            self.held = False
            return True

        if forceRelease is False:
            # We waited too long and lost the lock
            if self.maxLockAge and time.time() > self.acquiredAt + self.maxLockAge:
                self.held = False
                return False

        try:
            os.rmdir(self.lockPath)
            self.held = False
            return True
        except:
            self.held = False
            return False

    @property
    def isHeld(self):
        '''
            isHeld - True if anyone holds the lock, otherwise False.

            @return bool - If lock is held by anyone
        '''
        if not os.path.exists(self.lockPath):
            return False
        
        try:
            mtime = os.stat(self.lockPath).st_mtime
        except FileNotFoundError as e:
            return False
        
        if mtime < time.time() - self.maxLockAge:
            # Expired
            return False

        return True

    @property
    def hasLock(self):
        '''
            hasLock - Property, returns True if we have the lock, or False if we do not.

            @return <bool> - True/False if we have the lock or not.
        '''
        # If we don't hold it currently, return False
        if self.held is False:
            return False
        
        # Otherwise if we think we hold it, and it is held, it must be held.
        if not self.isHeld:
            self.held = False
            return False

        return True


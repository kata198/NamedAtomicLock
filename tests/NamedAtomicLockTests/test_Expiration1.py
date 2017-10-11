#!/usr/bin/env GoodTests.py
'''
    Expiration unit tests for NamedAtomicLock

        NOTE: Additional tests should have their own class for performance reasons
          ( each class gets its own fork )

'''

import os
import random
import subprocess
import time
import sys


import NamedAtomicLock



class TestExpiration1(object):
    '''
        TestExpiration1 - Expiration1 tests
    '''

    def setup_class(self):
        '''
            setup_class - Called once to setup this class for testing.

                Sets the following attributes:

                  self.lockPrefix - A unique prefix based on the uid, unix timestamp, and random numbers
        '''
        
        randomNumbers = [ random.randint(1000, 9999) for i in range(3) ]

        self.lockPrefix = "%d_%d_%s__" %( os.getuid(), int(time.time()), ','.join([str(num) for num in randomNumbers]))



    def setup_method(self, whichMethod):
        '''
            setup_method - Called for every method.

              Sets the following: 

                 self.lockObj - A NamedAtomicLock which is guarenteed to not be held (i.e. is force released)

                self.otherLocks - Set to an empty list. Append locks here to have them automatically released on teardown (including for test_basic)
        '''

        self.otherLocks = []
        
#        self.lockObj = NamedAtomicLock.NamedAtomicLock(self.lockPrefix + 'test_Expiration1')
#
#        # Force release, so no matter previous state we start fresh
#        self.lockObj.release(forceRelease=True)


    def teardown_method(self, whichMethod):
        '''
            teardown_method - Called after completion of each method (pass or fail)

                @param whichMethod - The method which just completed
        
             Interacts with following attributes:

                self.lockObj   - force-releases this common lock

                self.otherLocks - Any locks in this list will be force released

              If there are any errors in releasing, this method will continue to try to release all other locks
                and raise an AssertionError at the end containing all the failures.
        '''

        errorMsgs = []
#        try:
#            self.lockObj.release(forceRelease=True)
#        except Exception as e:
#            errorMsgs.append('Got exception trying to force-release the common lock for TestExpiration1. %s:  %s' %(type(e).__name__, str(e)))

        for otherLock in self.otherLocks:
            try:
                otherLock.release(forceRelease=True)
            except Exception as e:
                errorMsgs.append('Got exception trying to free a member of "otherLocks" [ "%s" ]. %s:  %s' %(otherLock.name, type(e).__name__, str(e)))

        if errorMsgs:
            raise AssertionError('Got %d errors in teardown of %s.\n\n%s' %(len(errorMsgs), '\n\n'.join(errorMsgs)))



    def test_expire(self):
        
        lockName = self.lockPrefix + '_test_Expiration1_expire1'

        lockObj = NamedAtomicLock.NamedAtomicLock(lockName, maxLockAge=3)

        self.otherLocks.append(lockObj)

        # altObj - Shares name with lockObj
        altObj  = NamedAtomicLock.NamedAtomicLock(lockObj.name, maxLockAge=3)

        # Acquire lock and assert attributes
        didAcquire = lockObj.acquire(1)

        assert didAcquire , 'Expected acquire to return True'

        assert lockObj.hasLock , 'Expected to have lock on object after acquire'
        assert lockObj.isHeld , 'Expected isHeld=TRue on held lock'

        assert not altObj.hasLock , 'Expected alt object to not have lock'
        assert altObj.isHeld , 'Expected alt object to show that lock is held by someone else'

        # Sleep past expiration
        time.sleep(3.5)

        assert lockObj.hasLock is False , 'Expected hasLock to change to False after maxLockAge passes'
        assert lockObj.isHeld is False , 'Expected isHeld to  change to False after maxLockAge passes'
        assert altObj.isHeld is False , 'Expected isHeld to  change to False after maxLockAge passes for alt obj'

        didAcquire = altObj.acquire(1)

        assert didAcquire , 'Expected alt object to be able to acquire after maxLockAge passes, without original lock releasing'


if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

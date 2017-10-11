#!/usr/bin/env GoodTests.py
'''
    Locking unit tests for NamedAtomicLock
'''

import os
import random
import subprocess
import time
import sys


import NamedAtomicLock



class TestLocking(object):
    '''
        TestLocking - Locking tests
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

              unless you are the 'test_basic' method, which does a basic runthrough of acquire/release (and thus asserts that this method will work at all)

                self.otherLocks - Set to an empty list. Append locks here to have them automatically released on teardown (including for test_basic)
        '''

        self.otherLocks = []
        
        if whichMethod != self.test_basic:
            # test_basic does a basic run-through and asserts that the forced release
            #    would work, so don't pre-setup on that method.
            self.lockObj = NamedAtomicLock.NamedAtomicLock(self.lockPrefix + 'test_Locking')

            # Force release, so no matter previous state we start fresh
            self.lockObj.release(forceRelease=True)

    def teardown_method(self, whichMethod):
        '''
            teardown_method - Called after completion of each method (pass or fail)

                @param whichMethod - The method which just completed
        
             Interacts with following attributes:

                self.lockObj   - Except for test_basic, force-releases this common lock

                self.otherLocks - Any locks in this list will be force released

              If there are any errors in releasing, this method will continue to try to release all other locks
                and raise an AssertionError at the end containing all the failures.
        '''

        errorMsgs = []
        if whichMethod != self.test_basic:
            try:
                self.lockObj.release(forceRelease=True)
            except Exception as e:
                errorMsgs.append('Got exception trying to force-release the common lock for TestLocking. %s:  %s' %(type(e).__name__, str(e)))

        for otherLock in self.otherLocks:
            try:
                otherLock.release(forceRelease=True)
            except Exception as e:
                errorMsgs.append('Got exception trying to free a member of "otherLocks" [ "%s" ]. %s:  %s' %(otherLock.name, type(e).__name__, str(e)))

        if errorMsgs:
            raise AssertionError('Got %d errors in teardown of %s.\n\n%s' %(len(errorMsgs), '\n\n'.join(errorMsgs)))



    def test_basic(self):
        '''
            test_basic - Test a basic run-through
        '''

        lockName = self.lockPrefix + 'test_Locking__basic'

        thisLock = NamedAtomicLock.NamedAtomicLock(lockName)

        # Force-release this lock after method is called
        self.otherLocks.append(thisLock)

        if thisLock.isHeld:
            # If anybody holds this lock (somehow? Very unlikely due to lockPrefix..), then force release it.
            sys.stderr.write('Warning: Lock with name "%s" was already held, but should not have been...\n\n' %( lockName, ))

            assert not self.hasLock , 'Fresh lock object using name "test_Locking__basic" is held, and by us! (should not be. Could be held, but not by us.)'

            try:
                thisLock.release(forceRelease=True)
            except Exception as e:
                raise AssertionError('Error forcing release of already-held lock. %s:  %s' %(type(e).__name__, str(e)) )

            assert not thisLock.isHeld , "Failed to force-release lock which shouldn't have been held in the first place..."
            assert not thisLock.hasLock , "hasLock is True after force-releasing lock which shouldn't have been held in the first place..."
        else:
            assert not thisLock.hasLock , "hasLock is True even though isHeld is False"
        
        gotLock = thisLock.acquire(timeout=2)

        assert gotLock is True, 'Expected acquire to return True indicating that we obtained the lock, but got False.'

        assert thisLock.isHeld , 'Expected after acquire that isHeld=True, but it was False'
        assert thisLock.hasLock , 'Expected after acquire that hasLock=True, but it was False'

        stillHasLock = thisLock.acquire(timeout=2)

        assert stillHasLock is True, 'Expected calling acquire after already holding the lock returns True, but got: %s' %(repr(stillHasLock), )

        isHeld = thisLock.isHeld
        assert isHeld is True , 'Expected calling acquire after already acquired keeps isHeld=True, but got: %s' %(repr(isHeld), )

        hasLock = thisLock.hasLock
        assert hasLock is True , 'Expected calling acquire after already acquired keeps hasLock=True, but got: %s' %(repr(hasLock), )

        # Test that creating a lock using the same name, even though other object, still is held.
        otherLockObj = NamedAtomicLock.NamedAtomicLock(lockName)

        assert otherLockObj.isHeld is True , 'Expected a new NamedAtomicLock object with same "name" as an already-acquired lock has isHeld=True'
        assert otherLockObj.hasLock is False , 'Expected a new NamedAtomicLock object with same "name" as an already-acquired lock has hasLock=False, even though isHeld=True (lock is held in general, but not with this new object)'

        # Try to release (non-forced) with other object

        didRelease = otherLockObj.release(forceRelease=False)

        assert not didRelease , 'Called release on lock that is held but not by that object, expected release to return False.'

        assert thisLock.isHeld , 'Expected failed release to not change "isHeld" status'
        assert thisLock.hasLock , 'Expected failed release to not change "hasLock" on owning object'

        assert otherLockObj.isHeld is True , 'Expected failed release to not change "isHeld" on alternate obj'
        assert otherLockObj.hasLock is False, 'Expected failed release to not change "hasLock" on alternate obj'

        # Try to release with hoilding object
        didRelease = thisLock.release(forceRelease=False)

        assert didRelease , 'Expected "release" on lock-holding object to return True (success)'

        assert not thisLock.isHeld , 'Expected after "release" isHeld=False'
        assert not thisLock.hasLock , 'Expected after "release" hasLock=False'

        assert otherLockObj.isHeld is False , 'Expected after "release", other object has isHeld=False'
        assert otherLockObj.hasLock is False , 'Expected after "release", other object has hasLock=False'


    def test_acquireRelease(self):
        
        lockObj = self.lockObj

        # altObj - Shares name with lockObj
        altObj  = NamedAtomicLock.NamedAtomicLock(lockObj.name)

        # Doesn't need to go into otherLocks because name is same, and teardown forces release
        #self.otherLocks.append(altObj)

        # Acquire lock and assert attributes
        didAcquire = lockObj.acquire(2)

        assert didAcquire , 'Expected acquire to return True'

        assert lockObj.hasLock , 'Expected to have lock on object after acquire'
        assert lockObj.isHeld , 'Expected isHeld=TRue on held lock'

        assert not altObj.hasLock , 'Expected alt object to not have lock'
        assert altObj.isHeld , 'Expected alt object to show that lock is held by someone else'

        # Try to acquire already-held lock with alternate object
        didAcquire = altObj.acquire(1)

        assert didAcquire is False , 'Expected alt object to not be able to acquire already-held lock'

        # Try to release with held object
        didRelease = lockObj.release(forceRelease=False)
        
        assert didRelease , 'Expected to be able to release lock we held'
        assert lockObj.hasLock == lockObj.isHeld == False , 'Expected hasLock and isHeld to be False after release'
        assert altObj.hasLock == altObj.isHeld == False , 'Expected hasLock and isHeld to be False after release for alt obj'

        # Re-acquire
        didAcquire = lockObj.acquire(2)

        assert didAcquire , 'Failed to re-acquire lock'

        # Try to release with alternate object (non-force)
        didRelease = altObj.release(forceRelease=False)

        assert not didRelease , 'Expected to not be able to release lock we did not hold'

        assert lockObj.hasLock , 'After failed release: Expected to have lock on object after acquire'
        assert lockObj.isHeld , 'After failed release: Expected isHeld=TRue on held lock'

        assert not altObj.hasLock , 'After failed release: Expected alt object to not have lock'
        assert altObj.isHeld , 'After failed release: Expected alt object to show that lock is held by someone else'


        # Try to release with alternate object (force)
        didRelease = altObj.release(forceRelease=True)

        assert didRelease , 'Expected forceRelease=True to allow alt object to release lock'

        assert not lockObj.isHeld , 'Expected isHeld=False after release'
        assert not lockObj.hasLock , 'Expected hasLock=False on orig object after forced-release on alt obj'

        assert not altObj.isHeld , 'Expected isHeld=False after release for alt obj'
        assert not altObj.hasLock , 'Expected hasLock=False on orig object after forced-release on alt obj for alt obj'




if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

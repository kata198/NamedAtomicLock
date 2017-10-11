#!/usr/bin/env GoodTests.py
'''
    General unit tests for NamedAtomicLock
'''

import os
import random
import subprocess
import sys
import time

import NamedAtomicLock

class TestGeneral(object):
    '''
        TestGeneral - General tests
    '''

    def setup_class(self):
        '''
            setup_class - Called once to setup this class for testing.

                Sets the following attributes:

                  self.lockPrefix - A unique prefix based on the uid, unix timestamp, and random numbers
        '''
        
        randomNumbers = [ random.randint(1000, 9999) for i in range(3) ]

        self.lockPrefix = "%d_%d_%s__" %( os.getuid(), int(time.time()), ','.join([str(num) for num in randomNumbers]))


    def test_init(self):
        '''
            test_init - Test the init function
        '''

        LOCK_NAME = self.lockPrefix + 'test_general_init'

        # Test basic create -- just a name
        gotException = False
        try:
            myLock = NamedAtomicLock.NamedAtomicLock(LOCK_NAME)
        except Exception as e:
            gotException = e

        assert gotException is False , "Exception trying to create a NamedAtomicLock object with just a lock name. %s:  %s" %( type(gotException).__name__, str(gotException))


        assert myLock.name == LOCK_NAME , 'Expected "name" attribute to be set. Expected "%s" but got "%s"' %(LOCK_NAME, myLock.name, )

        # Test that no name fails
        gotException = False
        try:
            myLock = NamedAtomicLock.NamedAtomicLock()
        except:
            gotException = True

        assert gotException , 'Expected constructor to require a name, but was able to create a NamedAtomicLock.NamedAtomicLock object without one.'


        # Test alternate lock dir
        thisDir = os.path.realpath( os.getcwd() )

        myLock = NamedAtomicLock.NamedAtomicLock(LOCK_NAME, lockDir=thisDir)

        assert myLock.lockPath.startswith(thisDir) , 'Passed in alternate lockDir of "%s", but was not used ( generated path is "%s" )' %(thisDir, myLock.lockPath)

        assert myLock.lockDir == thisDir , 'Expected "lockDir" attribute to be set to alternate path'


        # Test that we fail when providing an alternate lockDir which does not exist
        gotException = False
        try:
            # If this path does exist on your system, you deserve to fail.
            myLock = NamedAtomicLock.NamedAtomicLock(LOCK_NAME, lockDir='/blargie_pie')
        except ValueError as e:
            gotException = e
        except Exception as e:
            raise AssertionError('Expected invalid lockDir to throw a ValueError, but we got a %s exception instead.' %( type(e).__name__, ))


        assert gotException is not False , 'Expected to get a ValueError providing a lockDir which does not exist'

        # I don't like testing for exception string, but make sure it is the one we threw and not some unexpected ValueError
        #   origin someowhere else..
        assert str(gotException).startswith('lockDir /blargie_pie') , 'Got a ValueError passing a lockDir which does not exist, but the message is not expected (i.e. a ValueError was thrown by something unexpected).\nGot: ' + str(gotException)


        # Assert the maxLockAge attribute is setting
        myLock = NamedAtomicLock.NamedAtomicLock(LOCK_NAME)

        assert myLock.maxLockAge is None , 'Expected providing no maxLockAge to have value of "None". Got: %s' %(repr(myLock.maxLockAge), )

        myLock = NamedAtomicLock.NamedAtomicLock(LOCK_NAME, maxLockAge=3600)
    
        assert myLock.maxLockAge == 3600 , 'Expected passing maxLockAge=3600 to set on the object. Got: %s' %(repr(myLock.maxLockAge), )



if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

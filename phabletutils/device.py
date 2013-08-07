# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
# Copyright 2013 Canonical
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess
import logging

from time import sleep

log = logging.getLogger()


def call(args):
    subprocess.check_call(args, shell=True)


def check_output(args):
    return subprocess.check_output(args, shell=True)


class Device(object):
    '''Android device.'''

    def __init__(self, cmd, device=None):
        if device:
            log.info('Setting device %s' % device)
            self._cmd = '%s -s %s %%s' % (cmd, device)
        else:
            self._cmd = '%s %%s' % cmd
        self._device = device

    @property
    def device(self):
        '''Returns the device used for the adb interface.'''
        return self._device


class AndroidBridge(Device):
    '''Interface to adb.'''

    def __init__(self, device=None):
        '''Initializes an adb interface attached to a given device.'''
        super(AndroidBridge, self).__init__(device=device, cmd='adb')

    def start(self):
        '''Attempts to start adb if not running.'''
        log.debug('Starting adb server')
        cmd = 'start-server'
        call(self._cmd % cmd)

    def push(self, src, dst):
        '''Performs and adb push.'''
        log.info('Pushing %s to %s' % (src, dst))
        cmd = 'push %s %s' % (src, dst)
        call(self._cmd % cmd)

    def pull(self, src, dst):
        '''Performs and adb pull.'''
        log.info('Pulling %s to %s' % (src, dst))
        cmd = 'pull %s %s' % (src, dst)
        call(self._cmd % cmd)

    def wait_for_device(self, wait=2):
        '''Waits for device.'''
        # Hack wait to avoid LP:1176929
        log.info('Restarting device... wait')
        sleep(wait)
        call(self._cmd % 'wait-for-device')
        log.info('Restarting device... wait complete')

    def root(self):
        '''Set device to work as root.'''
        call(self._cmd % 'root')
        self.wait_for_device()

    def chmod(self, filename, mode):
        '''Performs a chmod on target device.'''
        cmd = 'shell chmod %s %s' % (mode, filename)
        call(self._cmd % cmd)

    def getprop(self, android_property):
        '''Returns an android property.'''
        cmd = 'shell getprop %s ' % (android_property)
        return check_output(self._cmd % cmd)

    def tcp_forward(self, src, dst):
        '''Creates a tcp forwarding rule.'''
        cmd = 'forward tcp:%s tcp:%s' % (src, dst)
        call(self._cmd % cmd)

    def shell(self, command):
        '''Runs shell command and returns output'''
        cmd = 'shell %s' % command
        return check_output(self._cmd % cmd)

    def chroot(self, command, root='data/ubuntu'):
        '''Runs command in chroot.'''
        log.debug('Running in chroot: %s' % command)
        cmd = 'shell "PATH=/usr/sbin:/usr/bin:/sbin:/bin ' \
              'system/xbin/chroot %s %s"' % (root, command)
        call(self._cmd % cmd)

    def reboot(self, recovery=False, bootloader=False):
        '''Reboots device.'''
        log.info('Restarting device... wait')
        if recovery:
            cmd = 'reboot recovery'
        elif bootloader:
            cmd = 'reboot bootloader'
        else:
            cmd = 'reboot'
        call(self._cmd % cmd)
        if recovery:
            sleep(20)
        log.info('Restarting device... wait complete')


class Fastboot(Device):
    '''Interface to fastboot'''

    def __init__(self, device=None):
        super(Fastboot, self).__init__(device=device, cmd='fastboot')

    def flash(self, image_partition, image_file):
        log.info('Flashing %s to %s' % (image_partition, image_file))
        cmd = 'flash %s %s' % (image_partition, image_file)
        call(self._cmd % cmd)

    def flash_system(self, image_file):
        self.flash('system', image_file)

    def flash_recovery(self, image_file):
        self.flash('recovery', image_file)

    def flash_boot(self, image_file):
        self.flash('boot', image_file)

    def reboot(self):
        log.info('Rebooting device')
        cmd = 'reboot'
        call(self._cmd % cmd)

    def boot(self, image_file=None):
        if image_file:
            log.info('Booting %s' % image_file)
            cmd = 'boot %s' % image_file
        else:
            log.info('Booting OS')
            cmd = 'boot'
        call(self._cmd % cmd)

    def wipe(self):
        log.info('Wiping all userdata')
        cmd = '-w'
        call(self._cmd % cmd)

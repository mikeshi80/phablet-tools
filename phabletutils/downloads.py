# This program is free software: you can redistribute it and/or modify it
# under the terms of the the GNU General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the applicable version of the GNU Lesser General Public
# License for more details.
#.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2013 Canonical, Ltd.

import hashlib
import logging
import os
import subprocess


log = logging.getLogger()


def download(uri, target):
    '''Downloads an artifact into target.'''
    log.info('Downloading %s' % uri)
    if uri.startswith('http://cdimage.ubuntu.com') or \
       uri.startswith('https://system-image.ubuntu.com'):
        subprocess.check_call(['wget', '-c', uri, '-O', target])
    else:
        subprocess.check_call(['curl', '-L', '-C', '-', uri, '-o', target])


class Downloader(object):
    '''A helper to fetch multiple artifacts.'''

    def __init__(self, uri, download_list, hashes):
        '''Initializes a download helper for android based images.'''
        self._uri = uri
        self._download_list = download_list
        self._hashes = hashes
        if hashes:
            self.validate = self._validate
        else:
            self.validate = self._validate_legacy

    def download(self):
        '''Downloads and validates the download list.'''
        for file_path in self._download_list:
            if self.validate(file_path):
                continue
            uri = '%s/%s' % (self._uri, os.path.basename(file_path))
            if not uri:
                raise EnvironmentError('In offline mode and checksum does '
                                       'not match for at least %s' % file_path)
            download(uri, file_path)
            if not self._hashes:
                file_hash = '%s.md5sum'
                download(file_hash % uri, file_hash % file_path)
            if not self.validate(file_path):
                raise EnvironmentError('File download failed for %s to %s' %
                                       (uri, file_path))
            log.info('Validating download of %s' % file_path)

    def _validate(self, file_path):
        '''Validates downloaded files against a checksum.'''
        file_name = os.path.basename(file_path)
        if file_name not in self._hashes:
            return False
        return self.checksum_file(file_path) == self._hashes[file_name]

    def _validate_legacy(self, file_path):
        '''Validates with the legacy method of individual md5sum files.'''
        file_hash = '%s.md5sum' % file_path
        if not os.path.exists(file_hash):
            return False
        with open(file_hash, 'r') as f:
            read_hash = f.read().split()[0]
        return self.checksum_file(file_path, hashlib.md5) == read_hash

    def checksum_file(self, file_path, sum_method=hashlib.sha256):
        '''Returns the checksum for a file with a specified algorightm.'''
        file_sum = sum_method()
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'rb') as f:
            for file_chunk in iter(
                    lambda: f.read(file_sum.block_size * 128), b''):
                file_sum.update(file_chunk)
        return file_sum.hexdigest()

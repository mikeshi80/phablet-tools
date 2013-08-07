# Copyright (C) 2013 Canonical Ltd.
# Author: Sergio Schvezov <sergio.schvezov@canonical.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Unit tests for phabletutils.environment."""

from mock import patch
from phabletutils import cdimage
from testtools import TestCase
from testtools.matchers import Equals


@patch('subprocess.check_output')
class TestCdimageLinks(TestCase):
    def setUp(self):
        super(TestCdimageLinks, self).setUp()
        self.cdimage_uri = 'http://cdimage.ubuntu.com/ubuntu-touch/daily-build'
        self.rsync_uri_part = 'rsync://cdimage.ubuntu.com/cdimage/' \
                              'ubuntu-touch/daily-build'
        self.rsync_call = ['rsync', '-l']

    def testCurrent(self, process_mock):
        """Given a cdimage uri return the linked build for current."""
        # given
        target_build = '20130714'
        process_mock.return_value = target_build
        self.rsync_call.append('%s/current' % self.rsync_uri_part)
        # when
        build = cdimage.get_latest_current(self.cdimage_uri)
        # then
        self.assertThat(build, Equals(target_build))
        process_mock.assert_called_once_with(self.rsync_call)

    def testPending(self, process_mock):
        """Given a cdimage uri return the linked build for current."""
        # given
        target_build = '20130714.1'
        process_mock.return_value = target_build
        self.rsync_call.append('%s/pending' % self.rsync_uri_part)
        # when
        build = cdimage.get_latest_pending(self.cdimage_uri)
        # then
        self.assertThat(build, Equals(target_build))
        process_mock.assert_called_once_with(self.rsync_call)
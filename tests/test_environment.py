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
from os import path
from phabletutils import environment
from phabletutils import settings
from testtools import TestCase
from testtools.matchers import Equals
from testscenarios import TestWithScenarios
from testscenarios import multiply_scenarios


class FakeSettings(object):
    download_dir = 'fake_download_dir'
    device_file_img = 'device-%s.img'
    boot_file_img = 'boot-%s.img'


@patch('phabletutils.environment.get_ubuntu_stamp')
class TestPlainEnvironments(TestCase):
    def setUp(self):
        super(TestPlainEnvironments, self).setUp()
        self.device = 'mako'
        self.series = 'saucy'
        self.settings = FakeSettings()
        self.uri = 'http://download.com/artifacts'
        self.build = '10'

    def testNonCdimage(self, get_ubuntu_stamp):
        # given
        get_ubuntu_stamp.return_value = self.build
        download_dir = path.join(self.settings.download_dir, self.build)
        full_download_dir = environment.get_download_dir_full_path(
            download_dir)
        system_img_path = path.join(full_download_dir,
            self.settings.device_file_img % self.device)
        boot_img_path = path.join(full_download_dir,
                                  self.settings.boot_file_img % self.device)
        # when
        env = environment.Environment(self.uri, self.device, self.series,
                                      None, None, False, None, None,
                                      self.settings)
        # then
        self.assertFalse(env.project)
        self.assertThat(env.download_dir, Equals(full_download_dir))
        self.assertThat(env.download_uri, Equals(self.uri))
        self.assertThat(env.system_img_path, Equals(system_img_path))
        self.assertThat(env.boot_img_path, Equals(boot_img_path))
        self.assertFalse(env.recovery_img_path)


def get_file_paths(files, download_dir, device, series):
    if not series:
        series = settings.default_series
    replacements = (series, device)
    files = {
        'system_img': path.join(download_dir,
                                files['system_img'] % replacements),
        'boot_img': path.join(download_dir,
                              files['boot_img'] % replacements),
        'recovery_img': path.join(download_dir,
                                  files['recovery_img'] % replacements),
        'device_zip': path.join(download_dir,
                                files['device_zip'] % replacements),
        'ubuntu_zip': path.join(download_dir, files['ubuntu_zip'] % series),
    }
    return files


@patch('phabletutils.cdimage.get_sha256_content')
@patch('phabletutils.cdimage.get_latest_current')
class TestCdimageEnvironments(TestWithScenarios, TestCase):

    scenarios = multiply_scenarios(
                [('legacy touch', dict(legacy=True)),
                 ('touch', dict(legacy=False))],
                [('use default series', dict(series=None)),
                 ('set series', dict(series='raring'))],
                [('base path', dict(base_path='/prev_download')),
                 ('no base path', dict(base_path=None))])

    def setUp(self):
        super(TestCdimageEnvironments, self).setUp()
        if self.legacy:
            self.project = 'ubuntu-touch-preview'
        else:
            self.project = 'ubuntu-touch'
        self.device = 'manta'
        self.build = '20130606'
        self.download_dir = path.join(settings.download_dir,
                                      self.project, self.build)
        if not self.base_path:
            self.full_download_dir = environment.get_download_dir_full_path(
                    self.download_dir)
            self.download_uri = path.join(settings.cdimage_uri_base,
                    self.project, 'daily-preinstalled', self.build)
        else:
            self.full_download_dir = self.base_path
            self.download_uri = None
        self.files = get_file_paths(settings.files[self.project],
                                    self.full_download_dir,
                                    self.device, self.series)

    def testEnvironmentSetup(self, cdimage_get_latest, cdimage_sha256):
        # given
        cdimage_get_latest.return_value = self.build
        cdimage_sha256.return_value = 'sha'
        # when
        env = environment.Environment(None, self.device, self.series,
                                      None, None, False, self.legacy,
                                      self.base_path, settings)
        # then
        self.assertTrue(env.project)
        self.assertThat(env.download_dir, Equals(self.full_download_dir))
        self.assertThat(env.download_uri, Equals(self.download_uri))
        self.assertThat(env.system_img_path, Equals(self.files['system_img']))
        self.assertThat(env.boot_img_path, Equals(self.files['boot_img']))
        self.assertThat(env.device_zip_path, Equals(self.files['device_zip']))
        self.assertThat(env.ubuntu_zip_path, Equals(self.files['ubuntu_zip']))
        self.assertThat(env.recovery_img_path,
                Equals(self.files['recovery_img']))
        # Check recovery file list
        self.assertTrue(self.files['device_zip'] in env.recovery_files)
        self.assertTrue(self.files['ubuntu_zip'] in env.recovery_files)
        self.assertFalse(self.files['recovery_img'] in env.recovery_files)
        self.assertFalse(self.files['system_img'] in env.recovery_files)
        self.assertFalse(self.files['boot_img'] in env.recovery_files)
        # Check bootstrap file list
        self.assertFalse(self.files['device_zip'] in env.bootstrap_files)
        self.assertTrue(self.files['ubuntu_zip'] in env.bootstrap_files)
        self.assertTrue(self.files['recovery_img'] in env.bootstrap_files)
        self.assertTrue(self.files['system_img'] in env.bootstrap_files)
        self.assertTrue(self.files['boot_img'] in env.bootstrap_files)
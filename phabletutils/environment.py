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

import configobj
import logging
import requests

from os import path
from phabletutils import cdimage
#from xdg.BaseDirectory import xdg_config_home
from os.path import expanduser

log = logging.getLogger()


def get_download_dir_full_path(subdir):
    #try:
    #    userdirs_file = path.join(xdg_config_home, 'user-dirs.dirs')
    #    userdirs_config = configobj.ConfigObj(userdirs_file, encoding='utf-8')
    #    userdirs_download = path.expandvars(
    #        userdirs_config['XDG_DOWNLOAD_DIR'])
    #    download_dir = userdirs_download
    #except KeyError:
    #    download_dir = path.expandvars('$HOME')
    #    log.warning('XDG_DOWNLOAD_DIR could not be read')
    download_dir = expanduser('~')
    return path.join(download_dir, subdir)


def get_ubuntu_stamp(uri):
    '''Downloads the jenkins build id from stamp file'''
    try:
        ubuntu_stamp = requests.get('%s/quantal-ubuntu_stamp' % uri)
        if ubuntu_stamp.status_code != 200:
            ubuntu_stamp = requests.get('%s/ubuntu_stamp' % uri)
        if ubuntu_stamp.status_code != 200:
            log.error('Latest build detection not supported... bailing')
            exit(1)
        # Make list and get rid of empties
        build_data = filter(lambda x: x.startswith('JENKINS_BUILD='),
                            ubuntu_stamp.content.split('\n'))
        jenkins_build_id = build_data[0].split('=')[1]
    except (requests.HTTPError, requests.Timeout, requests.ConnectionError):
        log.error('Could not download build data from jenkins... bailing')
        exit(1)
    except IndexError:
        log.error('Jenkins data format has changed, incompatible')
        exit(1)
    return jenkins_build_id


class Project(object):

    @property
    def uri(self):
        return self._uri

    @property
    def download_uri(self):
        return self._download_uri

    @property
    def download_dir(self):
        return self._download_dir

    @property
    def name(self):
        return self._project

    @property
    def series(self):
        return self._series

    def hashes(self):
        return cdimage.get_sha256_dict(self.hash_content)

    @property
    def hash_content(self):
        self._load_hashes()
        return self._hash_content

    @property
    def hash_file_name(self):
        return self._hash_file_name

    def list_revisions(self):
        revisions = cdimage.get_available_revisions(self._uri)
        cdimage.display_revisions(revisions)

    def __init__(self, project, series, cdimage_uri_base, base_path,
                 hash_file_name, pending, revision=None, latest_revision=None):
        if not project:
            return None
        log.debug('project: %s, series: %s, cdimage_uri_base: %s, '
                  'base_path: %s, hash_file_name: %s, revision: %s, '
                  'latest_revision: %s, pending: %s' % (project, series, 
                  cdimage_uri_base, base_path, hash_file_name, revision, 
                  latest_revision, pending))
        self._project = project
        self._uri = '%s/%s' % (cdimage_uri_base, project)
        self._series = series
        self._hash_file_name = hash_file_name

        if base_path:
            download_uri = None
            download_dir = base_path
        elif latest_revision:
            self._series, revision = \
                cdimage.get_latest_revision(self._uri)
            download_uri = '%s/%s/%s' % (self._uri,
                                         self._series, revision)
            download_dir = path.join(project, self._series, revision)
        elif revision:
            revision_split = revision.split('/')
            if len(revision_split) != 2:
                raise EnvironmentError(
                    'Improper use of revision, needs to be formatted like'
                    '[series]/[revision]. Use --list-revisions to find'
                    'the available revisions on cdimage')
            # TODO add verification that uri exists
            self._series = revision_split[0]
            download_uri = '%s/%s' % (self._uri, revision)
            download_dir = path.join(project, self._series, revision)
        else:
            uri = '%s/daily-preinstalled' % self._uri
            if pending:
                link = cdimage.get_latest_pending(uri)
            else: 
                link = cdimage.get_latest_current(uri)
            download_uri = '%s/%s' % (uri, link)
            download_dir = path.join(project, link)
        self._download_uri = download_uri
        self._download_dir = download_dir

    def _load_hashes(self):
        self._hash_path = path.join(self._download_dir, self._hash_file_name)
        if path.exists(self._hash_path):
            with open(self._hash_path, 'r') as f:
                hash_content = f.read()
        else:
            hash_content = cdimage.get_sha256_content(
                '%s/%s' % (self._download_uri, self._hash_file_name))
        self._hash_content = hash_content


class Environment(object):
    '''All the hacks to support multiple environments live here.'''

    @property
    def project(self):
        return self._project

    @property
    def download_dir(self):
        return self._download_dir

    @property
    def download_uri(self):
        return self._download_uri

    @property
    def bootstrap_files(self):
        return [self._files[i] for i in self._bootstrap_files]

    @property
    def recovery_files(self):
        return [self._files[i] for i in self._recovery_files]

    @property
    def device_zip_path(self):
        return self._files['device_zip']

    @property
    def ubuntu_zip_path(self):
        return self._files['ubuntu_zip']

    @property
    def system_img_path(self):
        return self._files['system_img']

    @property
    def boot_img_path(self):
        return self._files['boot_img']

    @property
    def recovery_img_path(self):
        return self._files['recovery_img']

    def __init__(self, preset_uri, device, series, latest_revision, revision,
                 pending, legacy, base_path, settings):
        self._set_project(series, pending, legacy, base_path, latest_revision,
                          revision, settings)
        self._set_download(preset_uri, settings)
        self._files, self._bootstrap_files, self._recovery_files = \
            self._set_files(device, settings)

    def _set_project(self, series, pending, legacy, base_path,
                     latest_revision, revision, settings):
        if getattr(settings, 'revision', None):
            if not series:
                series = settings.default_series
            if legacy:
                project_name = 'ubuntu-touch-preview'
            else:
                project_name = 'ubuntu-touch'
            self._project = Project(
                project_name, series, settings.cdimage_uri_base, base_path,
                settings.hash_file_name, pending, revision, latest_revision)
        else:
            self._project = None

    def _set_download(self, preset_uri, settings):
        if preset_uri:
            self._download_uri = preset_uri
        elif not self._project:
            self._download_uri = settings.download_uri
        elif self._project:
            self._download_uri = self._project.download_uri
        else:
            raise EnvironmentError('Environment not setup correctly')
        if self._project:
            download_dir = path.join(settings.download_dir,
                                     self._project.download_dir)
        else:
            download_dir = path.join(settings.download_dir,
                                     get_ubuntu_stamp(self.download_uri))
        log.debug('Download set to %s' % self.download_uri)
        if self._download_uri:
            self._download_dir = get_download_dir_full_path(download_dir)
        else:
            self._download_dir = download_dir

    def _set_files(self, device, settings):
        files = {}
        project = self._project
        if project:
            templ = settings.files[project.name]
            files['ubuntu_zip'] = templ['ubuntu_zip'] % (project.series,)
            for key in templ:
                if key is 'ubuntu_zip':
                    continue
                files[key] = templ[key] % (project.series, device)
            bootstrap_files = ['ubuntu_zip', 'system_img', 'boot_img',
                                     'recovery_img']
            recovery_files = ['device_zip', 'ubuntu_zip']
        else:
            files['ubuntu_zip'] = None
            files['device_zip'] = None
            files['recovery_img'] = None
            files['system_img'] = settings.device_file_img % (device,)
            files['boot_img'] = settings.boot_file_img % (device,)
            bootstrap_files = ['system_img', 'boot_img']
            recovery_files = None
        for key in files:
            if not files[key]:
                continue
            files[key] = path.join(self._download_dir, files[key])
        return files, bootstrap_files, recovery_files
            

    def store_hashes(self):
        if not self._project.hash_content:
            return None
        with open(path.join(self._download_dir,
                  self._project.hash_file_name), 'w') as f:
            for line in self._project.hash_content:
                f.write(line)

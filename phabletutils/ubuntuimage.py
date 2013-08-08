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

import json
import os.path
import requests

from phabletutils import downloads
from phabletutils import settings


def get_json_from_index(device, index=-1):
    """Returns json index for device"""
    json_index_uri = '%s/daily/%s/index.json' % \
        (settings.system_image_uri, device)
    json_index_request = requests.get(json_index_uri)
    json_index = json.loads(json_index_request.content)
    version_data = sorted([entry for entry in json_index['images']
                          if entry['type'] == "full"],
                          key=lambda entry: entry['version'])[index]
    return version_data


def download_images(download_dir, json_list):
    files = {}
    files['updates'] = []
    for entry in sorted(json_list['files'], key=lambda entry: entry['order']):
        filename = entry['path'].split("/")[-1]
        signame = entry['signature'].split("/")[-1]
        filename_path = os.path.join(download_dir, filename)
        signame_path = os.path.join(download_dir, signame)
        filename_uri = '%s/%s' % (settings.system_image_uri, entry['path'])
        signame_uri = '%s/%s' % (settings.system_image_uri, entry['signature'])
        with downloads.flocked(filename_path):
            downloads.download(filename_uri, filename_path)
            downloads.download(signame_uri, signame_path)
        files['updates'].append({'filename': filename_path,
                                 'signame': signame_path})
    files['base'] = []
    for keyring in ('image-master', 'image-signing'):
        filename = '%s.tar.xz' % keyring
        signame = '%s.asc' % filename
        filename_path = os.path.join(download_dir, filename)
        signame_path = os.path.join(download_dir, signame)
        filename_uri = '%s/gpg/%s' % (settings.system_image_uri, filename)
        signame_uri = '%s.asc' % filename_uri
        with downloads.flocked(filename_path):
            downloads.download(filename_uri, filename_path)
            downloads.download(signame_uri, signame_path)
        files['base'].append({'filename': filename_path,
                              'signame': signame_path})
    return files

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

import logging
import re
import requests
import subprocess
import urlparse


log = logging.getLogger()


def _get_elements(uri):
    '''Scraps cdimage and returns a list of relevant links as elements.'''
    request = requests.get(uri).content
    html_elements = filter(
        lambda x: '<li><a href=' in x and
        'Parent Directory' not in x and
        'daily' not in x and
        'current' not in x,
        request.split('\n'))
    # cdimage lays out the content in more than one way.
    if not html_elements:
        html_elements = filter(
            lambda x: 'alt="[DIR]"' in x and
            'Parent Directory' not in x and
            'daily' not in x and
            'pending' not in x and
            'current' not in x,
            request.split('\n'))
        html_elements = [re.search(r'<a.* href.*>.*</a>', x).group(0)
                         for x in html_elements]
    elements_inter = [re.sub('<[^>]*>', '', i) for i in html_elements]
    elements = [i.strip().strip('/') for i in elements_inter]
    return elements


def _get_releases(uri):
    '''Fetches the available releases for a given cdimage project URI.'''
    releases = [{'release': i, 'uri': '%s/%s' % (uri, i)}
                for i in _get_elements(uri)]
    log.debug('releases: %s', releases)
    return releases


def _get_revisions(uri):
    '''Returns the revisions for a given release URI.'''
    return _get_elements(uri)


def get_available_revisions(cdimage_uri):
    '''Returns all the releases available for a given cdimage project.'''
    if cdimage_uri[-1] != '/':
        cdimage_uri = cdimage_uri + '/'
    releases = _get_releases(cdimage_uri)
    for release in releases:
        release['revisions'] = _get_revisions(release['uri'])
    return releases


def get_latest_revision(cdimage_uri):
    '''Returns the latest revision tagged.'''
    log.debug('cdimage_uri: %s', cdimage_uri)
    try:
        latest_release = _get_releases(cdimage_uri)[-1]
        log.debug('latest_release: %s', latest_release)
        latest_revision = _get_revisions(latest_release['uri'])[-1]
    except IndexError:
        raise EnvironmentError('No releases for current project. Verify '
                               'by checking %s' % cdimage_uri)
    return latest_release['release'], latest_revision


def display_revisions(revisions):
    '''Displays the available revisions for a give cdimage project.'''
    for series in revisions:
        print 'Available releases:'
        if 'revisions' in series:
            for rev in series['revisions']:
                print '\t%s/%s' % (series['release'], rev)
        else:
            print 'No releases for %s available' % rev['release']
    if not revisions:
        print 'No revisions have been tagged for this project yet'
        print 'To list revisions from the preview images add the ' \
              '--legacy switch'


def _get_link_target(uri):
    '''Returns the target for the link in the image.'''
    uri = urlparse.urlparse(uri)
    uri = 'rsync://%s/cdimage%s' % (uri.netloc, uri.path)
    link = subprocess.check_output(['rsync', '-l', uri]).split()[-1]
    return link


def get_latest_current(cdimage_uri):
    '''Returns the latest build in current.'''
    uri = '%s/%s' % (cdimage_uri, 'current')
    build = _get_link_target(uri)
    return build


def get_latest_pending(cdimage_uri):
    '''Returns the latest build in pending.'''
    uri = '%s/%s' % (cdimage_uri, 'pending')
    build = _get_link_target(uri)
    return build


def get_sha256_dict(hash_file_content):
    '''Returns a dictionary with the sha256 sums for all files.'''
    if not hash_file_content:
        log.debug('hash file is empty')
        return None
    hash_list = filter((lambda x: len(x) is not 0),
                       hash_file_content.split('\n'))
    hash_list = [h.split() for h in hash_list]
    hash_dict = {}
    for hash_entry in hash_list:
        if hash_entry[1][0] == '*':
            hash_entry[1] = hash_entry[1][1:]
        hash_dict[hash_entry[1]] = hash_entry[0]
    return hash_dict


def get_sha256_content(cdimage_hash_uri):
    '''Fetches the SHA256 sum file from cdimage.'''
    hash_request = requests.get(cdimage_hash_uri)
    if hash_request.status_code != 200:
        return None
    else:
        return hash_request.content

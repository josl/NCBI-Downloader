#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

'''

from source import ontology, platforms, location_hash
from template import metadata, mandatory_fields
import re
import urllib
import copy
import logging
import sys
import json
import io

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='%(levelname)s:%(message)s',
    filename='metadata.log',
    filemode='w'
)
_logger = logging.getLogger(__name__)


class Metadata():

    def __init__(self, attrs, accession):
        self.metadata = copy.deepcopy(metadata)
        self.metadata.update(attrs)
        self.accession = accession.strip()
        self.url = 'http://www.ncbi.nlm.nih.gov/sra/?term=%s&format=text' % (
            self.accession)
        self.data = urllib.urlopen(self.url).read()

    def __format_date(yyyy=None, mm=None, dd=None):
        '''
        This method stringify the date tuple using a standard format:
          YYYY-MM-DD or
          YYYY-MM or
          YYYY
        If all arguments are None, FormatDate returns an empty string
        '''
        date = ''
        if yyyy is not None and yyyy != '':
            if mm is not None and mm != '':
                if dd is not None and dd != '':
                    date = '%04d-%02d-%02d' % (yyyy, mm, dd)
                else:
                    date = '%04d-%02d' % (yyyy, mm)
            else:
                date = '%04d' % (yyyy)
        return date

    def save_metadata(self, dir):
        '''
        Writes self.metadata as meta.json in dir
        :param: dir
        :return: True
        '''
        f = open('%s/meta.json' % dir, 'w')
        f.write(json.dumps(self.metadata, ensure_ascii=False))
        f.close()

    def valid_metadata(self):
        '''
        Checks if metadata is valid
        :return: True if all mandatory fields are not ''
        '''
        for i in mandatory_fields:
            if self.metadata[i] == '':
                return False
                break
        return True

    def update_files(self, files):
        '''
        Checks if metadata is valid
        :return: True if all mandatory fields are not ''
        '''
        self.metadata['files_names'] = files

    def update_attributes(self):
        '''
        XXX
        :return: accessionid of non identified sources
        '''

        match = re.findall(r'Sample Attributes: (.+)\n', self.data)
        for answer in match:
            for attributes in answer.split(';'):
                stat = attributes.split('=')
                att = stat[0].strip('/ ').lower().replace('\'', '')
                val = stat[1].strip('\' ').replace('\'', '\`')
                if att == 'geo_loc_name' and ':' in stat[1]:
                    self.metadata['country'] = val.split(':')[0]
                    self.metadata['region'] = val.split(':')[1]
                elif att == 'geo_loc_name':
                    self.metadata['country'] = val
                elif att == 'serovar':
                    self.metadata['subtype']['serovar'] = val
                elif att == 'mlst':
                    self.metadata['subtype']['mlst'] = val
                elif att == 'isolation_source':
                    found = False
                    for cat, keywords in ontology:
                        if any([x in val.lower() for x in keywords]):
                            found = True
                            self.metadata[att] = cat
                            break
                    if not found:
                        _logger.warning(
                            'Source not identified: %s, %s',
                            val, self.accession
                        )
                    self.metadata['source_note'] = val
                elif att == 'BioSample':
                    self.metadata['notes'] = '%s BioSample=%s, ' % (
                        self.metadata['notes'], val)
                elif att == 'collection date':
                    self.metadata[att] = __format_date(*InterpretDate(val))
                    if self.metadata[att] == '':
                        _logger.warning(
                            'Date Empty: %s',
                            val, self.accession
                        )
                elif att == 'geographic location':
                    geo_dict = {
                        'country': '',
                        'region': '',
                        'city': '',
                        'zip_code': '',
                        'longitude': '',
                        'latitude': '',
                        'location_note': ''
                    }
                    val = val.lower()
                    if val not in location_hash.keys():
                        try:
                            g = geocoder.google(val)
                        except Exception, e:
                            _logger.warning(
                                'Geocoder error %s', self.accession
                            )
                            location_hash[val] = ('', '', '', '', val)
                        else:
                            try:
                                results = g.content['results'][0]
                                for x in results['address_components']:
                                    type = x['types'][0]
                                    type_map = {
                                        'country': 'country',
                                        'postal_code': 'zip_code',
                                        'administrative_area_level_1':
                                            'region',
                                        'locality': city
                                    }
                                    if type in type_map.values():
                                        m_type = type_map[type]
                                        geo_dict[m_type] = x['long_name']
                            except:
                                try:
                                    a_tmp = g.address.split(',')
                                    if len(address_tmp) > 2:
                                        geo_dict['city'] = a_tmp[0]
                                        geo_dict['region'] = a_tmp[-2]
                                        geo_dict['country'] = a_tmp[-1]
                                    elif len(address_tmp) == 2:
                                        geo_dict['city'] = a_tmp[0]
                                        geo_dict['country'] = a_tmp[-1]
                                    elif len(address_tmp) == 1:
                                        geo_dict['country'] = a_tmp[0]
                                except:
                                    pass
                                else:
                                    try:
                                        geo_dict['zip_code'] = int(
                                            geo_dict['city'].split(' ')[0]
                                        )
                                    except:
                                        pass
                            finally:
                                geo_dict['longitude'] = g.lng
                                geo_dict['latitude'] = g.lat
                                geo_dict['location_note'] = g.location
                    self.metadata.update(geo_dict)
                elif att in self.metadata:
                    self.metadata[att] = val
                else:
                    self.metadata['notes'] = '%s %s: %s, ' % (
                        self.metadata['notes'], att, val)

        match = re.findall(r'Sample Attributes: (.+)\n', self.data)
        for answer in match:
            self.metadata['sequencing_platform'] = platforms.get(
                answer.lower(), 'unknown'
            )

        match = re.findall(r'Library Layout: (.+)\n', self.data)
        for answer in match:
            self.metadata['sequencing_type'] = answer.split(',')[0].lower()
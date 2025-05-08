#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
#------------------------------------------------------------------------------
# Name:  wcs_client.py
#
#   General purpose WCS 2.0 Client:
#       The routine is inteded to be imported as modules.
#       If cmd-line usage is desired the cmdline_wcs_client.py will provide it.
#       The documentation of the modules functionality is provided as doc-strings.
#
#   This WCS-Client provides the following functionality:
#         - GetCapabilities Request
#         - DescribeCoverage Request
#         - GetCoverage Request
#
#         - return responses
#         - download coverages
#         - download time-series of coverages
#
#   It allows users to specify:
#         + Server URL
#         + Coverage
#          + Axes subsets
#         + Rangesubsetting (eg. Bands)
#         + File-Format (image format) for downloads
#         + output CRS for downloads
#         + interpolation
#
# Name:        wcs_client.py
# Project:     DeltaDREAM
# Author(s):   Christian Schiller <christian dot schiller at eox dot at>
##
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------
"""
import base64
import sys
import os
import time, datetime
import urllib.request, urllib.error, urllib.parse, socket

global __version__
__version__ = '0.1'

    # check for OS Platform and set the Directory-Separator to be used
global dsep
dsep = os.sep

    # sets the url where epsg CRSs are defined/referenced
global crs_url
crs_url = 'http://www.opengis.net/def/crs/EPSG/0/'


    # sets a storage location in case the user doesn't provide one (to be on the save side) - eg. for error msgs.
global temp_storage
temp_storage = None
try_dir = ['TMP', 'TEMP', 'HOME', 'USER']
for elem in try_dir:
    temp_storage = os.getenv(elem)
    if temp_storage != None:
        break

if temp_storage is None:
    cur_dir = os.getcwd()
    temp_storage = cur_dir # +'/tmp'




#/************************************************************************/
#/*                              wcsClient()                             */
#/************************************************************************/

class wcsClient(object):
    """
        General purpose WCS client for WCS 2.0 server access.
        It offers:
          - GetCapabilities Request
          - DescribeCoverage Request
          - GetMap Request
        It therefore provides the receipt of
            - GetCapabilities response XML documents
            - DescribeCoverage response XML documents
            - download coverages using GetCoverage request
            - download time-series of coverages using the combination of
         It allows the users to specify:
            + Server URL
            + Coverage
            + Axes subsets
            + Rangesubsetting (eg. Bands)
            + File-Format (image format) for downloads
            + output CRS for downloads
            + interpolation

        Detailed description of parameters associated with each Request are
        porvided with the respective request
    """
        # default timeout for all sockets (in case a requests hangs)
    _timeout = 180
    socket.setdefaulttimeout(_timeout)
    def __init__(self):
        pass

    #/************************************************************************/
    #/*                           _set_base_request()                        */
    #/************************************************************************/
    def _set_base_request(self):
        """
            Returns the basic url components for any valid WCS request
        """
        base_request = {'service': 'service=WCS'}

        return base_request

    #/************************************************************************/
    #/*                            _set_base_cap()                           */
    #/************************************************************************/
    def _set_base_cap(self):
        """
            Returns the basic url components for a valid GetCapabilities request
        """
        base_cap = {'request': '&request=',
            'server_url': '',
            'updateSequence': '&updateSequence=',
            'sections' :'&sections='}

        return base_cap


    #/************************************************************************/
    #/*                            _set_base_desccov()                       */
    #/************************************************************************/
    def _set_base_desccov(self):
        """
            Returns the basic urls components for a valid DescribeCoverage Request
        """
        base_desccov = {'version': '&version=',
            'request': '&request=',
            'server_url': '',
            'coverageID': '&coverageID='}

        return base_desccov


    #/************************************************************************/
    #/*                             _set_base_getcov()                        */
    #/************************************************************************/
    def _set_base_getcov(self):
        """
           Rreturns the basic urls components for a GetCoverage Request
        """
        getcov_dict = {'version': '&version=',
            'request': '&request=',
            'server_url': '',
            'coverageID': '&coverageid=',
            'format': '&format=',
            'rangesubset': '&rangesubset=',
            'subsettingcrs': '&subsettingcrs=',
            'outputcrs': '&outputcrs=',
            'interpolation': '&interpolation=',
            'output': None}

        return getcov_dict


    #/************************************************************************/
    #/*                           GetCapabilities()                          */
    #/************************************************************************/
    def GetCapabilities(self, input_params, username='', password=''):
        """
            Creates a GetCapabilitiy request url based on the input_parameters
            and executes the request.
            Returns:  XML GetCapabilities resonse
        """
        procedure_dict = self._set_base_cap()
        http_request = self._create_request(input_params, procedure_dict)
        result_xml = wcsClient._execute_xml_request(self, http_request, username, password)

        return result_xml


    #/************************************************************************/
    #/*                           DescribeCoverage()                         */
    #/************************************************************************/
    def DescribeCoverage(self, input_params, username='', password=''):
        """
            Creates a DescribeCoverage request url based on the input_parameters
            and executes the request.
            Returns:   XML DescribeCoverage response
        """
        procedure_dict = self._set_base_desccov()

        http_request = self._create_request(input_params, procedure_dict)
        result_xml = wcsClient._execute_xml_request(self, http_request, username, password)

        return result_xml


    #/************************************************************************/
    #/*                              GetCoverage()                           */
    #/************************************************************************/

    def GetCoverage(self, input_params, username='', password='', subsets_requests_params_str=''):
        """
            Creates a GetCoverage request url based on the input_parameters
        """
        procedure_dict = self._set_base_getcov()
        http_request = self._create_request(input_params, procedure_dict)

        if subsets_requests_params_str != '':
            http_request += "&" + subsets_requests_params_str

        result, outfile = wcsClient._execute_getcov_request(self, http_request, input_params, username, password)
        return result, outfile


    #/************************************************************************/
    #/*                         _execute_xml_request()                       */
    #/************************************************************************/
    def _execute_xml_request(self, http_request, username='', password=''):
        """
            Executes the GetCapabilities, DescribeCoverage
            requests based on the generated http_url
            Returns:  either XML response document  or  a list of coverageIDs
            Output: prints out the submitted http_request  or Error_XML in case of failure
        """

        print('REQUEST: ',http_request)  #@@

        try:
            # create a request object,
            request_handle = urllib.request.Request(http_request, headers={'User-Agent': 'Python-urllib/2.7,QgsWcsClient-plugin'})

            if username != "" and password != "":
                # Encode credentials
                credentials = f"{username}:{password}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()

                # Create request with Authorization header
                request_handle.add_header("Authorization", f"Basic {encoded_credentials}")

            response = urllib.request.urlopen(request_handle)
            xml_result = response.read()
            status = response.code

            # extract only the CoverageIDs and provide them as a list for further usage
            return xml_result

        except urllib.error.URLError as url_ERROR:
            if hasattr(url_ERROR, 'reason'):
                print('\n', time.strftime("%Y-%m-%dT%H:%M:%S%Z"), "- ERROR:  Server not accessible -" , url_ERROR.reason)
                err_msg=['ERROR', url_ERROR.read()]
                return err_msg

            elif hasattr(url_ERROR, 'code'):
                print(time.strftime("%Y-%m-%dT%H:%M:%S%Z"), "- ERROR:  The server couldn\'t fulfill the request - Code returned:  ", url_ERROR.code, url_ERROR.read())
                err_msg = str(url_ERROR.code)+'--'+url_ERROR.read()
                return err_msg

        return


    #/************************************************************************/
    #/*                     _execute_getcov_request()                        */
    #/************************************************************************/

    def _execute_getcov_request(self, http_request, input_params, username='', password=''):
        """
            Executes the GetCoverage request based on the generated http_url and stores
            the received/downloaded coverages in the defined  output location.
            The filenames are set to the coverageIDs (with extension according to requested file type)
            plus the current date and time. This timestamp is added to avoid accidentaly overwriting of
            received coverages having the same coverageID but a different subsets.

            Output: prints out the submitted http_request
                    stores the received datasets
                    saves Error-XML (-> access_error_"TimeStamp".xml) at output location (in case of failure)
            Returns:  HttpCode (if success)
        """
        print('REQUEST:', http_request)

        now = time.strftime('_%Y-%m-%dT%H:%M:%S')

            # set some common extension to a more 'useful' type
        if input_params['format'].find('/') != -1:
            out_format_ext = os.path.basename(input_params['format'])
            if out_format_ext == "tiff":
                out_format_ext = "tif"
            elif out_format_ext == "x-netcdf":
                out_format_ext = "nc"
            elif out_format_ext == "jpeg":
                out_format_ext = "jpg"
            elif out_format_ext == "x-hdf":
                out_format_ext = "hdf"
            elif out_format_ext.startswith("gml"):
                out_format_ext = "gml"
        else:
            out_format_ext = input_params['format']


        out_coverageID = input_params['coverageID']+now+'.'+out_format_ext  # input_params['format']

        if 'output' in input_params and input_params['output'] is not None:
            outfile = input_params['output']+dsep+out_coverageID
        else:
            outfile = temp_storage+dsep+out_coverageID
            print('REQUEST-GetCov: ',http_request)

        try:
            request_handle = urllib.request.Request(http_request, headers={'User-Agent': 'Python-urllib/2.7,QgsWcsClient-plugin'})

            if username != "" and password != "":
                # Encode credentials
                credentials = f"{username}:{password}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()

                # Create request with Authorization header
                request_handle.add_header("Authorization", f"Basic {encoded_credentials}")

            response = urllib.request.urlopen(request_handle)
            result = response.read()
            status = response.code

            try:
                file_getcov = open(outfile, 'w+b')
                file_getcov.write(result)
                file_getcov.flush()
                os.fsync(file_getcov.fileno())
                file_getcov.close()
                return status, outfile


            except IOError as xxx_todo_changeme:
                (errno, strerror) = xxx_todo_changeme.args
                print("I/O error({0}): {1}".format(errno, strerror))
            except:
                print("Unexpected error:", sys.exc_info()[0])
                raise


        except urllib.error.URLError as url_ERROR:
            if hasattr(url_ERROR, 'reason'):
                print('\n', time.strftime("%Y-%m-%dT%H:%M:%S%Z"), "- ERROR:  Server not accessible -", url_ERROR.reason)
                    # write out the servers return msg
                errfile = outfile.rpartition(dsep)[0]+dsep+'access_error'+now+'.xml'
                access_err = open(errfile, 'w+b')
                access_err.write(url_ERROR.read())
                access_err.flush()
                access_err.close()
                return None, errfile
            elif hasattr(url_ERROR, 'code'):
                print(time.strftime("%Y-%m-%dT%H:%M:%S%Z"), "- ERROR:  The server couldn\'t fulfill the request - Code returned:  ", url_ERROR.code, url_ERROR.read())
                err_msg = str(url_ERROR.code)+'--'+url_ERROR.read()
                return err_msg, None
        except TypeError:
            pass

        return


    #/************************************************************************/
    #/*                              _merge_dicts()                           */
    #/************************************************************************/
    def _merge_dicts(self, input_params, procedure_dict):
        """
            Merge and harmonize the input_params-dict with the required request-dict
            e.g. the base_getcov-dict
        """
        request_dict = {}
        for k, v in input_params.items():
            #print 'TTTT: ',  k,' -- ',v
                # make sure there is always a version set
            if k == 'version' and (v == '' or v == None):
                v = '2.0.0'
                # skip all keys with None or True values
            if v == None or v == True:
                continue

                # create the request-dictionary but ensure there are no whitespaces left
                # (which got inserted for argparse() to handle negativ input values correctly)
            request_dict[k] = str(procedure_dict[k])+str(v).strip()

            # get the basic request settings
        base_request = self._set_base_request()
        request_dict.update(base_request)

        return request_dict



    #/************************************************************************/
    #/*                               _create_request()                      */
    #/************************************************************************/
    def _create_request(self, input_params, procedure_dict):
        """
            Create the http-request according to the user selected Request-type
        """

        request_dict = self._merge_dicts(input_params, procedure_dict)
            # this doesn't look so nice, but this way I can control the order within the generated request
        http_request = ''
        if 'server_url' in request_dict:
            http_request = http_request+request_dict.get('server_url')
            if not http_request.endswith("?"):
                http_request += "?"

        if 'service' in request_dict:
            http_request = http_request+request_dict.get('service')
        if 'version' in request_dict:
            http_request = http_request+request_dict.get('version')
        if 'request' in request_dict:
            http_request = http_request+request_dict.get('request')
        if 'coverageID' in request_dict:
            http_request = http_request+request_dict.get('coverageID')
        if 'format' in request_dict:
            http_request = http_request+request_dict.get('format')
        if 'rangesubset' in request_dict:
            http_request = http_request+request_dict.get('rangesubset')
        if 'subsettingcrs' in request_dict:
            http_request = http_request+request_dict.get('subsettingcrs')
        if 'outputcrs' in request_dict:
            http_request = http_request+request_dict.get('outputcrs')
        if 'interpolation' in request_dict:
            http_request = http_request+request_dict.get('interpolation')
        if 'mediatype' in request_dict:
            http_request = http_request+request_dict.get('mediatype')

        return http_request


#/************************************************************************/
# /*            END OF:        wcs_Client()                              */
#/************************************************************************/





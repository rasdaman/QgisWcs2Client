QgsWcsClient2
=============

A QGIS WCS 2.0 Plugin

A tool to download (and subset in space and time) raster data and get the data in your desired file-format and projection.

The WCS 2.0 allows to GetCapabilities, DescribeCoverage then access/download via GetCoverage request the raster data (coverages) from OGC WCS 2.0 compliant servers.
Unlike WMS, WCS enables the access to the original data (and not just to portrayals).
For multi-bands coverages, the bands of interest can also be selected/sub-setted and their order in the output can be chosen.
The 2D downloaded coverages encoded in these formats (png, tiff, netCDF) are directly loaded as layers into QGIS.


Added Features & Fixed Bugs:

2025-05-18
- Added support for basic header authentication
- Simplified GetCapabilities tab
- Improved functionalities in GetCoverage tab
- Moved content of help and about as .html pages out of the python code
- Removed dependency on lxml python package

2024-01-15
- Update for QGIS 3.x

2017-05-03 - version 0.3:
- added Button to import WCS-Urls already stored in native QGis settings
- added Button to sort the Server_List
- enabled resizing of QgsWcsClient2-Client Window
- added "WGS84 UpperCorner & WGS84LowerCorner" (BoundingBox) fields to GetCapabilities and DescribeEOCoverageSet Results-View
- added a uniq "Browser tag" to be submitted with the requests, to verify in the access log-files that the Qgis-plugin was used (Identifies now with User-Agent => 'Python-urllib/2.7,QgsWcsClient-plugin')
- enabled support to access https:// sites
- config_server.pkl file (containing the server entries) will not get overwritten during update/re-installatinon anymore (a default one will only be installed if it is not available at plugin startup)
- added possibility to view full GetCapabilities XML response-document (also made more clear to view DescribeEOCoverageSet XML) (now all are accessible => GetCap, DescCov, DescEOCov:  just use copy/paste to save them)
- better error checking e.g. for http errors -> warning messages (e.g. for redirects, automatic redirection is not supported to minimize security issues)
- fixed xml_parsing error
- fixed issue with "offered CRS"
- fixed issue "offered interpolation"
- fixed issue if no coverage was found in selected time-period
- removed the "striping/alternatingRowColors" from the Coverage-listings
- fixed issue with "no data selected" fixed for "DescribeEOCoverage" Request
- fixed various the xml-namespace handling issues
- fixed issue with the "clock" icon shown permanently
- fixed Time selection (BeginTime/EndTime) for DescribeEOCoverageSet (2.5 D coverages i.e 2D plus Time), added plausability check
- fixed issue with associateing the corresponding axisLabel / CRS etc. with each coverage (once DescribeCoverage is executed for a specific Coverage)

2017-09-22 - version 0.3.1:
- fixed minor issue with Windows installation of 'config_srvlist.pkl' - due to differernt line endings in Linux/Windows

2018-06-26 - version 0.3.2
- fixed issue when modifying a Server-URL without changing Server-Name
- fixed issue with DescribeEOCoverageSet requests when using sections parameter

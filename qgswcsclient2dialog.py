# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgsWcsClient2
                                 A QGIS plugin
 A OGC WCS 2.0/EO-WCS Client
                             -------------------
        begin                : 2014-06-26; 2017-04-10
        copyright            : (C) 2014 by Christian Schiller / EOX IT Services GmbH, Vienna, Austria
        email                : christian dot schiller at eox dot at
 ***************************************************************************/

/*********************************************************************************/
 *  The MIT License (MIT)                                                         *
 *                                                                                *
 *  Copyright (c) 2014 EOX IT Services GmbH                                       *
 *                                                                                *
 *  Permission is hereby granted, free of charge, to any person obtaining a copy  *
 *  of this software and associated documentation files (the "Software"), to deal *
 *  in the Software without restriction, including without limitation the rights  *
 *  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell     *
 *  copies of the Software, and to permit persons to whom the Software is         *
 *  furnished to do so, subject to the following conditions:                      *
 *                                                                                *
 *  The above copyright notice and this permission notice shall be included in    *
 *  all copies or substantial portions of the Software.                           *
 *                                                                                *
 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR    *
 *  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,      *
 *  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE   *
 *  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER        *
 *  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, *
 *  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE *
 *  SOFTWARE.                                                                     *
 *                                                                                *
 *********************************************************************************/
 The main QgsWcsClient2 Plugin Application -- an OGC WCS 2.0/EO-WCS Client
 """

from builtins import str
from builtins import range
import os, pickle
from collections import defaultdict

from PyQt5 import sip

from qgis.core import *

from qgis.PyQt import QtCore, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *
from qgis.PyQt.QtWidgets import QProgressDialog, QDialog, QMessageBox, QFileDialog, QApplication
from qgis.PyQt.QtGui import QCursor

from .ui_qgswcsclient2 import Ui_QgsWcsClient2
from .qgsnewhttpconnectionbasedialog import qgsnewhttpconnectionbase
from .display_txtdialog import display_txt
from .downloader import download_url
from .EOxWCSClient.wcs_client import wcsClient



#global setttings and saved server list
global config
from . import config
import xml.etree.ElementTree as ET
from typing import Union, Optional


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)


#---------------
    # running clock icon
def mouse_busy(function):
    """
        set the mouse icon to show clock
    """
        #def new_function(self):
    def new_function(*args, **kwargs):
        """
            set the mouse icon to show clock
        """
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()

        try:
            #function(self)
            return function(*args, **kwargs)
        except Exception as e:
            raise e
            print("Error {}".format(e.args[0]))
        finally:
            QApplication.restoreOverrideCursor()

    QApplication.restoreOverrideCursor()
    return new_function


#---------------
    # provide a pop-up warning message
def warning_msg(msg):
    """
        present a message in a popup dialog-box
    """
    msgBox = QtWidgets.QMessageBox()
    msgBox.setText(msg)
    msgBox.addButton(QtWidgets.QPushButton('OK'), QtWidgets.QMessageBox.YesRole)
    msgBox.exec_()


#---------------


## ====== Main Class ======

class QgsWcsClient2Dialog(QDialog, Ui_QgsWcsClient2):
    """
        main QGis-WCS plugin dialog
    """
    def __init__(self, iface):
        global config

        QDialog.__init__(self)
        self.setupUi(self)
        self.iface = iface

            # if server information is already available, activate the Edit-Button, and the update the
            # selectionBar
        if len(config.srv_list['servers']) > 0:
            self.btnEdit_Serv.setEnabled(True)
            self.btnDelete_Serv.setEnabled(True)
            self.updateServerListing()

                # creating progress dialog for download
        # self.progress_dialog = QProgressDialog(self)
        # self.progress_dialog.setAutoClose(True)  # False # was set originally
        # title = self.tr("WSC-2.0/EO-WCS Downloader")
        # self.progress_dialog.setWindowTitle(title)

            # instantiate the wcsClient
        self.myWCS = wcsClient()

        self.treeWidget_GCa.itemClicked.connect(self.on_GCa_clicked)
        self.treeWidget_DC.itemClicked.connect(self.on_DC_clicked)
        self.treeWidget_GCov.itemClicked.connect(self.on_GCov_clicked)

        self.described_cov_gmls_dict = {}

#---------------
        # remove all 'keys' which are set to 'None' from the request-parameter dictionary
    def clear_req_params(self, req_params):

        for k, v in list(req_params.items()):
            if v is None:
                req_params.pop(k)
        return req_params



## ====== Beginning Server Tab-section ======

#---------------
        # add a new server to the list
    def newServer(self):
        global config

        flags = Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint
        dlgNew = qgsnewhttpconnectionbase(self, flags, toEdit=False, choice='')
        dlgNew.exec_()
        self.btnConnectServer_Serv.setFocus(True)

        if dlgNew.idx_sel != '':
            self.cmbConnections_Serv.setCurrentIndex(int(dlgNew.idx_sel))


#---------------
        # read the selected server/url params
    def get_serv_url(self):
        global serv

        sel_serv = self.cmbConnections_Serv.currentText()
        idx = serv.index(sel_serv)
        sel_url = config.srv_list['servers'][idx][1]
        return sel_serv, sel_url


#---------------
        # modify a server entry
    def editServer(self):
        global config

        flags = Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint

        idx = self.cmbConnections_Serv.currentIndex()
        if idx < 0:
            warning_msg("There is no server configuration to edit")
            return

        select_serv = config.srv_list['servers'][idx]
        print("Editing: ", idx, " -- ", select_serv, " -- Check: ", serv[idx])

        dlgEdit = qgsnewhttpconnectionbase(self, flags, toEdit=True, choice=idx)
        dlgEdit.txt_NewSrvName.setText(select_serv[0])
        dlgEdit.txt_NewSrvUrl.setText(select_serv[1])
        dlgEdit.exec_()
        self.btnConnectServer_Serv.setFocus(True)
        self.cmbConnections_Serv.setCurrentIndex(int(idx))

#---------------
        # delete a server entry
    def deleteServer(self):
        global config

        idx = self.cmbConnections_Serv.currentIndex()
        if len(config.srv_list['servers']) == 0:
            warning_msg("There is no server configuration to delete")
            return

        config.srv_list['servers'].pop(idx)

        self.write_srv_list()
        self.updateServerListing()
        self.btnConnectServer_Serv.setFocus(True)

#---------------
        #sort the server list alphabetically
    def sortServerListing(self):

        config.srv_list = config.read_srv_list()
        config.srv_list['servers'].sort()

        self.write_srv_list()
        self.updateServerListing()
        self.btnConnectServer_Serv.setFocus(True)

#---------------
        # update the server-listing shown in the selectionBar
    def updateServerListing(self):
        global serv
        global config

        serv = []
        config.srv_list = config.read_srv_list()
        idx = self.cmbConnections_Serv.currentIndex()

        for ii in range(len(config.srv_list['servers'])):
            serv.append(config.srv_list['servers'][ii][0][:])

        self.cmbConnections_Serv.clear()
        self.cmbConnections_Serv.addItems(serv)

#---------------
       # write the sever names/urls to a file
    @mouse_busy
    def write_srv_list(self):

        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        outsrvlst = os.path.join(plugin_dir, 'config_srvlist.pkl')
        fo = open(outsrvlst, 'wb')
        pickle.dump(config.srv_list, fo, 0)
        fo.close()

#---------------
        # import WCS Names & Urls from the antive Qgis-settings location
    @mouse_busy
    def importQgis_ServList(self, *args):
        global config
        from qgis.PyQt.QtCore import QSettings

        qgs_settings = QSettings(QSettings.NativeFormat, QSettings.UserScope, 'QGIS', 'QGIS2')

        qgis_wcs_urls = []
        for elem in qgs_settings.allKeys():
            if elem.startswith('Qgis/connections-wcs') and elem.endswith('url'):
                print('Importing WCS-Url: ', str.rsplit(str(elem),'/',2)[-2], qgs_settings.value(elem))
                qgis_wcs_urls.append([str.rsplit(str(elem),'/',2)[-2], str(qgs_settings.value(elem))])

            # append qgis_wcs_urls to the QgsWcsClient2 plugin settings
        config.srv_list = config.read_srv_list()
        for elem in qgis_wcs_urls:
            config.srv_list['servers'].append((str(elem[0]), elem[1]))

            # write the imported settings to the QgsWcsClient2 plugin settings file
        self.write_srv_list()
        self.updateServerListing()
        self.btnConnectServer_Serv.setFocus(True)


#---------------
        # get the path where the downloaded datasets shall be stored
    @mouse_busy
    def get_outputLoc(self, *args):
        global req_outputLoc

        start_dir = os.getenv("HOME")
        req_outputLoc = QFileDialog.getExistingDirectory(self, "Select Output Path", start_dir)
        if len(req_outputLoc) > 0:
            if not req_outputLoc.endswith(os.sep):
                req_outputLoc = req_outputLoc+os.sep
            self.lineEdit_Serv_OutputLoc.setText(str(req_outputLoc))


#---------------
        # check if the url exist and if we get a respond to a simple OWS request
    @mouse_busy
    def connectServer(self, *args):
        global config
        global serv

        FGCa_sect = False
        selected_serv, selected_url = self.get_serv_url()
        print('You choose: ', selected_serv, "URL:", selected_url)

        self.username = self.textbox_username.text().strip()
        self.password = self.textbox_password.text().strip()

        if self.tab_GCa.isEnabled():
            self.tab_GCa.setEnabled(False)
        if self.tab_DC.isEnabled():
            self.tab_DC.setEnabled(False)
        if self.tab_GCov.isEnabled():
            self.tab_GCov.setEnabled(False)
        if self.checkBox_GCaFull.isChecked():
            self.checkBox_GCaFull.setChecked(False)

        url_base = selected_url
            # request only  &sections=ServiceMetadata -- this makes if faster (especially on large sites),
            # but some Servers don't provide/accept it, so there is a fallback implemented
        url_ext = "?service=WCS&request=GetCapabilities"
        myUrl = url_base + url_ext

        msg = "Your choice:    "+selected_serv+"\n"
        msg = msg+"URL:                   "+selected_url+"\n"

        srv_valid = QUrl(myUrl).isValid()
        if srv_valid is True:
            msg = msg+"Server address is valid \n"
            msg = msg+"Now testing the connection and response.....\n "
            msg = msg+"       this may take some time (depending on the server and the volume of its offering)\n"
            self.textBrowser_Serv.setText(msg)

        # self.progress_dialog.done(QDialog.Accepted)
        # self.progress_dialog.cancel()
        # self.progress_dialog.show()

        #after changing a server connection --> reset all fields (at least the combo-boxes)
        self.reset_comboboxes()

        req_qgsmng = QNetworkAccessManager(self)

        # start the download
        response = download_url(req_qgsmng, myUrl, None, None, self.username, self.password)

        # check if response is valid and useful, else try the fallback or issue an error
        error = True
        if response[0] is not True:
            msg = msg+"Response:    An Error occurred: --> "+str(response[1])+"\n HTTP-Code received: "+str(response[0])+"\n"
        elif response[0] is True and ((type(response[2]) is str or type(response[2]) is str) and response[2].startswith('Redirection-URL:')):
            msg = msg+"\n\t**** ATTENTION! ****\nThe server you selected:\n\t"+selected_serv +"\nresponded with a:\n\t"+response[2]+"\n"
            msg = msg+"Please VERIFY(!) URL and change your Server-List accordingly."
        elif response[0] is True and ((response[2] is not None or len(response[2]) == 0)):
            # No error from server
            msg = self.eval_response(response, msg)
            error = False
        else:
            msg = msg+"Response:    An Error occurred: --> "+str(response[1])+"\n HTTP-Code received: "+str(response[0])+"\n"

        if error is True and (self.username != '' and self.password != ''):
            msg += "Hint: make sure provided username and password are correct for the requested server."

        # self.progress_dialog.close()
        self.textBrowser_Serv.setText(msg)

        self.checkBox_GCaDaSerSum.setChecked(False)
        self.checkBox_GCaCovSum.setChecked(False)


#---------------
        # reset content of combo-boxes and tree-widgets
    def reset_comboboxes(self):
        global config

        self.treeWidget_GCa.clear()
        self.treeWidget_DC.clear()
        self.treeWidget_GCov.clear()

        self.comboBox_GCovInterpol.clear()

        for elem in range(0, 3):
            self.comboBox_GCovInterpol.addItem(_fromUtf8(""))
            self.comboBox_GCovInterpol.setItemText(elem, _translate("QgsWcsClient2", config.default_interpol[elem], None))


#---------------
        #   evaluate a valid response and enable settings in the tabs
    def eval_response(self, response, msg):

        msg = msg+"Response:    Server OK\n"
        ret_msg = self.parse_first_xml_when_connecting_server(response[2])
        if ret_msg is not None:
            msg = msg + "\n"+ret_msg
        self.treeWidget_GCa.clear()
        self.treeWidget_DC.clear()
        self.treeWidget_GCov.clear()

 #       self.progress_dialog.close()

            # all tabs (except Server/Help/About) are disabled until server connection is OK
            # once server connection is verifyed, activate all other tabs
        if not self.tab_GCa.isEnabled():
            self.tab_GCa.setEnabled(True)
        if not self.tab_DC.isEnabled():
            self.tab_DC.setEnabled(True)
        if not self.tab_GCov.isEnabled():
            self.tab_GCov.setEnabled(True)

        if not self.checkBox_GCa_ActiveDate.isEnabled():
            self.checkBox_GCa_ActiveDate.setEnabled(True)

        if self.radioButton_GCovOutputCRS.isChecked():
            self.radioButton_GCovOutputCRS.setChecked(False)
        if not self.radioButton_GCovOutputCRSOrig.isChecked():
            self.radioButton_GCovOutputCRSOrig.setChecked(True)

        return msg


#---------------
        # get a mapping of the namespaces
    def get_namespace(self, result_xml):
        my_nsp=result_xml.getroot().nsmap
        return my_nsp

#---------------
        # get a listing of interpolation methods offered
    def getlist_interpol(self, dom):
        supported_interpolations = dom["Capabilities"]["ServiceMetadata"]["Extension"]["InterpolationMetadata"]["InterpolationSupported"]
        results = []
        for str in supported_interpolations:
            # e.g. near
            shorthand_interpolation = str.split("/")[-1]
            results.append(shorthand_interpolation)

        return results

#---------------
        # get a listing of fromats offered
    def getlist_formats(self, dom):
        results = dom["Capabilities"]["ServiceMetadata"]["formatSupported"]
        return results

#---------------
        # parse the response issued during "Server Connect" and set some parameters
    def parse_first_xml_when_connecting_server(self, in_xml):
        global offered_version
        global config
        global use_wcs_GCo_call
        use_wcs_GCo_call = 0
        join_xml = b''.join(in_xml)

        dom = self.element_to_dict(ET.fromstring(join_xml))
        offered_version = dom["Capabilities"]["@version"]

        print('WCS-Version: ', offered_version)

            # since this is for plugin WCS >2.0 and EO-WCS, we skip the WCS 1.x and issue an error
        if offered_version.startswith('1'):
            msg = "WARNING: \nThe selected Site doesn't support WCS 2.0  or above. \n\n"
            msg = msg+"The server responded with supported version:    "+ offered_version +"\n"
            msg = msg+"    (Hint: try to use the QGis internal WCS for this site)"
            self.progress_dialog.close()
            warning_msg(msg)
            return msg

        interpolations = self.getlist_interpol(dom)
        outformats = self.getlist_formats(dom)

        self.comboBox_GCovInterpol.clear()
        for i, interpolation in enumerate(interpolations):
            self.comboBox_GCovInterpol.addItem(_fromUtf8(""))
            self.comboBox_GCovInterpol.setItemText(i, _translate("QgsWcsClient2", interpolation, None))

        self.comboBox_GCOvOutFormat.clear()
        for i, format in enumerate(outformats):
            self.comboBox_GCOvOutFormat.addItem(_fromUtf8(""))
            self.comboBox_GCOvOutFormat.setItemText(i, _translate("QgsWcsClient2", format, None))

        # Default set output file to tiff file, so it can load to QGIS map
        self.comboBox_GCOvOutFormat.setCurrentText("image/tiff")


## ====== End of Server Tab-section ======


#---------------
    @mouse_busy
    def exeGetCapabilities(self, *args):
        """
            read-out params from the GetCapabilities Tab, execute the request and show results
        """
        global cov_ids
        global dss_ids
        global req_outputLoc

        self.treeWidget_GCa.clear()
        req_sections = []
        req_full_GCa = False
        req_updateDate = ''
        selected_serv, selected_url = self.get_serv_url()

        if self.checkBox_GCaAll.isChecked():
            req_sections.append("All")
        if self.checkBox_GCaDaSerSum.isChecked():
            req_sections.append("DatasetSeriesSummary")
        if self.checkBox_GCaCovSum.isChecked():
            req_sections.append("CoverageSummary")
        if self.checkBox_GCaServId.isChecked():
            req_sections.append("ServiceIdentification")
        if self.checkBox_GCaServProv.isChecked():
            req_sections.append("ServiceProvider")
        if self.checkBox_GCaServMeta.isChecked():
            req_sections.append("ServiceMetadata")
        if self.checkBox_GCaOpMeta.isChecked():
            req_sections.append("OperationsMetadata")
        if self.checkBox_GCaCont.isChecked():
            req_sections.append("Content")
        if self.checkBox_GCaLang.isChecked():
            req_sections.append("Languages")
        if self.checkBox_GCaFull.isChecked():
            req_full_GCa = True

        req_outputLoc = self.lineEdit_Serv_OutputLoc.text()

        if self.dateEdit_GCaDocUpdate.isEnabled():
            req_updateDate = self.dateEdit_GCaDocUpdate.text()
        else:
            req_updateDate = None

        req_sections = ','.join(req_sections)
        if len(req_sections) == 0:
            req_sections = None

            # basic request setting
        req_params = {'request': 'GetCapabilities',
            'server_url': selected_url,
            'updateSequence': req_updateDate,
            'sections' : req_sections}

        req_params = self.clear_req_params(req_params)

            # issue the WCS request
        GCa_result = self.myWCS.GetCapabilities(req_params, self.username, self.password)
        if  type(GCa_result) is list and GCa_result[0] == 'ERROR':
            self.textBrowser_Serv.setText(GCa_result[0]+'\n'+GCa_result[1].decode()+'\n    HINT:  Select only the "All" setting or select none')
            warning_msg(GCa_result[0]+'\n'+GCa_result[1].decode()+'\n    HINT:  Select only the All setting or select none')
            return


        if req_full_GCa is False:
                # parse the results and place them in the crespective widgets
            # try:
            cov_ids, axis_labels, cov_lcorns, cov_ucorns = self.parse_get_capabilities_xml(GCa_result)
            # except TypeError:
                # self.textBrowser_Serv.setText("No usable results received"+'\n    HINT:  Select only the "All" setting or select none')
                # warning_msg("No usable results received"+'\n    HINT:  Select only the All setting or select none')
                # return

    # TODO -- add the coverage extension (BoundingBox) information to the respective Tabs
            if len(cov_ids) > 0:
                for i in range(0, len(cov_ids)):
                    inlist = (cov_ids[i], axis_labels[i], cov_lcorns[i], cov_ucorns[i])
                    QtWidgets.QTreeWidgetItem(self.treeWidget_GCa, inlist)

            self.treeWidget_GCa.resizeColumnToContents(0)
        else:
            myDisplay_txt = display_txt(self)
            myDisplay_txt.textBrowser_Disp.setText(GCa_result.decode())
            myDisplay_txt.show()
            if self.checkBox_GCaFull.isChecked():
                self.checkBox_GCaFull.setChecked(False)

        QApplication.changeOverrideCursor(Qt.ArrowCursor)

#---------------
        # GetCapabilities button
    def on_GCa_clicked(self):
        global cov_ids
        global dss_ids

        sel_GCa_items = self.treeWidget_GCa.selectedItems()
        self.treeWidget_DC.clear()
        self.treeWidget_GCov.clear()

        #  place selected items also in the DescribeCoverage, GetCoverage Tab widgets
        for elem in sel_GCa_items:
          #                           covID          BeginTime       EndTime            UpperCorner      LowerCorner      [C]/[S]
            print('Selected Item: ', elem.data(0, 0), elem.data(1, 0), elem.data(2, 0), elem.data(3, 0), elem.data(4, 0), elem.data(5, 0))
            if elem.data(0, 0) in cov_ids:
                item = QtWidgets.QTreeWidgetItem(self.treeWidget_DC, (elem.data(0, 0), ))
                item2 = QtWidgets.QTreeWidgetItem(self.treeWidget_GCov, (elem.data(0, 0), ))
            elif elem.data(0, 0) in dss_ids:
                item1 = QtWidgets.QTreeWidgetItem(self.treeWidget_DCS, (elem.data(0, 0), elem.data(1, 0), elem.data(2, 0), elem.data(3, 0), elem.data(4, 0)))

        self.treeWidget_DC.resizeColumnToContents(0)
        self.treeWidget_GCov.resizeColumnToContents(0)

        self.treeWidget_DC.resizeColumnToContents(0)
        self.treeWidget_GCov.resizeColumnToContents(0)


#---------------
        # updateDate field
    def updateDateChanged(self):

        if self.dateEdit_GCaDocUpdate.isEnabled():
            self.dateEdit_GCaDocUpdate.setEnabled(False)
        else:
            self.dateEdit_GCaDocUpdate.setEnabled(True)


#---------------
        # parse GetCapabilities XML-response
    def parse_get_capabilities_xml(self, GCa_result):

        dom = self.element_to_dict(ET.fromstring(GCa_result))

        coverage_summaries = dom["Capabilities"]["Contents"]["CoverageSummary"]
        if len(coverage_summaries) == 0:
            return

        coverage_ids = []
        axis_labels = []
        lower_corners = []
        upper_corners = []

        for i in range(0, len(coverage_summaries)):
            coverage_id = dom["Capabilities"]["Contents"]["CoverageSummary"][i]["CoverageId"]
            lower_corner = dom["Capabilities"]["Contents"]["CoverageSummary"][i]["BoundingBox"]["LowerCorner"]
            upper_corner = dom["Capabilities"]["Contents"]["CoverageSummary"][i]["BoundingBox"]["UpperCorner"]

            coverage_ids.append(coverage_id)
            lower_corners.append(lower_corner)
            upper_corners.append(upper_corner)

            coverage = dom["Capabilities"]["Contents"]["CoverageSummary"][i]
            if "AdditionalParameters" in coverage:
                additional_parameters_dict = coverage["AdditionalParameters"]

                for parameter_dict in additional_parameters_dict["AdditionalParameter"]:
                    if parameter_dict["Name"] == "axisList":
                        axis_labels.append(parameter_dict["Value"])
                        break

        return coverage_ids, axis_labels, lower_corners, upper_corners


## ====== End of GetCapabilities section ======


## ====== Beginning DescribeCoverage section ======
        # read-out the DescribeCoverage Tab, execute a DescribeCoverage request and display response
        # in a general purpose window
    @mouse_busy
    def exeDescribeCoverage(self, show_dialog=True):
        global selected_covid
        global offered_crs
        global offered_version

        selected_serv, selected_url = self.get_serv_url()

        try:
                # a basic DescribeCoverage request
            req_params = {'version': offered_version,
                'request': 'DescribeCoverage',
                'server_url':  selected_url,
                'coverageID':  selected_covid }
        except NameError:
            msg = "Error:    You need to select a CoverageID first!\n   (see also GetCapabilities TAB)"
            warning_msg(msg)
            return


        req_params = self.clear_req_params(req_params)
        DC_result = self.myWCS.DescribeCoverage(req_params, self.username, self.password)

        if DC_result[0] == "ERROR":
            msg = f"Failed to describe coverage '{selected_covid}'. Reason: " + DC_result[1]
            warning_msg(msg)
            return

        gml = DC_result.decode()
        if self.described_cov_gmls_dict is None:
            self.described_cov_gmls_dict = {}
        else:
            self.described_cov_gmls_dict[selected_covid] = gml

        if show_dialog:
            # open a new window to display the returned DescribeCoverage-Response XMl
            myDisplay_txt = display_txt(self)
            myDisplay_txt.textBrowser_Disp.setText(gml)
            myDisplay_txt.show()

        QApplication.changeOverrideCursor(Qt.ArrowCursor)


#---------------
        # the DescribeCoverage Button
    def on_DC_clicked(self):
        global selected_covid

        sel_DC_items = self.treeWidget_DC.selectedItems()
        selected_covid = sel_DC_items[0].data(0, 0)


#---------------

## ====== End of DescribeCoverage section ======

## ====== Beginning GetCoverage section ======
        # read-out the GetCoverage Tab and execute the GetCoverage request
    @mouse_busy
    def exeGetCoverage(self, *args):
        global selected_gcovid
        global req_outputLoc
        global offered_crs
        global offered_version
        global use_wcs_GCo_call

        subsets_requests_params_str = self.__get_axes_subsets_from_group_box(self.groupBox_get_cov_axes_subsets.layout())

        selected_serv, selected_url = self.get_serv_url()

        req_format = self.comboBox_GCOvOutFormat.currentText()
        req_interpolation = self.comboBox_GCovInterpol.currentText()

        if req_interpolation.encode().startswith(b"nearest"):
            req_interpolation = None

        req_rangesubset = self.lineEdit_GCovBands.text()
        if len(req_rangesubset) == 0:
            req_rangesubset = None

            # check if a coverage has been selected
        try:
            selected_gcovid
        except NameError:
            msg = "Error:   You need to select one or more Coverage(s) first.\n(see the GetCapabilities & DescribeCoverage tabs"
            warning_msg(msg)
            return

        output_crs = None
        if self.radioButton_GCovOutputCRS.isChecked():
            epsg_no = self.lineEdit_GCovOutputEPSG.text()
            if not str(epsg_no).isdigit():
                warning_msg("EPSG code must be positive number, e.g. 3857")
                return

            output_crs = "https://opengis.net/def/crs/EPSG/0/" + epsg_no

        if not "req_outputLoc" in globals():
            msg = "Error: For downloading coverages you need to supply a Local Storage Path --> see TAB Server / Storage"
            QMessageBox.critical(self, "Error", msg, QMessageBox.Ok)
                # put focus on Server/STorage Tab to allow provision of Output Location
            self.tabWidget_EOWcsClient2.setCurrentIndex(0)
            self.get_outputLoc()
        elif len(req_outputLoc) == 0:
            self.tabWidget_EOWcsClient2.setCurrentIndex(0)
            self.get_outputLoc()
        else:
            req_outputLoc = self.lineEdit_Serv_OutputLoc.text()


        try:
                # a basic GetCoverage request
            for gcov_elem in selected_gcovid:
                req_params = {'version': offered_version,
                    'request': 'GetCoverage',
                    'server_url': selected_url,
                    'coverageID': gcov_elem,
                    'format':  req_format,
                    'rangesubset': req_rangesubset,
                    'interpolation': req_interpolation,
                    'outputcrs': output_crs,
                    'output': req_outputLoc}

                if req_params['format'].startswith('application/gml'):
                    if req_params['format'].count('+') != -1:
                        req_params['format'] = req_params['format'].replace('+','%2B')

                    req_params['mediatype'] = 'multipart/related'


                try:
                        # send the request
                    req_params = self.clear_req_params(req_params)

                    GCov_result, outfile = self.myWCS.GetCoverage(req_params, self.username, self.password, subsets_requests_params_str)
                    print("GCov_result / HTTP-Code: ", GCov_result)
                except IOError as TypeError:
                    return

                if GCov_result == 200:
                    #Register the downloaded datsets with QGis MapCanvas -> load and show
                    if req_format.startswith("image/") or "netcdf" in req_format:
                        self.add_to_map(outfile)
                        warning_msg("Added the downloaded result as a image layer on QGIS successfully.")
                    else:
                        warning_msg(f"Output format is not image/netCDF format to display on QGIS. Check downloaded result in this file: \n\n '{outfile}'")

                    # reset the cursur
                    QApplication.changeOverrideCursor(Qt.ArrowCursor)
                else:
                    msg = f"Failed to process request from server. Check error message in this downloaded file: \n\n '{outfile}'"
                    warning_msg(msg)

        except NameError as EEE:
            print('NameError: ', EEE)
            msg = "Error:    You need to select one or more CoverageIDs first!\n "
            warning_msg(msg)
            return


#---------------

    @mouse_busy
    def handle_get_cov_tree_item_clicked(self, item, column):
        """
        When clicking on an item on GetCoverage tree, then it should send a DescribeCoverage request to server
        and fetch the axes from that endpoint
        """
        global selected_covid
        selected_covid = item.text(0)
        print(f"Clicked on item {selected_covid}")

        if selected_covid not in self.described_cov_gmls_dict:
            # If the coverage was not described -> show dialog with GML so user can have a look then cache it and loads the axes subsets
            self.exeDescribeCoverage(True)
        else:
            # If the coverage was described -> do not show the dialog with GML
            self.exeDescribeCoverage(False)

        axes_list = []
        try:
            gml = self.described_cov_gmls_dict[selected_covid]
            dom = self.element_to_dict(ET.fromstring(gml))

            axes_labels = dom["CoverageDescriptions"]["CoverageDescription"]["boundedBy"]["Envelope"]["@axisLabels"].split(" ")
            lower_bounds = dom["CoverageDescriptions"]["CoverageDescription"]["boundedBy"]["Envelope"]["lowerCorner"].split(" ")
            upper_bounds = dom["CoverageDescriptions"]["CoverageDescription"]["boundedBy"]["Envelope"]["upperCorner"].split(" ")

            for i in range(0, len(axes_labels)):
                axes_list.append({
                    "axis_label": axes_labels[i],
                    "lower_bound": lower_bounds[i],
                    "upper_bound": upper_bounds[i]
                })

        except Exception as ex:
            warning_msg(f"Failed to parse GML result of DescribeCoverage request. Reason: {ex}")
            return

        # remove any contents on the group box
        self.clear_widget_content(self.groupBox_get_cov_axes_subsets)

        # then, build the new axes subsets layout based on the parsed axes
        self.__get_cov_build_axes_subsets_layout(axes_list)

        QApplication.processEvents()

    def __get_cov_build_axes_subsets_layout(self, axes_list):
        """
        When a coverage is selected in TreeView of GetCoverage tab, then, it needs to have new layout with textboxes,
        radio buttons for the axes of this coverage
        """
        self.get_cov_axes_subsets_slicing_radios_buttons_rows = []
        layout_tmp = QtWidgets.QVBoxLayout()

        for i, axis in enumerate(axes_list):
            axis_label = axis["axis_label"]
            lower_bound = str(axis["lower_bound"])
            upper_bound = str(axis["upper_bound"])

            # first row (axis label)
            row = QtWidgets.QHBoxLayout()
            label_axis = QtWidgets.QLabel(f"Dim{i + 1}: axis {axis_label} with extent:")
            row.addWidget(label_axis)
            layout_tmp.addLayout(row)

            # Create a new QButtonGroup for each row to ensure the radios in the row are exclusive to each other
            # NOTE:  without container for QButtonGroup() like this
            # then it has issue for multiple buttons behaving as if they're in the same group (!)
            radio_buttons_group = QtWidgets.QButtonGroup(self)
            radio_buttons_group.setExclusive(False)  # Only one button can be checked in the group

            # second row (lower bound)
            row = QtWidgets.QHBoxLayout()

            label_axis = QtWidgets.QLabel("Lower bound:")
            textbox_lower = QtWidgets.QLineEdit()
            textbox_lower.setProperty("id", "lowerbound_" + axis_label)
            textbox_lower.setText(lower_bound)

            lower_bound_radio = QtWidgets.QRadioButton("Slice")
            lower_bound_radio.setProperty("id", "lowerbound_" + axis_label)
            lower_bound_radio.setToolTip("Check button to slice on this axis' lower bound")
            radio_buttons_group.addButton(lower_bound_radio)  # Add to this row's group

            row.addWidget(label_axis)
            row.addWidget(textbox_lower)
            row.addWidget(lower_bound_radio)

            layout_tmp.addLayout(row)

            # third row (upper bound)
            row = QtWidgets.QHBoxLayout()

            label_dash = QtWidgets.QLabel("Upper bound:")
            textbox_upper = QtWidgets.QLineEdit()
            textbox_upper.setProperty("id", "upperbound_" + axis_label)
            textbox_upper.setText(upper_bound)

            upper_bound_radio = QtWidgets.QRadioButton("Slice")
            upper_bound_radio.setProperty("id", "upperbound_" + axis_label)
            upper_bound_radio.setToolTip("Check button to slice on this axis' upper bound")
            radio_buttons_group.addButton(upper_bound_radio)  # Add to the same row's group

            row.addWidget(label_dash)
            row.addWidget(textbox_upper)
            row.addWidget(upper_bound_radio)

            layout_tmp.addLayout(row)

            self.get_cov_axes_subsets_slicing_radios_buttons_rows.append((lower_bound_radio, upper_bound_radio))

            # # Connect the toggled signal to the toggle_radio function for both radio buttons
            lower_bound_radio.toggled.connect(
                lambda checked, rb=lower_bound_radio, r_index=i: self.__get_cov_toggle_axes_slice_radio(checked, rb,
                                                                                                        r_index))
            upper_bound_radio.toggled.connect(
                lambda checked, rb=upper_bound_radio, r_index=i: self.__get_cov_toggle_axes_slice_radio(checked, rb,
                                                                                                        r_index))

            # add the ruler to separate axes
            if i < len(axes_list) - 1:
                line = QtWidgets.QFrame()
                line.setFrameShape(QtWidgets.QFrame.HLine)
                line.setFrameShadow(QtWidgets.QFrame.Sunken)

                layout_tmp.addWidget(line)

        # Then add all generated axes subsets to the layout
        self.groupBox_get_cov_axes_subsets.setLayout(layout_tmp)

    def __get_axes_subsets_from_group_box(self, input_layout):
        """
        Iterate all children row layouts of the input group box, then to select axes subset:
        - If no radio buttons is selected -> trim for axis
        - If one of radio button is selected -> slice for the axis by the bound where radio button is checked
        return e.g. subset=Lat(30:50)&subset=lon(35.5)
        """
        axes_subsets_dict = {}

        # Recursively iterate over the items in the layout to find all text boxes and checked check boxes
        text_boxes, radio_buttons = self.__get_all_textboxes_checked_radio_buttons_from_group_box(input_layout)
        # NOTE: need to loop with text boxes first to get all lower and upper bounds, then loop to radio buttons
        # to know which axis should be sliced when a radio button checked (!)
        collected_widgets = text_boxes + radio_buttons

        for widget in collected_widgets:
            # e.g. lowerbound_lat
            id = widget.property("id")
            parts = id.split("_")
            # e.g. lower_bound
            bound_type = parts[0]
            # e.g. lat
            axis_label = parts[1]
            if axis_label not in axes_subsets_dict:
                axes_subsets_dict[axis_label] = {
                    "lowerbound": None,
                    "upperbound": None
                }

            if isinstance(widget, QLineEdit):
                value = widget.text()
                axes_subsets_dict[axis_label][bound_type] = value
            elif isinstance(widget, QRadioButton):
                # A slice radio button is checked (e.g. lower_bound is sliced), then set upper_bound is None
                if bound_type == "lowerbound":
                    axes_subsets_dict[axis_label]["upperbound"] = None
                else:
                    axes_subsets_dict[axis_label]["lowerbound"] = None

        axes_subsets_requests_params_str = ""
        for axis_label, obj in axes_subsets_dict.items():

            subset_tmp = ""
            if obj["lowerbound"] is None:
                subset_tmp = obj["upperbound"]
            elif obj["upperbound"] is None:
                subset_tmp = obj["lowerbound"]
            else:
                subset_tmp = obj["lowerbound"] + ":" + obj["upperbound"]

            # e.g. subset=Lat(30:50)&subset=lon(35.5)
            axes_subsets_requests_params_str += "SUBSET=" + axis_label + "(" + subset_tmp + ")&"

        from urllib.parse import quote
        return quote(axes_subsets_requests_params_str)

    def __get_all_textboxes_checked_radio_buttons_from_group_box(self, input_layout):
        """
        Get all text boxes and any checked radio buttons in axes subsets group box to build the subsets parameter for
        WCS GetCoverage request
        """
        collected_widgets_tuples = []
        text_boxes = []
        radio_buttons = []

        # Recursively iterate over the items in the layout
        for i in range(input_layout.count()):
            item = input_layout.itemAt(i)

            if item.widget():
                # If it's a QLineEdit, add it to the list
                if isinstance(item.widget(), QLineEdit):
                    text_boxes.append(item.widget())

                    # Check for next sibling if it exists
                    next_item = input_layout.itemAt(i + 1)
                    if next_item and isinstance(next_item.widget(), QRadioButton):
                        # If the next item is a widget, add it (if needed)
                        next_widget = next_item.widget()
                        if next_widget.isChecked():
                            radio_buttons.append(next_widget)
            elif item.layout():
                # If the item is a layout, recurse into it
                text_boxes_tmp, radio_buttons_tmp = self.__get_all_textboxes_checked_radio_buttons_from_group_box(item.layout())
                text_boxes.extend(text_boxes_tmp)
                radio_buttons.extend(radio_buttons_tmp)

        return (text_boxes, radio_buttons)

    def __get_cov_toggle_axes_slice_radio(self, checked, radio_button, row_index):
        """ Custom function to toggle radio button and allow unchecking """
        if checked:
            # If radio1 is checked, uncheck radio2 in the same row, and vice versa
            if radio_button == self.get_cov_axes_subsets_slicing_radios_buttons_rows[row_index][0]:  # radio_lower_bound
                self.get_cov_axes_subsets_slicing_radios_buttons_rows[row_index][1].setChecked(False)
            else:  # radio_upper_bound
                self.get_cov_axes_subsets_slicing_radios_buttons_rows[row_index][0].setChecked(False)

        # GetCoverage Button
    def on_GCov_clicked(self):
        global selected_gcovid

        selected_gcovid = []
        sel_GCov_items = self.treeWidget_GCov.selectedItems()
        for elem in sel_GCov_items:
            selected_gcovid.append(elem.data(0, 0))
            print("Selected CoverageID: ", selected_gcovid)
                # to allow a DescribeCoverage request for a Coverage comeing from a DescribeEOCoverageSet request
                # we add the selected Coverage to the DescribeCoverage window
                # to avoid duplicat entries we have to check if the entry already exists
            DC_treeContent = self.treeWidget_DC.findItems(elem.data(0, 0), Qt.MatchStartsWith, 0)
            if len(DC_treeContent) == 0:
                item = QtWidgets.QTreeWidgetItem(self.treeWidget_DC, (elem.data(0, 0),))


#---------------
        # activate the SubsetCRS setting and field
    def enableGCov_SubCRS(self, *args):
        if self.radioButton_GCovOutputCRS.isChecked():
            self.radioButton_GCovOutputCRSOrig.setChecked(False)
            self.lineEdit_GCovOutputEPSG.setEnabled(True)


#---------------
        # activate the OriginalCRS setting
    def enableGCov_SubOrig(self, *args):
        if self.radioButton_GCovOutputCRSOrig.isChecked():
            self.radioButton_GCovOutputCRS.setChecked(False)
            self.lineEdit_GCovOutputEPSG.setEnabled(False)


#---------------
        # enabele scaling X-Size
    def enableGCov_XSize(self, *args):
        if self.radioButton_GCovXSize.isChecked():
            self.radioButton_GCov_OutSizeOrig.setChecked(False)


#---------------
        # enabele scaling X-Resolution
    def enableGCov_XResolution(self, *args):
        if self.radioButton_GCovXRes.isChecked():
            self.radioButton_GCov_OutSizeOrig.setChecked(False)


#---------------
        # enabele scaling Y-Size
    def enableGCov_YSize(self, *args):
        if self.radioButton_GCovYSize.isChecked():
            self.radioButton_GCov_OutSizeOrig.setChecked(False)

#---------------
        # enabele scaling Y-Resolution
    def enableGCov_YResolution(self, *args):
        if self.radioButton_GCovYRes.isChecked():
            self.radioButton_GCov_OutSizeOrig.setChecked(False)

#---------------
        # reset scaling to original size/resolution
    def disableGCov_OutSize(self, *args):
        if self.radioButton_GCov_OutSizeOrig.isChecked():
            self.lineEdit_GCovXAxisLabel.setEnabled(False)
            self.lineEdit_GCovXSize.setEnabled(False)
            self.radioButton_GCovXSize.setChecked(False)
            self.radioButton_GCovXRes.setChecked(False)
            self.lineEdit_GCovYAxisLabel.setEnabled(False)
            self.lineEdit_GCovYSize.setEnabled(False)
            self.radioButton_GCovYSize.setChecked(False)
            self.radioButton_GCovYRes.setChecked(False)

## ====== End of GetCoverage section ======


## ====== Add data to Map Canvas ======
        # read the the downloaded datasets, register them and show them in the QGis MapCanvas
    def add_to_map(self, outfile):
        self.canvas = self.iface.mapCanvas()

        layer_name = os.path.basename(outfile)
        cov_layer = QgsRasterLayer(outfile, layer_name)
        if not cov_layer.isValid():
            warning_msg("Layer failed to load. Reason: " + cov_layer.error().message() )

        QgsProject.instance().addMapLayer(cov_layer)


## ====== End of Add data to Map Canvas ======

    ##################### Utility methods
    def parse_tag_name(self, element: Union[ET.Element, str]) -> str:
        """
        Extract just the tag name of an XML element, removing namespace components.
        Example: "{http://www.example.com}root" -> "root"

        :param element: An XML element from which to extract the tag name.
        :return: The tag name of the element.
        """
        if isinstance(element, ET.Element):
            element = element.tag
        elif not isinstance(element, str):
            raise RuntimeError(f"Cannot parse tag name, but expected xml.etree.ElementTree.Element"
                                     f" or string argument, but got {element.__class__}.")
        return element.split('}')[-1]

    def element_to_dict(self, t: ET.Element) -> dict:
        """
        Convert an XML element into a nested dictionary.

        This function recursively converts an XML element and its children into a
        nested dictionary. The keys of the dictionary are the tag names of the XML
        elements. Attributes of the XML elements are prefixed with '@' in the
        dictionary keys, and text content is stored under a '#text' key.

        :param t: The XML element to convert.
        :return: A nested dictionary representing the structure and content of the XML element.

        :note:
            - Elements with multiple children having the same tag name are converted into lists.
            - Text content is only added to the dictionary if the element has children
              or attributes, to avoid overwriting important data with whitespace.
        """
        tag = self.parse_tag_name(t)
        d = {tag: {} if t.attrib else None}
        children = list(t)
        if children:
            dd = defaultdict(list)
            for dc in map(self.element_to_dict, children):
                for k, v in dc.items():
                    dd[k].append(v)
            d = {tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
        if t.attrib:
            d[tag].update(('@' + self.parse_tag_name(k), v) for k, v in t.attrib.items())
        if t.text:
            text = t.text.strip()
            if children or t.attrib:
                if text:
                    d[tag]['#text'] = text
            else:
                d[tag] = text
        return d

    def clear_widget_content(self, widget):
        layout = widget.layout()
        if layout is not None and not sip.isdeleted(layout):
            self.force_clear_layout_from_layout(layout)

            QWidget().setLayout(layout)  # Detach layout safely
            # Do NOT call layout.deleteLater()

    def force_clear_layout_from_layout(self, layout):
        if layout is None or sip.isdeleted(layout):
            return

        while layout.count():
            item = layout.takeAt(0)
            child_widget = item.widget()
            child_layout = item.layout()

            if child_widget:
                child_widget.setParent(None)
            elif child_layout and not sip.isdeleted(child_layout):
                self.force_clear_layout_from_layout(child_layout)

        # No deleteLater or detachment here
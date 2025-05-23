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
 Function for the Server / Url  setup dialog
"""

import os, pickle
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from qgis.PyQt import QtCore, QtGui
from .ui_qgswcsclient2 import Ui_QgsWcsClient2
from .qgsnewhttpconnectionbase import Ui_qgsnewhttpconnectionbase

# global setttings and saved server list
global config
from . import config

srvlst = []


class qgsnewhttpconnectionbase(QDialog, QObject, Ui_qgsnewhttpconnectionbase):
    MSG_BOX_TITLE = "WCS 2 Client"

    def __init__(self, parent, fl, toEdit, choice):
        QDialog.__init__(self, parent, fl)
        self.toEdit = toEdit
        self.idx_sel = choice
        self.parent = parent
        self.flags = fl
        self.setupUi(self)
        self.txt_NewSrvName.setFocus(True)
        self.setWindowTitle('WCS 2 Client')  # +version())

    def accept(self):
        global config
        srvlst = config.srv_list['servers']
        srv_name = self.txt_NewSrvName.text()
        srv_url = self.txt_NewSrvUrl.text()

        # fix to enable changing of url without changing servername
        if str(self.idx_sel).isdigit():
            if srv_name == srvlst[self.idx_sel][0] and srv_url != srvlst[self.idx_sel][1]:
                srv_name += ' '

            # verify that URL starts with http://
        if not srv_url.startswith("http://") and not srv_url.startswith("https://"):
            msg = "Sorry, you need to supply a 'Server URL' starting with http://  or https://\n"
            self.warning_msg(msg)
            srv_name = self.txt_NewSrvName.text()

        if self.toEdit is False:
            # NEW
            for srv in config.srv_list["servers"]:
                if srv_name == srv[0]:
                    self.warning_msg("Server name already exists, please set another name")
                    return

            srvlst.append([srv_name, srv_url])
            self.idx_sel = len(srvlst) - 1

        if self.toEdit is True:
            # EDIT
            srvlst[self.idx_sel] = [srv_name, srv_url]

        config.srv_list = {'servers': srvlst}
        if (len(srv_name) > 0 and len(srv_url) > 0):
            self.parent.write_srv_list()
            self.parent.updateServerListing()
        else:
            msg = "Sorry, the provided 'Server Name' " + str(
                srv_name) + " or the provided 'Server URL '" + srv_url + " is not valid"
            self.warning_msg(msg)

        self.close()

    def warning_msg(self, msg):
        msgBox = QMessageBox()
        msgBox.setText(msg)
        msgBox.addButton(QPushButton('OK'), QMessageBox.YesRole)
        msgBox.exec_()

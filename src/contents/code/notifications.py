# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
from __future__ import unicode_literals

from PyQt4.Qt import QBitArray, QString, QPixmap

from PyKDE4.kdecore import KGlobal, KComponentData
from PyKDE4.kdeui import KNotification

import os
from shutil import copyfile
# ------------------------------------------------------------------------------


class Notifications(object):

    def __init__(self, appname, source):
        self.appname = appname
        self.source = source
        self.ensure_notifyrc()

    def ensure_notifyrc(self):
        appdir = '{base}/share/apps/{app}/'.format(
            base=KGlobal.dirs().localkdedir(), app=self.appname
        )
        rcpath = os.path.join(
            appdir, '{app}.notifyrc'.format(app=self.appname)
        )

        if os.path.exists(rcpath):
            return

        if not os.path.exists(appdir):
            os.mkdir(appdir)

        copyfile(self.source, rcpath)

    def notify(self, event_name, title, message, timeout=0):
        comp = KComponentData(
            self.appname, self.appname,
            KComponentData.SkipMainComponentRegistration
        )

        KNotification.event(
            event_name,
            title,
            message,
            QPixmap(),
            None,
            KNotification.Persistent,
            comp
        )

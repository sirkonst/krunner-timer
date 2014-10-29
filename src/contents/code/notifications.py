# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
from __future__ import unicode_literals

from PyKDE4.kdecore import KGlobal

import dbus

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
        # Do notify by dbus because KNotification doesn't respect timeout
        _bus_name = 'org.kde.knotify'
        _object_path = '/Notify'
        _interface_name = 'org.kde.KNotify'

        session_bus = dbus.SessionBus()
        obj = session_bus.get_object(_bus_name, _object_path)
        interface = dbus.Interface(obj, _interface_name)
        interface.event(
            event_name, self.appname, [],
            title, message,
            "", "",
            timeout * 1000,
            0
        )

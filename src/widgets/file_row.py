# window.py
#
# Copyright 2024 Nokse22
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import gi
from gi.repository import Adw
from gi.repository import Gtk, Gdk, Gio, GLib, GObject

import os

@Gtk.Template(resource_path='/io/github/nokse22/Exhibit/ui/file_row.ui')
class FileRow(Adw.ActionRow):
    __gtype_name__ = 'FileRow'

    __gsignals__ = {
        'open-file': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'delete-file': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    file_button = Gtk.Template.Child()
    filename_label = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()

    filepath = ""

    def __init__(self):
        super().__init__()

        self.file_button.connect("clicked", self.on_open_clicked)
        self.delete_button.connect("clicked", self.on_delete_clicked)

    def on_open_clicked(self, btn):
        self.emit("open-file")

    def set_filename(self, filepath):
        if filepath == "":
            return

        self.filepath = filepath
        self.filename_label.set_label(os.path.basename(filepath))
        self.filename_label.set_visible(True)
        self.delete_button.set_visible(True)

    def on_delete_clicked(self, btn):
        self.filename_label.set_visible(False)
        self.delete_button.set_visible(False)
        self.emit("delete-file")

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

import f3d
from f3d import *

import math

from ..vector_math import *

up_dirs_vector = {
    "-X": (-1.0, 0.0, 0.0),
    "+X": (1.0, 0.0, 0.0),
    "-Y": (0.0, -1.0, 0.0),
    "+Y": (0.0, 1.0, 0.0),
    "-Z": (0.0, 0.0, -1.0),
    "+Z": (0.0, 0.0, 1.0)
}

@Gtk.Template(resource_path='/io/github/nokse22/Exhibit/ui/f3d_viewer.ui')
class F3DViewer(Gtk.GLArea):
    __gtype_name__ = 'F3DViewer'

    def __init__(self, *args):
        self.set_auto_render(True)
        self.connect("realize", self.on_realize)
        self.connect("render", self.on_render)
        self.connect("resize", self.on_resize)

        self.set_allowed_apis(Gdk.GLAPI.GL)
        # self.set_required_version(1, 0)

        self.prev_pan_offset = 0
        self.drag_prev_offset = (0, 0)
        self.drag_start_angle = 0

        self.always_point_up = True

        self.prev_scale = 1

        self.distance = 0

        self.engine = Engine(Window.EXTERNAL)
        self.loader = self.engine.getLoader()
        self.camera = self.engine.window.getCamera()

        self.engine.autoload_plugins()

        self.settings = {
            "model.scivis.cells": True,
            "model.scivis.array-name": "",
        }

        self.engine.options.update(self.settings)

    def reset_to_bounds(self):
        self.camera.resetToBounds()
        self.get_distance()
        self.queue_render()

    def front_view(self, *args):
        up_v = up_dirs_vector[self.settings["scene.up-direction"]]
        vector = v_mul(tuple([up_v[2], up_v[0], up_v[1]]), 1000)
        self.camera.position = v_add(self.camera.focal_point, vector)
        self.camera.setViewUp(up_dirs_vector[self.settings["scene.up-direction"]])
        self.camera.resetToBounds()
        self.get_distance()
        self.queue_render()

    def right_view(self, *args):
        up_v = up_dirs_vector[self.settings["scene.up-direction"]]
        vector = v_mul(tuple([up_v[1], up_v[2], up_v[0]]), 1000)
        self.camera.position = v_add(self.camera.focal_point, vector)
        self.camera.setViewUp(up_dirs_vector[self.settings["scene.up-direction"]])
        self.camera.resetToBounds()
        self.get_distance()
        self.queue_render()

    def top_view(self, *args):
        up_v = up_dirs_vector[self.settings["scene.up-direction"]]
        vector = v_mul(up_v, 1000)
        self.camera.position = v_add(self.camera.focal_point, vector)
        vector = v_mul(tuple([up_v[1], up_v[2], up_v[0]]), 1000)
        self.camera.setViewUp(vector)
        self.camera.resetToBounds()
        self.get_distance()
        self.queue_render()

    def isometric_view(self, *args):
        up_v = up_dirs_vector[self.settings["scene.up-direction"]]
        vector = v_add(tuple([up_v[2], up_v[0], up_v[1]]), tuple([up_v[1], up_v[2], up_v[0]]))
        self.camera.position = v_mul(v_norm(v_add(vector, up_v)), 1000)
        self.camera.setViewUp(up_dirs_vector[self.settings["scene.up-direction"]])
        self.camera.resetToBounds()
        self.get_distance()
        self.queue_render()

    def update_options(self, options):
        self.engine.options.update(options)
        for key, value in options.items():
            self.settings[key] = value
        self.queue_render()

    def render_image(self):
        self.f3d_viewer.get_context().make_current()
        img = self.engine.window.render_to_image()
        return img

    def has_geometry_loader(self, filepath):
        return self.engine.loader.hasGeometryReader(filepath)

    def has_scene_loader(self, filepath):
        return self.engine.loader.hasSceneReader(filepath)

    def load_geometry(self, filepath):
        self.engine.loader.load_geometry(filepath, True)

    def load_scene(self, filepath):
        self.engine.loader.load_scene(filepath)

    def on_resize(self, gl_area, width, height):
        self.width = width
        self.height = height

    def on_realize(self, area):
        if self.get_context() is None:
            print("Could not create GL context")

    def on_render(self, area, ctx):
        self.get_context().make_current()
        self.engine.window.render()
        return True

    def get_camera_to_focal_distance(self):
        up = up_dirs_vector[self.settings["scene.up-direction"]]
        pos = self.camera.position
        foc = self.camera.focal_point

        pos_proj = v_sub(v_dot_p(pos, v_abs(up)), pos)
        foc_proj = v_sub(v_dot_p(foc, v_abs(up)), foc)

        dist = p_dist(pos_proj, foc_proj)

        pos_height = v_dot_p(pos, v_abs(up))
        foc_height = v_dot_p(foc, v_abs(up))

        diff = v_sub(pos_height, foc_height)

        for number in diff:
            if number != 0:
                return dist, (1 if number > 0 else -1)
        return dist, 1

    def get_gimble_limit(self):
        return self.distance / 10

    def get_distance(self):
        self.distance = p_dist(self.camera.position, (0,0,0))

    def pan(self, x, y, z):
        val = self.distance / 40
        self.camera.pan(x * val, y * val, z * val)
        self.queue_render()

    def rotate_camera(self, direction):
        val = self.distance / 40

        focal_point = self.camera.focal_point

        match direction:
            case "left":
                self.camera.pan(-val, 0, 0)
                self.camera.focal_point = focal_point
            case "right":
                self.camera.pan(val, 0, 0)
                self.camera.focal_point = focal_point
            case "up":
                dist, direction = self.get_camera_to_focal_distance()
                if dist > self.get_gimble_limit() or (dist < self.get_gimble_limit() and direction == -1):
                    self.camera.pan(0, val, 0)
                    self.camera.focal_point = focal_point
            case "down":
                dist, direction = self.get_camera_to_focal_distance()
                if dist > self.get_gimble_limit() or (dist < self.get_gimble_limit() and direction == 1):
                    self.camera.pan(0, -val, 0)
                    self.camera.focal_point = focal_point

        if self.always_point_up:
            up = up_dirs_vector[self.settings["scene.up-direction"]]
            self.camera.setViewUp(up)

        self.queue_render()

    def set_view_up(self, direction):
        self.camera.setViewUp(direction)
        self.queue_render()

    @Gtk.Template.Callback("on_scroll")
    def on_scroll(self, gesture, dx, dy):
        if self.settings["scene.camera.orthographic"]:
            self.camera.zoom(1 - 0.1*dy)
        else:
            self.camera.dolly(1 - 0.1*dy)
        self.get_distance()
        self.queue_render()

    @Gtk.Template.Callback("on_zoom_scale_changed")
    def on_zoom_scale_changed(self, zoom_gesture, scale):
        self.camera.dolly(1 - self.prev_scale + scale)
        self.prev_scale = scale
        self.get_distance()
        self.queue_render()

    @Gtk.Template.Callback("on_drag_update")
    def on_drag_update(self, gesture, x_offset, y_offset):
        if gesture.get_current_button() == 1:
            dist, direction = self.get_camera_to_focal_distance()
            y = -(self.drag_prev_offset[1] - y_offset) * 0.5
            x = (self.drag_prev_offset[0] - x_offset) * 0.5
            if not self.always_point_up:
                self.camera.elevation(y)
                self.camera.azimuth(x)
            else:
                if (dist > self.get_gimble_limit() or (dist < self.get_gimble_limit()) and
                        (direction == 1 and y < 0) or (dist < self.get_gimble_limit() and direction == -1 and y > 0)):
                    self.camera.elevation(y)
                self.camera.azimuth(x)
        elif gesture.get_current_button() == 2:
            self.camera.pan(
                (self.drag_prev_offset[0] - x_offset) * (0.0000001*self.width + 0.001*self.distance),
                -(self.drag_prev_offset[1] - y_offset) * (0.0000001*self.height + 0.001*self.distance),
                0
            )

        if self.always_point_up:
            up = up_dirs_vector[self.settings["scene.up-direction"]]
            self.camera.setViewUp(up)

        self.queue_render()

        self.drag_prev_offset = (x_offset, y_offset)

    @Gtk.Template.Callback("on_drag_end")
    def on_drag_end(self, gesture, *args):
        self.drag_prev_offset = (0, 0)

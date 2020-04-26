#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  main_ui.py
#
#  Copyright 2020 Thomas Castleman <contact@draugeros.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
from __future__ import print_function
from sys import argv, stderr, version_info
from os import getenv, mkdir, path, remove
from time import sleep, time
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from ctypes import cdll, byref, create_string_buffer
from subprocess import check_output, Popen, CalledProcessError

# Make it easier for us to print to stderr
def eprint(*args, **kwargs):
	print(*args, file=stderr, **kwargs)

if (version_info[0] == 2):
	eprint("Please run with Python 3 as Python 2 is End-of-Life.")
	exit(2)

CONFIG_DIR = getenv("HOME") + "/.config/time-tracker"
CONFIG_FILE = CONFIG_DIR + "/time-tracker.conf"
A = -0.4344262295
B = 4.983606557

def pgrep():
	try:
		check_output(["pgrep", "time-tracker"])
		return True
	except CalledProcessError:
		return False

def set_procname(newname):
	libc = cdll.LoadLibrary('libc.so.6')    #Loading a 3rd party library C
	buff = create_string_buffer(len(newname)) #Note: One larger than the name (man prctl says that)
	buff.value = bytes(newname, "utf-8")                 #Null terminated string as it should be
	libc.prctl(15, byref(buff), 0, 0, 0) #Refer to "#define" of "/usr/include/linux/prctl.h" for the misterious value 16 & arg[3..5] are zero as the man page says.


set_procname("timetracker-cfg")
if (pgrep()):
	running = "Stop"
else:
	running = "Start"

class main_ui(Gtk.Window):
	def __init__(self):
		# Initialize the Window
		Gtk.Window.__init__(self, title="Time Tracker")
		self.grid=Gtk.Grid(orientation=Gtk.Orientation.VERTICAL)
		self.page0 = Gtk.Grid(orientation=Gtk.Orientation.VERTICAL)
		self.page1 = Gtk.Grid(orientation=Gtk.Orientation.VERTICAL)
		self.add(self.grid)
		self.set_icon_name("time")
		self.read_settings()
		self.read_logs("clicked")
		self.main(1)

	def reload(self, button):
		self.read_logs("clicked")
		self.main(1)

	def format_time(self, seconds, format_string):
		if (format_string == "s"):
			return "%s seconds" % (round(seconds))
		elif (format_string == "m"):
			minutes = int(seconds / 60)
			if (minutes >= 1):
				seconds = seconds - (minutes * 60)
			else:
				return seconds
			return "%s minutes, %s seconds" % (minutes, round(seconds))
		elif (format_string == "h"):
			minutes = int(seconds / 60)
			if (minutes >= 1):
				seconds = seconds - (minutes * 60)
				if (minutes >= 60):
					hours = int(minutes/60)
					minutes = minutes - (hours * 60)
					return "%s hours, %s minutes, %s seconds" % (hours, minutes, round(seconds))
				else:
					return "%s minutes, %s seconds" % (minutes, round(seconds))
			else:
				return "%s seconds" % (round(seconds))
		elif (format_string == "d"):
			minutes = int(seconds / 60)
			if (minutes >= 1):
				seconds = seconds - (minutes * 60)
				if (minutes >= 60):
					hours = int(minutes/60)
					minutes = minutes - (hours * 60)
					if (hours >= 24):
						days = int(hours / 24)
						hours = hours - (days * 24)
						return "%s days, %s hours, %s minutes, %s seconds" % (days, hours, minutes, round(seconds))
					else:
						return "%s hours, %s minutes, %s seconds" % (hours, minutes, round(seconds))
				else:
					return "%s minutes, %s seconds" % (minutes, round(seconds))
			else:
				return "%s seconds" % (round(seconds))
		elif (format_string == "w"):
			minutes = int(seconds / 60)
			if (minutes >= 1):
				seconds = seconds - (minutes * 60)
				if (minutes >= 60):
					hours = int(minutes/60)
					minutes = minutes - (hours * 60)
					if (hours >= 24):
						days = int(hours / 24)
						hours = hours - (days * 24)
						if (days >= 7):
							weeks = int(days / 7)
							days = days - (weeks * 7)
							return "%s weeks, %s days, %s hours, %s minutes, %s seconds" % (weeks, days, hours, minutes, round(seconds))
						else:
							return "%s days, %s hours, %s minutes, %s seconds" % (days, hours, minutes, round(seconds))
					else:
						return "%s hours, %s minutes, %s seconds" % (hours, minutes, round(seconds))
				else:
					return "%s minutes, %s seconds" % (minutes, round(seconds))
			else:
				return "%s seconds" % (round(seconds))
		else:
			return self.format_time(seconds, "h")


	def main(self, page):
		global running
		self.clear_window()

		# Normally these would be local to the whole class, not just this def
		# They have been made local to just this def in order to prevent a bug
		stack = Gtk.Stack()
		stack.add_titled(self.page0, "page0", "Report")
		self.page0.set_visible(True)
		stack.add_titled(self.page1, "page1", "Settings")
		self.page1.set_visible(True)
		self.grid.attach(stack, 1, 2, 4, 1)

		stack_switcher = Gtk.StackSwitcher()
		stack_switcher.set_stack(stack)
		self.grid.attach(stack_switcher, 2, 1, 1, 1)

		vert = 0
		horiz = 0
		for each in self.processes:
			globals()[each + "_label"] = Gtk.Label()
			globals()[each + "_label"].set_markup("""\n\t<b>%s:</b>\t\n""" % (each))
			globals()[each + "_label"].set_justify(Gtk.Justification.LEFT)
			self.page0.attach(globals()[each + "_label"], horiz, vert, 1, 1)

			globals()[each + "_label1"] = Gtk.Label()
			globals()[each + "_label1"].set_markup("""\n\t%s\t\n""" % (self.format_time(globals()[each], self.time_format)))
			globals()[each + "_label1"].set_justify(Gtk.Justification.LEFT)
			self.page0.attach(globals()[each + "_label1"], horiz + 1, vert, 1, 1)

			vert = vert + 1

		self.label = Gtk.Label()
		self.label.set_markup("""\n\t<b>Total:</b>\t\n""")
		self.label.set_justify(Gtk.Justification.LEFT)
		self.page0.attach(self.label, horiz, vert, 1, 1)

		self.label1 = Gtk.Label()
		self.label1.set_markup("""\n\t%s\t\n""" % (self.format_time(self.total, self.time_format)))
		self.label1.set_justify(Gtk.Justification.LEFT)
		self.page0.attach(self.label1, horiz + 1, vert, 1, 1)

		self.toggle = Gtk.Button.new_with_label("\n\t%s Tracking\t\n" % (running))
		self.toggle.connect("clicked", self.track)
		self.page0.attach(self.toggle, horiz, vert + 1, 2, 1)

		self.toggle = Gtk.Button.new_with_label("\n\tReload Report\t\n")
		self.toggle.connect("clicked", self.reload)
		self.page0.attach(self.toggle, horiz, vert + 2, 2, 1)

		self.label2 = Gtk.Label()
		self.label2.set_markup("\nApps to Follow\n")
		self.label2.set_justify(Gtk.Justification.CENTER)
		self.page1.attach(self.label2, 1, 1, 2, 1)

		vert = 2
		for each in self.processes:
			globals()[each + "_label3"] = Gtk.Label()
			globals()[each + "_label3"].set_markup("""\n\t%s\t\n""" % (each))
			globals()[each + "_label3"].set_justify(Gtk.Justification.LEFT)
			self.page1.attach(globals()[each + "_label3"], 1, vert, 1, 1)

			globals()[each + "_button1"] = Gtk.Button.new_with_label("Remove %s" % (each))
			globals()[each + "_button1"].connect("clicked", self.remove)
			self.page1.attach(globals()[each + "_button1"], 2, vert, 1, 1)

			vert = vert + 1

		self.button4 = Gtk.Button.new_with_label("\n\tAdd Program\t\n")
		self.button4.connect("clicked", self.add_program)
		self.page1.attach(self.button4, 2, vert, 1, 1)

		self.label3 = Gtk.Label()
		self.label3.set_markup("\nTiming Sensitivity\n")
		self.label3.set_justify(Gtk.Justification.CENTER)
		self.page1.attach(self.label3, 1, vert + 1, 2, 1)

		adj = Gtk.Adjustment.new(self.sec_to_scale(self.polling_rate), 1, 10, 0.1, 0.1, 1)
		self.scale = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL, adj)
		self.scale.add_mark(1, Gtk.PositionType.TOP, "Less Precise")
		self.scale.add_mark(5, Gtk.PositionType.TOP, "Average")
		self.scale.add_mark(10, Gtk.PositionType.TOP, "More Precise")
		self.scale.connect("change-value", self.scale_to_sec)
		self.page1.attach(self.scale, 1, vert + 3, 3, 1)


		self.button2 = Gtk.Button.new_with_label("Done")
		self.button2.connect("clicked", self.apply)
		self.grid.attach(self.button2, 1, 3, 1, 1)

		if (page == 1):
			stack.set_visible_child(stack.get_child_by_name("page0"))
		elif (page == 2):
			stack.set_visible_child(stack.get_child_by_name("page1"))

		self.show_all()

	def track(self, widget):
		global running
		if (pgrep()):
			Popen(["killall", "time-tracker"])
			running = "Start"
		else:
			Popen(["../../bin/time-tracker"])
			running = "Stop"
		self.main(1)

	def add_program(self, widget):
			dialog = Gtk.FileChooserDialog("Time Tracker", self,
			Gtk.FileChooserAction.OPEN,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

			self.add_filters(dialog)

			response = dialog.run()
			if response == Gtk.ResponseType.OK:
				filename = dialog.get_filename().split("/")
				filename = filename[len(filename) - 1]
				self.processes.append(filename)

			dialog.destroy()
			self.read_logs("clicked")
			self.main(2)

	def add_filters(self, dialog):
		filter_text = Gtk.FileFilter()
		filter_text.set_name("Programs")
		filter_text.add_mime_type("application/x-shellscript")
		filter_text.add_mime_type("application/x-sharedlib")
		filter_text.add_mime_type("application/x-executable")
		filter_text.add_mime_type("application/x-perl")
		filter_text.add_mime_type("text/x-python3")
		filter_text.add_mime_type("application/x-ruby")
		dialog.add_filter(filter_text)

		filter_any = Gtk.FileFilter()
		filter_any.set_name("Any files")
		filter_any.add_pattern("*")
		dialog.add_filter(filter_any)

	def sec_to_scale(self, number):
		global A
		global B
		val = ((number - B )/ A)
		return(val)

	def scale_to_sec(self, widget, test1, test2):
		global A
		global B
		number = widget.get_value()
		self.polling_rate = A * number + B

	def remove(self, button):
		death_row = button.get_label().split(" ")[1]
		# print(death_row)
		for each in range(len(self.processes)):
			if (self.processes[each] == death_row):
				del(self.processes[each])
				break

		self.clear_window()
		self.main(2)

	def read_logs(self, button):
		global CONFIG_DIR
		self.total = 0
		for each in self.processes:
			globals()[each] = 0
			log_file = CONFIG_DIR + "/" + each + "-time.log"
			if (path.exists(log_file)):
				numbers = []
				contents = ""
				with open(log_file, "r") as num_file:
					contents = num_file.read()
				numbers = contents.split("\n")
				for each1 in numbers:
					try:
						globals()[each] = globals()[each] + float(each1)
					except ValueError:
						pass
			self.total = self.total + globals()[each]

	def read_settings(self):
		global CONFIG_DIR
		global CONFIG_FILE
		if (not path.exists(CONFIG_FILE)):
			try:
				mkdir(getenv("HOME") + "/.config")
			except FileExistsError:
				pass
			try:
				mkdir(CONFIG_DIR)
			except FileExistsError:
				pass
			try:
				with open(CONFIG_FILE, "w+") as out_file:
					out_file.write("""# Config File for time-tracker
# lines starting with '#' are comments
# lines starting with '$' are internal vars
# on each line, place process name of each app to be tracked
# so for instance if you want to track Filezilla usage, put
# 'filezilla' on it's own line (no quotation marks)

# How often to poll for processes, in seconds, floating point numbers supported
# More often gives better timing accuracy
# Less often uses less CPU power
$ polling_rate=2.8114754095

# how to format time output in settings window
# s = seconds
# m = minutes
# h = hours (default)
# d = days
# w = weeks
$ time_format=h
""")
			except IOError:
				eprint("ERROR: Could not write to config file.")
		else:
			with open(CONFIG_FILE, "r") as in_file:
				contents = str(in_file.read())
				contents = list(contents)
				contents = "".join(contents)
				self.processes = contents.split("\n")
			# set deault values
			self.polling_rate = 2.8114754095
			self.time_format = "h"
			for each in range(len(self.processes) - 1, -1, -1):
				if (len(self.processes[each]) <= 1):
					del(self.processes[each])
				elif (self.processes[each][0] == "#"):
					del(self.processes[each])
				elif (self.processes[each][0] == "$"):
					if ("polling_rate" in self.processes[each][1:]):
						self.polling_rate = float(self.processes[each].split("=")[1])
						del(self.processes[each])
					if ("time_format" in self.processes[each][1:]):
						self.time_format = self.processes[each].split("=")[1]
						del(self.processes[each])

	def apply(self, button):
		# Write new settings to conf file
		global CONFIG_DIR
		global CONFIG_FILE
		current_settings = ""
		if (path.exists(CONFIG_FILE)):
			remove(CONFIG_FILE)
			try:
				with open(CONFIG_FILE, "w+") as out_file:
						out_file.write("""# Config File for time-tracker
# lines starting with '#' are comments
# lines starting with '$' are internal vars
# on each line, place process name of each app to be tracked
# so for instance if you want to track Filezilla usage, put
# 'filezilla' on it's own line (no quotation marks)

# How often to poll for processes, in seconds, floating point numbers supported
# More often gives better timing accuracy
# Less often uses less CPU power
$ polling_rate=%s


# how to format time output in settings window
# s = seconds
# m = minutes
# h = hours (default)
# d = days
# w = weeks
$ time_format=%s
""" % (self.polling_rate, self.time_format))
						for each in self.processes:
							out_file.write(each)
							out_file.write("\n")
			except IOError:
				eprint("ERROR: Could not write to config file.")
		self.exit("clicked")

	def exit(self,button):
		Gtk.main_quit("delete-event")
		print(1)
		exit(1)

	def clear_window(self):
		children = self.grid.get_children()
		for each in children:
			self.grid.remove(each)

		children = self.page0.get_children()
		for each in children:
			self.page0.remove(each)

		children = self.page1.get_children()
		for each in children:
			self.page1.remove(each)


def show_main():
	window = main_ui()
	window.set_decorated(True)
	window.set_resizable(False)
	window.set_position(Gtk.WindowPosition.CENTER)
	window.connect("delete-event", main_ui.exit)
	window.show_all()
	Gtk.main()

#get length of argv
argc = len(argv)
show_main()


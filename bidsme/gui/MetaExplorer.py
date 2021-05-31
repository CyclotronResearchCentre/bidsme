###############################################################################
# MetaExplorer is a small gui class allowing explore and select meta-data
# values from supported data formats
###############################################################################
# Copyright (c) 2019-2020, University of Liège
# Author: Nikita Beliy
# Owner: Liege University https://www.uliege.be
# Credits: [Marcel Zwiers]
# Maintainer: Nikita Beliy
# Email: Nikita.Beliy@uliege.be
# Status: developpement
###############################################################################
# This file is part of BIDSme
# BIDSme is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# eegBidsCreator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with BIDSme.  If not, see <https://www.gnu.org/licenses/>.
##############################################################################

import os

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from Modules import selector


class cMetaExplorer(object):
    __slots__ = ["root", "meta", "Prefix", "mode",
                 "tvMeta",
                 "varSearch", "eSearch",
                 "bPrevious", "bNext", "varSCount",
                 "lfound", "lfound_index",
                 "bInsert",
                 "varSelected", "bJump"
                 ]

    def __init__(self, parent, meta_dict, title, mode="bare"):
        """
        Class implements the window presenting the metadata
        from meta_dict

        Parameters:
        -----------
        parent: parent window
        meta_dict: dictionary containing metadata
        title: window title
        mode: way how selected variable will be presented
                "bare"  -- simple string without brackets
                "meta"  -- string enclosed in <>
                "qmeta" -- same as "meta" but additional
                           double quotes are added
        """

        if mode not in ("bare",
                        "meta", "qmeta",
                        "bids", "qbids",
                        "custom", "qcustom"):
            raise Exception("Invalid mode {}".format(mode))

        self.mode = mode

        root = tk.Toplevel(parent)
        root.title(title)
        self.root = root

        self.Prefix = title
        self.meta = meta_dict

        self.lfound = []
        self.lfound_index = -1

        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        frMain = ttk.Frame(root)
        frMain.grid(row=0, column=0, sticky="nsew")
        frMain.rowconfigure(1, weight=1)
        frMain.columnconfigure(0, weight=1)

        frSearch = ttk.Labelframe(frMain, text="Search")
        self.varSearch = tk.StringVar()
        self.varSearch.trace_add('write', self.Search)
        self.eSearch = ttk.Entry(frSearch)
        self.eSearch.config(justify="left", textvariable=self.varSearch)
        self.eSearch.pack(side="left", fill="x", expand=True)
        self.eSearch.bind("<Shift-Return>", self.PrevSelect)
        self.eSearch.bind("<Return>", self.NextSelect)
        self.bNext = ttk.Button(frSearch, text=">>",
                                command=self.Next, state="disabled")
        self.bNext.pack(side="right")
        self.varSCount = tk.StringVar(value="0")
        lSCount = ttk.Label(frSearch,  width=-7, anchor="center",
                            textvariable=self.varSCount)
        lSCount.pack(side="right")
        self.bPrevious = ttk.Button(frSearch, text="<<",
                                    command=self.Prev, state="disabled")
        self.bPrevious.pack(side="right")
        frSearch.grid(column=0, row=0, padx=5, sticky="new", columnspan=2)

        self.tvMeta = ttk.Treeview(frMain, columns=("type", "value"),
                                   selectmode="browse")
        self.tvMeta["show"] = ("tree", "headings")
        self.tvMeta.grid(column=0, row=1, sticky="nsew")
        self.tvMeta.heading("type", text="type")
        self.tvMeta.column("type", anchor="w",  width=50, stretch=False)
        self.tvMeta.heading("value", text="value")
        self.tvMeta.tag_configure("normal", background='white')
        self.tvMeta.tag_configure("found", background='green')
        self.tvMeta.tag_configure('unset', background='grey')
        self.tvMeta.tag_configure('error', background='red')

        sy = ttk.Scrollbar(frMain, orient=tk.VERTICAL,
                           command=self.tvMeta.yview)
        self.tvMeta.configure(yscrollcommand=sy.set)
        sy.grid(column=1, row=1, sticky="nsw")

        self.tvMeta.bind("<<TreeviewSelect>>", self.SetSelection)

        frSelected = ttk.Labelframe(frMain, text="Selected")
        eSelected = ttk.Entry(frSelected)
        self.varSelected = tk.StringVar()
        eSelected.config(justify="left", state="readonly",
                         textvariable=self.varSelected)
        eSelected.pack(side="left", fill="x", expand=True)
        self.bJump = ttk.Button(frSelected, text="Jump",
                                command=self.Jump, state="disabled")
        self.bJump.pack(side="right")
        frSelected.grid(row=2, column=0, columnspan=2, sticky="new")

        frButtons = ttk.Frame(frMain)
        bCancel = ttk.Button(frButtons, text="Return", command=self.Cancel)
        bCancel.pack(side='right')
        self.bInsert = ttk.Button(frButtons, text="Copy",
                                  command=self.CopyToClipboard,
                                  state="disabled")
        self.bInsert.pack(side='right')
        frButtons.grid(column=0, row=3, rowspan=2, sticky="new")

        self.Populate()

    def show(self):
        self.root.deiconify()
        self.root.grab_set()
        self.root.wait_window()
        return self.varSelected.get()

    def CopyToClipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.varSelected.get())
        self.root.update()

    def Cancel(self):
        self.varSelected.set("")
        self.root.destroy()

    def Validate(self):
        return True

    def Populate(self):
        for name, item in self.meta.items():
            self.addNode("", name, item, 0)

    def addNode(self, parent, name, item, lvl=0):
        if parent:
            Id = "{}/{}".format(parent, name)
        else:
            Id = name
        if isinstance(item, list):
            self.tvMeta.insert(parent, 'end',
                               Id, text=name,
                               tags=("normal",),
                               values=("list", "..."))
            for i, it in enumerate(item):
                self.addNode(Id, str(i), it, lvl + 1)
        elif isinstance(item, dict):
            self.tvMeta.insert(parent, 'end',
                               Id, text=name,
                               tags=("normal",),
                               values=("dict", "..."))
            for i, it in item.items():
                self.addNode(Id, i, it, lvl + 1)
        elif isinstance(item, str):
            self.tvMeta.insert(parent, 'end',
                               Id, text=name,
                               tags=("normal",),
                               values=("Str", item))
        elif isinstance(item, int):
            self.tvMeta.insert(parent, 'end',
                               Id, text=name,
                               tags=("normal",),
                               values=("Int", item))

        elif isinstance(item, float):
            self.tvMeta.insert(parent, 'end',
                               Id, text=name,
                               tags=("normal",),
                               values=("Float", item))
        elif item is None:
            self.tvMeta.insert(parent, 'end',
                               Id, text=name,
                               tags=("unset",),
                               values=("None", ""))
        else:
            self.tvMeta.insert(parent, 'end',
                               Id, tags=("error",),
                               values=("Unknown", str(item)))

    def Search(self, *args):
        self.lfound = []
        self.lfound_index = -1
        pattern = self.varSearch.get().lower()
        self._search("", pattern)

        self.varSCount.set(str(len(self.lfound)))
        if len(self.lfound) > 0:
            self.bNext.state(["!disabled"])
            self.bPrevious.state(["!disabled"])
        else:
            self.bNext.state(["disabled"])
            self.bPrevious.state(["disabled"])

    def _search(self, node, query):
        res = False
        tag = "normal"
        text = node.lower()
        if node:
            text = self.tvMeta.item(node, "text").lower()
            if query and query in text:
                res = True
                self.lfound.append(node)

        for item_id in self.tvMeta.get_children(node):
            if self._search(item_id, query):
                res = True

        if res:
            tag = "found"
        if node:
            self.tvMeta.item(node, tags=(tag,))
        return res

    def Prev(self):
        if self.lfound_index < 1:
            self.lfound_index = len(self.lfound) - 1
        else:
            self.lfound_index -= 1
        self._ShowFound()

    def Next(self):
        if self.lfound_index < len(self.lfound) - 1:
            self.lfound_index += 1
        else:
            self.lfound_index = 0
        self._ShowFound()

    def _ShowFound(self):
        if self.lfound_index >= 0 and self.lfound_index < len(self.lfound):
            self.tvMeta.see(self.lfound[self.lfound_index])
            self.varSCount.set("{}/{}".format(self.lfound_index + 1,
                                              len(self.lfound)))
        else:
            self.lfound_index = -1
            self.varSCount.set(str(len(self.lfound)))

    def NextSelect(self, *args):
        if len(self.lfound) == 0:
            return
        self.Next()
        self.tvMeta.selection_set(self.lfound[self.lfound_index])

    def PrevSelect(self, *args):
        if len(self.lfound) == 0:
            return
        self.Prev()
        self.tvMeta.selection_set(self.lfound[self.lfound_index])

    def SetSelection(self, *args):
        sel = self.tvMeta.selection()
        if len(sel) > 0:
            var = sel[0]
            if self.mode == "meta":
                var = "<{}>".format(var)
            elif self.mode == "qmeta":
                var = "\"<{}>\"".format(var)
            if self.mode == "bids":
                var = "<<bids:{}>>".format(var)
            elif self.mode == "qbids":
                var = "\"<<bids:{}>>\"".format(var)
            if self.mode == "custom":
                var = "<<custom:{}>>".format(var)
            elif self.mode == "qcustom":
                var = "\"<<custom:{}>>\"".format(var)

            self.varSelected.set(var)
            self.bInsert.state(['!disabled'])
            self.bJump.state(['!disabled'])
        else:
            self.varSelected.set("")
            self.bInsert.state(["disabled"])
            self.bJump.state(["disabled"])

    def Jump(self):
        self.tvMeta.see(self.tvMeta.selection()[0])


class MetaExplorer(object):
    __slots__ = ["cbType", "varType", "cbFormat", "varFormat",
                 "path", "parent", "wFormatSelection"]

    def __init__(self, parent, path):
        self.parent = parent
        self.path = path

        self.wFormatSelection = tk.Toplevel(parent)
        self.wFormatSelection.title("select data type and format")
        self.wFormatSelection.rowconfigure(0, weight=1)
        self.wFormatSelection.columnconfigure(0, weight=1)

        frMain = ttk.Frame(self.wFormatSelection)
        frMain.grid(row=0, column=0, sticky="nsew")
        frMain.columnconfigure(1, weight=1)

        ttk.Label(frMain, text="Data type").grid(row=0, column=0, sticky="new")
        ttk.Label(frMain, text="Data format").grid(row=1, column=0,
                                                   sticky="new")

        self.varType = tk.StringVar()
        self.cbType = ttk.Combobox(frMain, textvariable=self.varType)
        self.cbType.state(["readonly"])
        data_types = list(selector.types_list.keys())
        self.cbType['values'] = data_types
        self.varType.set(data_types[0])
        self.cbType.grid(row=0, column=1, sticky="new")

        self.varFormat = tk.StringVar()
        self.cbFormat = ttk.Combobox(frMain, textvariable=self.varFormat)
        self.cbFormat.state(["readonly"])
        self.cbFormat.grid(row=1, column=1, sticky="new")
        self.UpdateFormats()

        self.cbType.bind('<<ComboboxSelected>>', self.UpdateFormats)

        bBrowse = ttk.Button(frMain, text="Select file", command=self.FindFiles)
        bBrowse.grid(row=2, column=1, sticky="new")

    def UpdateFormats(self, *args):
        classes = selector.types_list[self.varType.get()]
        formats = [cl.Type()
                   for cl in classes
                   if cl.Type() != "None"]
        self.cbFormat["values"] = formats
        self.varFormat.set(formats[0])

    def FindFiles(self, *args):
        cls = selector.selectByName(self.varFormat.get(), self.varType.get())
        fname = filedialog.askopenfilename(parent=self.wFormatSelection,
                                           initialdir=self.path,
                                           filetypes=[(self.varFormat.get(),
                                                      " ".join(cls._file_extentions))
                                                      ])

        if fname:
            dir_path = os.path.dirname(fname)
            self.path = dir_path
            if not cls.isValidFile(fname):
                messagebox.showinfo(title=fname,
                                    message='Is not valid {} file'
                                    .format(self.varFormat.get()))
                return
            recording = cls()
            recording._loadFile(fname)
            cMetaExplorer(self.wFormatSelection, recording.dump(),
                          "test", mode="qmeta").show()

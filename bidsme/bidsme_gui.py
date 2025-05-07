###############################################################################
# BIDSme-gui implements a GUI interface to Bidsne
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
from multiprocessing import Process

try:
    import tkinter as tk
    from tkinter import ttk

    from .gui import MetaExplorer

    def GUI():
        """
        Launches bidsme GUI to facilitate some bidsification
        tasks
        """
        p = Process(target=_gui, name="bidsme-GUI",
                    daemon=True)
        p.start()

    def _gui():
        root = tk.Tk()
        root.title("bidsme gui tools")
        mainframe = ttk.Frame(root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        ttk.Button(mainframe, text="Metadata Explorer",
                   command=lambda: MetaExplorer(root, os.getcwd()))\
           .grid(column=1, row=1, sticky="w")

        root.mainloop()

except ModuleNotFoundError:
    def GUI():
        """
        Placeholder for the GUI in case when tkinter is not aviable.
        Always raise ModuleNotFoundError
        """
        raise ModuleNotFoundError("bidsme GUI needs tkinter installed")


if __name__ == "__main__":
    GUI()

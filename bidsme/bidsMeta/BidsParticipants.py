###############################################################################
#  BidsParticipants.pydefines class that manages participants.tsv table
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
import logging
import pandas

from .BidsMeta import BIDSfieldLibrary


logger = logging.getLogger(__name__)


class BidsParticipants(object):
    __slots__ = ["destination", 
                 "_old_df", "_processed_df",
                 "_definition_file", "_df_file",
                 "__sub_columns", "__sub_list"]

    def __init__(self, destination: str, definitions: str=""):
        self._old_df = None
        self._processed_df = None
        self.destination = destination
        self._definition_file = os.path.join(destination, "participants.json")
        self._df_file = os.path.join(destination, "participants.tsv")
        self._df_errors = os.path.join(destination, "__participants.tsv")

        # Check if error file don't exists
        if os.path.isfile(self._df_errors):
            logger.critical("Found unmerged __participants.tsv file")
            raise FileExistsError(self._df_errors)

        # Loading definitions
        self.__sub_columns = BIDSfieldLibrary()
        if definitions:
            cls.__sub_columns.LoadDefinitions(filename)
        elif os.path.isfile(self._definition_file):
            cls.__sub_columns.LoadDefinitions(self._definition_file)
        else:
            cls.__sub_columns.AddField(
                    name="participant_id",
                    longName="Participant Id",
                    description="Unique label associated with a participant"
                    )

        # loading subject list
        if os.path.isfile(self._df_file):
            self.__sub_list = pandas.read_csv(self._df_file, sep="\t", header=0,
                                              usecols="participant_id",
                                              squeeze=True)
        else:
            self.__sub_list = pandas.Series()


    @classmethod
    def loadSubjectFields(cls, filename: str = "") -> None:
        """
        Loads the tsv fields for subject.tsv file

        Parameters
        ----------
        filename: str
            path to the template json file, if None,
            the default is loaded
        """
        if cls.__sub_columns is not None:
            logger.warning("Redefinition of participants template")
        cls.__sub_columns = BIDSfieldLibrary()
        if not filename:
            cls.__sub_columns.AddField(
                    name="participant_id",
                    longName="Participant Id",
                    description="Unique label associated with a participant"
                    )
        else:
            cls.__sub_columns.LoadDefinitions(filename)



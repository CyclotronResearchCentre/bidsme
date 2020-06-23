###############################################################################
# abstract.py provides a purely abstract part of baseModule class
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

from abc import ABC, abstractmethod
from datetime import datetime


class abstract(ABC):

    #########################
    # Pure virtual methodes #
    #########################
    @classmethod
    @abstractmethod
    def _isValidFile(cls, file: str) -> bool:
        """
        Virtual function that checks if file is valid one

        Parameters
        ----------
        file: str
            path to file to test

        Returns
        -------
        bool:
            True if file is valid for current class
        """
        raise NotImplementedError

    @abstractmethod
    def _loadFile(self, path: str) -> None:
        """
        Virtual function that load file at given path

        Parameters
        ----------
        path: str
            path to file to load
        """
        raise NotImplementedError

    @abstractmethod
    def _getAcqTime(self) -> datetime:
        """
        Virtual function that returns acquisition time, i.e.
        time corresponding to the first data of file

        Returns
        -------
        datetime
            datetime of acquisition of current scan
        """
        raise NotImplementedError

    @abstractmethod
    def dump(self) -> dict:
        """
        Virtual function that created adictionary of all meta-data
        associated with current file

        Returns
        -------
        dict:
            dictionary with parced values from current scan header,
            all data must be of basic python class: str, int, float,
            date, time, datetime
        """
        raise NotImplementedError

    @abstractmethod
    def _getField(self, field: list, prefix: str = ""):
        """
        Virtual function that retrives the field value
        from recording metadata. field is garanteed to be
        non-empty

        Parameters
        ----------
        field: list(str)
            list of nested values (or just one element)
            giving position of field to retrieve
        prefix: str
            prefix indicating the transformation function
            to call on retrieved value

        Returns
        -------
            retrieved value or None if field not found

        Raises
        ------
        TypeError:
            if field value is not applicable to prefix
            function
        KeyError:
            if prefix function is not defined
        """
        raise NotImplementedError

    @abstractmethod
    def recNo(self) -> int:
        """
        Virtual function returning current serie number
        (i.e. numero of scan in session).
        recNo together with recId must uniquely
        identify serie within session

        Returns
        -------
        int:
            Number of current serie, or 0 if not defined
        """
        raise NotImplementedError

    @abstractmethod
    def recId(self) -> str:
        """
        Virtual function returning current serie id
        (i.e. name of scan in session).
        recNo together with recId must uniquely
        identify serie within session

        Returns
        -------
        str:
            The Id string of current serie
        """
        raise NotImplementedError

    @abstractmethod
    def isCompleteRecording(self) -> bool:
        """
        Virtual function.
        Returns True if current recording is complete,
        False overwise.

        Returns
        -------
        bool:
            True if scan is complete, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def _getSubId(self) -> str:
        """
        Virtual function
        Returns subject id as defined in metadata

        Returns
        -------
        str:
            string representing Id of current subject as
            defined in header or None if such information
            is not defined
        """
        raise NotImplementedError

    @abstractmethod
    def _getSesId(self) -> str:
        """
        Virtual function
        Returns session id as defined in metadata

        Returns
        -------
        str:
            string representing Id of current session as
            defined in header or None if such information
            is not defined
        """
        raise NotImplementedError

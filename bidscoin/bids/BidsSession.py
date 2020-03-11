import os
import logging 
from copy import deepcopy as copy

from tools import tools
from bidsMeta import BIDSfieldLibrary


logger = logging.getLogger(__name__)


class BidsSession(object):
    __slots__ = ["__subject", "__session", 
                 "in_path",
                 "__sub_locked", "__ses_locked",
                 "sub_values"
                 ]

    __sub_columns = None
    __sub_values = dict()

    def __init__(self):
        self.__subject = None
        self.__session = None
        self.in_path = None

        self.__sub_locked = False
        self.__ses_locked = False

        if self.__sub_columns is None:
            raise ValueError("Participants tsv not initialized")
        self.sub_values = self.__sub_columns.GetTemplate()

    @property
    def subject(self) -> str:
        return self.__subject

    @subject.setter
    def subject(self, val: str):
        if self.__sub_locked:
            raise Exception("Subject Id is locked")
        if val is not None and not isinstance(val, str):
            raise TypeError("Subject Id must be str")
        self.__subject = val

    @property
    def session(self) -> str:
        return self.__session

    @session.setter
    def session(self, val: str) ->str:
        if self.__ses_locked:
            raise Exception("Session Id is locked")
        if val is not None and not isinstance(val, str):
            raise TypeError("Session Id must be str")
        self.__session = val

    def lock_subject(self):
        """
        Forbids any futher changes to subject Id
        and bidsify current value
        """
        self.__sub_locked = True
        self.__subject = tools.cleanup_value(self.__subject, "sub-")

    def unlock_subject(self):
        """
        Allows futher changes to subject Id
        """
        self.__sub_locked = False

    def lock_session(self):
        """
        Forbids any futher changes to session Id
        and bidsify current value
        """
        self.__ses_locked = True
        self.__session = tools.cleanup_value(self.__session, "ses-")

    def unlock_session(self):
        """
        Allows futher changes to session Id
        """
        self.__ses_locked = False

    def lock(self):
        """
        Forbids any futher changes to subject and session Id
        """
        self.lock_subject()
        self.lock_session()

    def getPrefix(self) -> str:
        """
        Returns prefix from subject and session Ids
        class must be valid
        """
        res = self.__subject
        if res is None:
            res = "Unknown"
        if self.__session:
            res += "_" + self.__session
        return res

    def getPath(self, empty: bool=False) -> str:
        """
        Returns path generated from subject and session Id

        Parameters
        ----------
        empty: bool
            if True, and session is not defined, generated
            path will still contain "ses-"
        """
        res = self.__subject
        if res is None:
            res = "Unknown"
        if self.__session:
            res = os.path.join(res, self.__session)
        elif empty:
            if self.__session is None:
                res = os.path.join(res, "Unknown")
            else:
                res = os.path.join(res, "/ses-")
        return res

    def isValid(self) -> bool:
        """
        Checks if session and subject Id are valid
        i.e. both are locked and defined (i.e. not None),
        and subject Id not an empty string
        """
        return self.isSubValid() and self.isSesValid()

    def isSubValid(self) -> bool:
        """
        Checks if subject ID is valid, i.e. is locked,
        not None and not empty
        """
        if not self.__sub_locked:
            return False
        if self.__subject is None:
            return False
        if self.__subject == "":
            return False
        return True

    def isSesValid(self) -> bool:
        """
        Checks if session ID is valid, i.e. is locked,
        not None
        """
        if not self.__ses_locked:
            return False
        if self.__session is None:
            return False
        return True

    def isLocked(self) -> bool:
        """
        returns True if both session and subject are locked
        """
        if not self.__sub_locked or not self.__ses_locked:
            return False
        else:
            return True

    @classmethod
    def loadSubjectFields(cls, filename: str="") -> None:
        """
        Loads the tsv fields for subject.tsv file

        Parameters
        ----------
        filename: str
            path to the template json file, if None,
            the default is loaded
        """
        if cls.__sub_columns is not None:
            raise ValueError("Redefinition of participants template")
        cls.__sub_columns = BIDSfieldLibrary()
        if not filename:
            cls.__sub_columns.AddField(
                    name="participant_id",
                    longName="Participant Id",
                    description="Unique label associated with a participant"
                    )
        else:
            cls.__sub_columns.LoadDefinitions(filename)

    def registerFields(self, conflicting: bool=False) -> None:
        """
        Register current values of participants fields

        Parameters
        ----------
        conflicting: bool
            if True, allow conflicting entries
        """
        self.sub_values["participant_id"] = self.subject
        if self.subject in self.__sub_values:
            last_values = self.__sub_values[self.subject][-1]
            conflict = False
            for key in self.sub_values:
                old_val = last_values[key]
                new_val = self.sub_values[key]
                if new_val is None:
                    self.sub_values[key] = old_val
                elif old_val != new_val:
                    conflict = True
            if conflict:
                if conflicting:
                    logger.warning("{}/{}: participants contains "
                                   "conflicting values"
                                   .format(self.subject, self.session))
                    self.__sub_values[self.subject].append(
                            copy(self.sub_values))
                else:
                    logger.critical("{}/{}: {} conflicts with {}"
                                    .format(self.subject, self.session,
                                            last_values, self.sub_values)
                                    )
                    raise ValueError("Conflicting participant values")
            else:
                self.__sub_values[self.subject][-1] = copy(self.sub_values)
        else:
            self.__sub_values[self.subject] = [copy(self.sub_values)]
        # self.sub_values = self.__sub_columns.GetTemplate()

    @classmethod
    def exportParticipants(cls, output:str) -> None:
        """
        Export current participants list to given location

        Parameters
        ----------
        output: str
            path to destination folder
        """
        fname = os.path.join(output, "participants.tsv")
        if os.path.isfile(fname):
            f = open(fname, "a")
            logger.warning("participants.tsv already exists, "
                            "some subjects may be duplicated")
        else:
            f = open(fname, "w")
            f.write(cls.__sub_columns.GetHeader())
            f.write("\n")
        for sub in sorted(cls.__sub_values):
            for vals in cls.__sub_values[sub]:
                f.write(cls.__sub_columns.GetLine(vals))
                f.write("\n")
        f.close()
        cls.__sub_columns.DumpDefinitions(os.path.join(output, 
                                                       "participants.json"))

class BidsSession(object):
    __slots__ = ["__subject", "__session", 
                 "in_path",
                 "__sub_locked", "__ses_locked"]

    def __init__(self):
        self.__subject = None
        self.__session = None
        self.in_path = None

        self.__sub_locked = False
        self.__ses_locked = False

    @property
    def subject(self) -> str:
        return self.__subject

    @property.setter
    def subject(self, val: str):
        if self.__sub_locked:
            raise Exception("Subject Id is locked")
        if val is not None or not isinstance(str, val):
            raise TypeError("Subject Id must be str")
        self.__subject = val

    @property
    def session(self) -> str:
        return self.__session

    @property.setter
    def session(self, val: str) ->str:
        if self.__sub_locked:
            raise Exception("Session Id is locked")
        if val is not None or not isinstance(str, val):
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
        if self.__session:
            res += "/" + self.__session
        elif empty:
            res += "/ses-"
        return res

    def isValid(self) -> bool:
        """
        Checks if session and subject Id are valid
        i.e. both are locked and defined (i.e. not None),
        and subject Id not an empty string
        """
        if not self.__sub_locked or not self.__ses_locked:
            return False
        if self.__subject is None or self.__session is None:
            return False
        if self.__subject == "":
            return False
        return True

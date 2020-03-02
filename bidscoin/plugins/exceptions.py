from exceptions import CoinException
"""
List of generic Plugin and individual plugin functions
exceptions
"""

class PluginError(CoinException):
    """
    Generic plugin error
    """
    base = 100
    code = 0


class PluginNotFoundError(PluginError):
    """
    Raises if plugin file not found
    """
    code = 1


class PluginModuleNotFoundError(PluginError):
    """
    Raises if no plugin modules found in plugin file
    """
    code = 2


class InitEPError(PluginError):
    """
    Raises if an error happens during the plugin initialisation
    """
    base = 100
    code = 0


class SubjectEPError(PluginError):
    """
    Raises if an error happens during the Subject adjustement
    """
    base = 110
    code = 0


class SessionEPError(PluginError):
    """
    Raises if an error happens during the Session adjustement
    """
    base = 120
    code = 0


class SequenceEPError(PluginError):
    """
    Raises if an error happens during the Sequence adjustement
    """
    base = 130
    code = 0


class RecordingEPError(PluginError):
    """
    Raises if an error happens during the Recording adjustement
    """
    base = 140
    code = 0


class FileEPError(PluginError):
    """
    Raises if an error happens during the post-copy file adjustement
    """
    base = 150
    code = 0


class SequenceEndEPError(PluginError):
    """
    Raises if an error happens during the post-sequence adjustement
    """
    base = 160
    code = 0


class SessionEndEPError(PluginError):
    """
    Raises if an error happens during the post-session adjustement
    """
    base = 170

class SubjectEndEPError(PluginError):
    """
    Raises if an error happens during the post-subject adjustement
    """
    base = 180

class FinaliseEPError(PluginError):
    """
    Raises if an error happens during the finalisation adjustement
    """
    base = 190
    code = 0

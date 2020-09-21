# Dictionary of channel types (in BIDS definition) that can be
# filled by user in plugin
from .EEG import channel_types

from .BrainVision import BrainVision

try:
    from .EDF import EDF
except ModuleNotFoundError as e:
    if e.name == "mne":
        from .._formats.dummy import dummy as EDF
        EDF.classes["EDF"] = e.name
    else:
        raise


__all__ = ["BrainVision", "EDF", "channel_types"]

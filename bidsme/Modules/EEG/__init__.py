# Dictionary of channel types (in BIDS definition) that can be
# filled by user in plugin
from .EEG import channel_types, channel_kinds

try:
    from .EDF import EDF
except ModuleNotFoundError as e:
    from .._formats.dummy import dummy as EDF
    EDF.classes["EDF"] = e.name

try:
    from .BrainVision import BrainVision
except ModuleNotFoundError as e:
    from .._formats.dummy import dummy as BrainVision
    BrainVision.classes["BrainVision"] = e.name

__all__ = ["BrainVision", "EDF", "channel_types", "channel_kinds"]

__formats = [BrainVision, EDF]

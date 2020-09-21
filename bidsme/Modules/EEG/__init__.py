# Dictionary of channel types (in BIDS definition) that can be
# filled by user in plugin
from .EEG import channel_types

from .BrainVision import BrainVision
from .EDF import EDF

__all__ = ["BrainVision", "EDF"]

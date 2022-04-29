from .main import init, main
from .prepare import prepare
from .mapper import mapper
from .process import process
from .bidsify import bidsify

__all__ = ["init", "main", "prepare",
           "mapper", "process", "bidsify"]

name = "bidsme"

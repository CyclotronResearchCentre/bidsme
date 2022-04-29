import os
import sys
import bidsme

if __name__ == "__main__":
    res = bidsme.main(sys.argv[1:])
    os.sys.exit(res)

#! /usr/bin/env python

import aurorax
import pprint


def main():
    source = aurorax.ephemeris.get_source(1)
    pprint.pprint(source)


# ----------
if (__name__ == "__main__"):
    main()

#!/usr/bin/env python3
"""Build the VIVAIA patrol channel using the shared patrol renderer."""
from build_fanka_patrol import ROOT, main

if __name__ == '__main__':
    main(channel=ROOT / 'vivaia-patrol', brand='VIVAIA')

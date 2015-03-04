#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# "THE SCOTCH-WARE LICENSE" (Revision 42):
# <DonMarco42@gmail.com> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a scotch whisky in return
# Marco 'don' Kaulea
# ----------------------------------------------------------------------------
"""goodfood

Usage:
    goodfood <url>
"""


import docopt
import requests


def main():
    arguments = docopt.docopt(__doc__)
    r = requests.get(arguments['<url>'])
    if r.status_code == 200:
        print(r.text)


if __name__ == '__main__':
    main()

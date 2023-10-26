#!/usr/bin/env python3

from distutils.core import setup, Extension


if __name__ == '__main__':
    setup(
        name='userlib', 
        ext_modules=[
            Extension(name='userlib', sources=['./userlib.c'], language='C')
        ],
    )

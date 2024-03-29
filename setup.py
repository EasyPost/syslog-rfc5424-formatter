#!/usr/bin/env python

from setuptools import setup


setup(
    name="syslog-rfc5424-formatter",
    version="1.2.3",
    author="EasyPost",
    author_email="oss@easypost.com",
    url="https://github.com/easypost/syslog-rfc5424-formatter",
    license="ISC",
    py_modules=['syslog_rfc5424_formatter'],
    keywords=["logging"],
    description="Logging formatter which produces well-formatted RFC5424 Syslog Protocol messages",
    project_urls={
        'Issue Tracker': 'https://github.com/easypost/syslog-rfc5424-formatter/issues',
        'Documentation': 'https://syslog-rfc5424-formatter.readthedocs.io/en/latest/',
    },
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <4',
    packages=['syslog_rfc5424_formatter'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: POSIX",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Topic :: System :: Logging",
    ]
)

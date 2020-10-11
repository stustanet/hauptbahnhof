#!/usr/bin/env python3

from setuptools import setup

VERSION = "1.0"


def readme():
    with open("README.md", "r") as f:
        return f.read()


setup(
    name="hauptbahnhof",
    version=VERSION,
    description="StuStaNet Hackerspace IoT Control Hub",
    long_description=readme(),
    maintainer="StuStaNet e.V. Admins",
    maintainer_email="admins@stustanet.de",
    url="https://gitlab.stusta.de/stustanet/hauptbahnhof",
    packages=[
        "hauptbahnhof",
        "hauptbahnhof.core",
        "hauptbahnhof.hackerman",
        "hauptbahnhof.nsa",
        "hauptbahnhof.haspa_web",
        "hauptbahnhof.mpd"
    ],
    # data_files=[
    #     (
    #         "/usr/lib/systemd/system/",
    #         ["systemd/hauptbahnhof-module@.service", "systemd/hauptbahnhof.target"]
    #     ),
    #     (
    #         "/etc/hauptbahnhof/",
    #         ["conf/hauptbahnhof.json", "conf/arplist.json"]
    #     ),
    # ],
    platforms=["Linux"],
    install_requires=["patho-mqtt", "hbmqtt", "websockets", "requests"],
    classifiers=[
        "Topic :: Internet :: WWW/HTTP",
        "Intended Audience :: Developers",
        "Environment :: Web Environment",
        "Environment :: Console",
        "Operating System :: POSIX :: Linux"
    ]
)

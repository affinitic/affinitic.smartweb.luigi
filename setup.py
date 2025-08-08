# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="affinitic.smartweb.luigi",
    version="1.0.0",
    description="Affinitic ETL based on Luigi for migrating existing website to smartweb",
    long_description="",
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: OS Independent",
    ],
    author="Julien Chandelle",
    author_email="support@affinitic.be",
    keywords="Python",
    url="https://git.affinitic.be/affinitic/affinitic_luigi",
    license="",
    packages=find_packages("src",exclude=("docs", )),
    install_requires=[
        "luigi",
    ],
    extras_require={
        "test": [
            "nose",
        ],
        "docs": [
            "sphinx",
        ],
    },
)

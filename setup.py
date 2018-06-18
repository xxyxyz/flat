from setuptools import setup

setup(
    name="flat",
    use_scm_version=True,
    url="http://xxyxyz.org/flat",
    description=(
        "Flat is a library for creating and manipulating digital forms of fine arts."
    ),
    author="Juraj Sukop",
    author_email="contact@xxyxyz.org",
    packages=["flat"],
    classifiers=[
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
    ],
    setup_requires=["setuptools_scm"],
)

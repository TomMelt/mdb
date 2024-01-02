from setuptools import find_packages, setup

setup(
    name="mdb",
    version="0.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "matplotlib",
        "numpy",
        "pexpect",
    ],
    extras_require={
        "develop": [
            "black",
            "flake8",
            "mypy",
            "types-setuptools",
        ]
    },
    entry_points={
        "console_scripts": [
            "mdb = mdb.mdb:main",
        ],
    },
)

from setuptools import setup, find_packages

setup(
    name="shredded",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "rich>=13.0.0",
        "typer>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "shredded=shredded.main:main",
        ],
    },
    python_requires=">=3.11",
)

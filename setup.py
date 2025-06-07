import sys

from setuptools import find_packages, setup

if sys.platform == "win32":
    print("NOTE: For Windows, ensure Microsoft C++ Build Tools are installed.")

setup(
    name="constellaxion",
    version="0.4.1",
    packages=find_packages(),
    install_requires=open("requirements.txt", encoding="utf-8").read().splitlines(),
    entry_points={
        "console_scripts": [
            "constellaxion=constellaxion.main:cli",
        ],
    },
    author="Constellaxion Technologies, Inc.",
    author_email="dev@constellaxion.ai",
    description="The constellaXion CLI for managing your laboratory database",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    keywords=["constellaxion", "ai", "ml ops"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    package_data={"constellaxion": ["services/gcp/*.py", "models/scripts/**/*.py"]},
)

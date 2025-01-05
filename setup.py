from setuptools import setup, find_packages

setup(
    name='constellaxion',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests',
        'rich',
        'click',
        "google-api-python-client",
        "google-auth",
        "google-auth-httplib2",
    ],
    entry_points={
        'console_scripts': [
            'constellaxion=constellaxion.main:cli',
        ],
    },
    author='Constellaxion Technologies, Inc.',
    author_email='dev@constellaxion.ai',
    description='The Constellaxion CLI for managing your laboratory database',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    keywords=["constellaxion", "ai", "ml ops"],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
    package_data={"constellaxion": ["models/tinyllama_1b/gcp/*.py"]}
)

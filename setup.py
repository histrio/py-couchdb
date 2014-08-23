from setuptools import setup

description = "Modern pure python CouchDB Client."

try:
   from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py

setup(
    name = "pycouchdb",
    url = "https://github.com/niwibe/py-couchdb",
    author = "Andrey Antukh",
    author_email = "niwi@niwi.be",
    version="1.9",
    packages = [
        "pycouchdb",
    ],
    description = description.strip(),
    zip_safe = False,
    include_package_data = True,
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "License :: OSI Approved :: BSD License",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
    ],
    entry_points = {
        "console_scripts": [
            "couchpy = pycouchdb.view:main"
        ],
    },
    cmdclass = {"build_py": build_py},
    install_requires = ["requests"]
)

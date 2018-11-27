import setuptools


configuration = {
    "name": "edera",
    "version": "0.10",
    "description": "A distributed workflow management framework",
    "classifiers": [
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: System :: Distributed Computing"
    ],
    "keywords": "workflow task schedule distributed dependency management",
    "url": "https://github.com/thoughteer/edera",
    "author": "Iskander Sitdikov",
    "author_email": "thoughteer@gmail.com",
    "license": "MIT",
    "packages": setuptools.find_packages(exclude=["tests", "tests.*"]),
    "include_package_data": True,
    "install_requires": [
        "flask >= 0.10.1, < 1.0",
        "iso8601 >= 0.1.10, < 1.0",
        "kazoo >= 2.5.0, < 3.0",
        "pymongo >= 3.4, < 4.0",
        "six >= 1.10, < 2.0",
        "sympy >= 0.7.4, < 1.0",
    ],
    "zip_safe": False,
}
setuptools.setup(**configuration)

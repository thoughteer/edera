import setuptools


setuptools.setup(
    name="edera",
    version="0.10.2",
    description="A distributed workflow management framework",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: System :: Distributed Computing",
    ],
    keywords="workflow task schedule distributed dependency management",
    url="https://github.com/thoughteer/edera",
    author="Iskander Sitdikov",
    author_email="thoughteer@gmail.com",
    license="MIT",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    install_requires=[
        "flask >= 1.0.2, < 2.0",
        "iso8601 >= 0.1.10, < 1.0",
        "kazoo >= 2.5.0, < 3.0",
        "pymongo >= 3.4, < 4.0",
        "six >= 1.10, < 2.0",
        "sympy >= 1.3, < 2.0",
    ],
    zip_safe=False)

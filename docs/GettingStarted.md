# Getting Started

### Prerequisite

**Edera** requires a Python distribution of version 2.7 or higher.
Unfortunately, version 3.7 is not supported yet.

### Installation

This Python package provides a vanilla `setup.py` file, so you can install it in any way you prefer; e.g.

```bash
$ pip install edera
```

### Running tests

You can run tests using `tox` ([PyPI](https://pypi.org/project/tox/)). See `tox.ini` for details.

```bash
$ tox  # run all tests for all available Python versions
$ tox -e py27  # run all tests for Python 2.7
$ tox tests/unit  # run only unit tests for all available Python versions
$ tox -e py36 tests/integration  # run only integration tests for Python 3.6
```

Some integration tests require MongoDB and ZooKeeper.
You can use Docker to set up a local development environment:

```bash
$ docker run -d -p 27017:27017 --name edera-mongo mongo
$ docker run -d -p 2181:2181 --name edera-zookeeper zookeeper
```

### Running demo

You can also use `tox` to run the included demo.

##### In production mode

```bash
$ mkdir -p demo/production
$ tox -e ui -- demo/production  # then open the link in a web-browser and keep refreshing
$ tox -e daemon -- demo/production  # in a separate terminal
```

##### In testing mode

```bash
$ mkdir -p demo/testing
$ tox -e ui -- demo/testing  # then open the link in a web-browser and keep refreshing
$ tox -e daemon -- -t demo/testing  # in a separate terminal
```

### Logging

We highly recommend you to use [`logging.handlers.SysLogHandler`](https://docs.python.org/2/library/logging.handlers.html#sysloghandler)
in combination with a syslog-compatible service like [`syslog-ng`](https://syslog-ng.org)
to implement logging in your application.
It seems to be the only reliable way to organize multi-process logging effortlessly.

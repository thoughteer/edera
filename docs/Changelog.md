# Changelog

### 0.11

* Added support for Python 3.7
* Implemented buffering on monitoring agents
* Fixed all known issues with `Proxy`
* Replaced pickling with custom interpreter-independent serialization
* Started to ignore monitor-related errors
* Limited tracebacks in the monitoring UI up to one last call
* Refactored `MonitoringSnapshot` (separated its core from task payloads)
* Made snapshot updates more reliable
* Added more debug logging

### 0.10.5

* Re-fixed URL highlighting in the monitoring UI

### 0.10.4

* Implemented `EmbeddedStorage` and simplified the `Storage` interface
* Fixed a couple of minor issues with the monitoring UI
* Slightly improved performance of `MongoStorage`
* Reduced the size of monitoring data
* Introduced static daemon modules and static timestamps for auto-testing

### 0.10.3

* Reduced the lag of the first execution in `Daemon` (#4)
* Updated the monitoring UI (#20)
* Fixed the concurrent access problem in `SQLiteStorage` (#14)
* Enabled PyPy 2.7/3.5 support
* Fixed a premature completion bug in `Daemon`

### 0.10.2

* Updated dependencies to the latest major versions

### 0.10.1

* Made `Daemon` handle SIGTERM correctly
* Fixed the snapshot updates dropping procedure in `MonitorWatcher`

### 0.10

* Reworked workflow auto-testing
* Fixed `WorkflowTestifier`
* Improved the normalization algorithm
* Made target checks interruptible
* Improved `MasterSlaveInvoker`
* Tweaked the monitoring UI
* Improved `Beanbag`

### 0.9

* Revised the whole framework
* Fixed a couple of major bugs
* Improved test coverage
* Introduced performance tests
* Optimized `Parameterizable` significantly
* Added a simple demo

### 0.8.4

* Fixed a major bug in DirectoryLocker

### 0.8.3

* Handled ZooKeeper errors during lock acquisition properly

### 0.8.2

* Switched to web-safe monospace fonts in the UI
* Marked log messages as HTML-safe
* Limited the number of log messages stored in the monitor

### 0.8.1

* Fixed label flattening in the UI

### 0.8

* Upgraded the monitoring UI:
    - Stopped failing when there are no snapshots available
    - Added support for custom captions
    - Made all anchors auto-focusing
    - Added start/finish timestamps and the duration for completed tasks
    - Added the full name of the task to facilitate search by name
    - Started capturing important logs and publishing them in the UI
    - Redesigned the UI a bit

### 0.7.4

* Got rid of the annoying animation flickering in monitoring UI
* Optimized `MongoStorage` by indexing it by (key, timestamp)

### 0.7.3

* Preserved tracebacks while reraising exceptions

### 0.7.2

* Handled None-targets during workflow testification

### 0.7.1

* Renamed (monitoring) `Server` to `App`
* Made relative URLs in the `App` WSGI-friendly

### 0.7

* Introduced infrastructure for workflow auto-testing:
    - Use `TestableTask` to define tests and stubs for your tasks
    - Use `WorkflowTestifier` to transform your workflows into auto-tests
    - Use `TestingWorkflowExecuter` to run your testing workflows
    - ...
    - PROFIT!!!
* Fixed a major bug in `WorkflowNormalizer`
* Made a `Daemon` class out of the `daemon.run` function
* Got rid of `ManagedInvoker` and introduced `ManagedWorkflowExecuter`
* Generalized linearizers to any graphs and introduced `TaskRanker`
* Reworked the `Queue` class to go well with `TaskRanker`
* Introduced a new `annotate` requisite
* Added some syntactic sugar to `GraphNode`
* Enhanced `tox.ini`
* Improved task ordering in the "Edera Monitor" web-interface
* Changed the style of imports throughout the code
* Got rid of "private" modules
* Changed the style of the control panel in the "Edera Monitor" web-interface
* Fixed documentation

### 0.6.1

* Lowered the minimum required version of `PyMongo` down to 3.1

### 0.6

* Introduced `MonitoringWorkflowExecuter` and `edera.monitoring`:
    - Allows workflow executors to report information about tasks
    - Allows you to aggregate this information over sources and time, and render it as an HTML
* Added a separate "offline" workflow to the daemon (useful to run monitor watchers)
* Re-worked the `Storage` interface
* Replaced DOA `ZooKeeperStorage` with more efficient MongoDB-based `MongoStorage`
* Refactored duplicating tests (`pytest` is really full of magic)
* Reorganized tests that involve external services (like ZooKeeper or MongoDB):
    - Such tests became optional
    - No test harnesses - only real service instances
    - Now you need to redefine corresponding environment variables in `tox.ini`
* Simplified class factory declarations (like `Qualifier`s)
* Fixed a couple of minor bugs
* Fixed documentation

### 0.5

* Introduced `Storage`s to store versioned key-value pairs:
  - `SQLiteStorage`
  - `ZooKeeperStorage`
* Converted some workflow executers into workflow processors
* Implemented target caching and integrated it into the daemon
* Fixed various minor bugs

### 0.4

* Introduced hackable `edera.daemon` that allows to run tasks in parallel as a service
* Reworked internal coroutine class hierarchy
* Added lots of `__repr__` implementations to facilitate debugging
* Redesigned qualifiers and added more useful qualifiers:
  - `Optional`
  - `Date`
  - `DateTime`
  - `TimeDelta`
* Introduced non-in-place coroutine context extensions using `+`
* Added a new `follow_all` requisite
* Settled an exception handling convention:
  - `ExcusableError`s should lead to `ExcusableError`s
  - `SystemExit` is not an error - never panic
* Introduced a couple of managers:
  - `ZooKeeperManager`
  - `CascadeManager`
* Introduced `ManagedInvoker` to run stuff within a context manager
* Discovered a bug related to forking in Python (see `ProcessWorker`)
* Introduced static default parameter values
* Hid phony tasks (ones that don't override `execute`) from the workflow execution log

### 0.3

* Re-implemented `DirectoryLocker` using `sqlite3`
* Removed `fasteners` from the dependencies
* Replaced explicit polling with coroutines
* Introduced a stable asynchronous signal handling agent

### 0.2.1

* Moved packaging tools from an external repository here

### 0.2

* Documented the code
* Added a quick guide
* Introduced soft interruptions through polling
* Introduced target freezing
* Rearranged and simplified the code a bit
* Made minor fixes

### 0.1

* Released the initial version with basic functionality

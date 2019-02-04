import datetime
import os.path
import pkg_resources
import re

import flask
import jinja2.loaders
import six

import edera.helpers

from edera.monitoring.watcher import MonitorWatcher


URL_PATTERN = "https?://[^\\s]*"


class MonitoringUI(flask.Flask):
    """
    A monitoring UI (web-application).

    This class aims to render monitoring snapshots and task payloads obtained from a watcher.

    Use it as a regular Flask application (either in developer mode or via WSGI).

    Attributes:
        caption (String) - the caption to show in the header

    Examples:
        Here is how you can run the UI in developer mode using a MongoDB-based storage:

            >>> import pymongo
            >>> from edera.helpers import Lazy
            >>> from edera.storages import MongoStorage
            >>> from edera.monitoring import MonitoringUI
            >>> monitor = MongoStorage(Lazy[pymongo.MongoClient](), "edera", "monitor")
            >>> MonitoringUI("example", monitor).run(debug=True)

    See also:
        $MonitorWatcher
    """

    def __init__(self, caption, monitor):
        """
        Args:
            caption (String) - a caption to show in the header
            monitor (Storage) - a storage that keeps snapshots
        """
        flask.Flask.__init__(self, __name__)
        self.caption = caption
        self.__watcher = MonitorWatcher(monitor)
        self.__configure()

    def __configure(self):

        @self.template_filter("formatdatetime")
        def format_datetime(dt):
            offset = datetime.datetime.now() - datetime.datetime.utcnow()
            return (dt + offset).strftime("%Y-%m-%d %H:%M:%S")

        @self.template_filter("formattimedelta")
        def format_timedelta(td):

            def decompose(seconds):
                if seconds >= 86400:
                    days = int(seconds / 86400)
                    if days == 1:
                        yield "1 day"
                    else:
                        yield "%d days" % days
                    seconds -= days * 86400
                if seconds >= 3600:
                    hours = int(seconds / 3600)
                    if hours == 1:
                        yield "1 hour"
                    else:
                        yield "%d hours" % hours
                    seconds -= hours * 3600
                if seconds >= 60:
                    minutes = int(seconds / 60)
                    if minutes == 1:
                        yield "1 minute"
                    else:
                        yield "%d minutes" % minutes
                    seconds -= minutes * 60
                if seconds != 0:
                    yield "%.3f seconds" % seconds

            return " ".join(decompose(td.total_seconds()))

        @self.template_filter("hashstring")
        def hash_string(string):
            return edera.helpers.sha1(string)[:6]

        @self.template_filter("selectkeys")
        def select_keys(mapping, keys):
            return {key: mapping[key] for key in keys}

        @self.template_filter("highlight")
        def highlight(message):
            link = jinja2.Markup("<a href='\g<0>'>\g<0></a>")
            return jinja2.Markup(re.sub(URL_PATTERN, link, message))

        @self.route("/")
        def index():
            snapshot = self.__watcher.load_snapshot()
            if snapshot is None:
                return flask.render_template("void.html", caption=self.caption)
            labeling = self.__label_tasks(snapshot)
            ranking = self.__rank_tasks(snapshot)
            return flask.render_template(
                "index.html",
                caption=self.caption,
                snapshot=snapshot,
                labeling=labeling,
                ranking=ranking,
                mode=flask.request.args.get("mode", "short"))

        @self.route("/report/<alias>")
        def report(alias):
            snapshot = self.__watcher.load_snapshot()
            if snapshot is None or alias not in snapshot.reports:
                flask.abort(404)
            labeling = self.__label_tasks(snapshot)
            payload = self.__watcher.load_payload(alias)
            return flask.render_template(
                "report.html",
                caption=self.caption,
                snapshot=snapshot,
                labeling=labeling,
                alias=alias,
                payload=payload)

        self.jinja_loader = jinja2.loaders.PackageLoader(
            "edera", package_path="resources/monitoring/ui/templates")
        self.static_folder = os.path.abspath(
            pkg_resources.resource_filename("edera", "resources/monitoring/ui/static"))

    def __label_tasks(self, snapshot):
        tasks = list(snapshot.aliases)
        aliases = [snapshot.aliases[task] for task in tasks]
        labels = edera.helpers.squash_strings(tasks)
        return dict(zip(aliases, labels))

    def __rank_tasks(self, snapshot):
        return {
            alias: (
                not report.state.failures,
                report.state.completed,
                report.state.phony,
                not report.state.runs,
                report.state.name,
            )
            for alias, report in six.iteritems(snapshot.reports)
        }

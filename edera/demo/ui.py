import argparse
import os.path

from edera.monitoring.ui import MonitoringUI
from edera.storages import SQLiteStorage


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="file re-hasher monitoring UI")
    parser.add_argument("-p", "--port", type=int, default=8080, help="server port")
    parser.add_argument("root", metavar="ROOT", help="root directory")
    arguments = parser.parse_args()
    monitor = SQLiteStorage(os.path.join(arguments.root, "monitor.db"))
    MonitoringUI("Edera Demo", monitor).run(port=arguments.port, debug=True)

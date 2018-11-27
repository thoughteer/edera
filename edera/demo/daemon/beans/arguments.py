import argparse


class Bean(argparse.Namespace):

    def __new__(cls):
        parser = argparse.ArgumentParser(description="file re-hasher")
        parser.add_argument("-d", "--debug", action="store_true", help="enable debug-logging")
        parser.add_argument("-t", "--test", action="store_true", help="run auto-tests")
        parser.add_argument("-f", "--fail", action="store_true", help="enforce failures")
        parser.add_argument("-s", "--sleep", type=float, default=5, help="sleep time (in seconds)")
        parser.add_argument("root", metavar="ROOT", help="root directory")
        return parser.parse_args()

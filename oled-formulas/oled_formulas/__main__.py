"""Start or pause the registered formula queue through its existing service."""
import argparse
import sys

from core.api import catalog__load_config
from .api import control_pilot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('start', 'pause'))
    try:
        control_pilot(catalog__load_config(), parser.parse_args().action == 'start')
    except (ValueError, RuntimeError, OSError, KeyError) as exc:
        sys.exit(str(exc))


if __name__ == '__main__':
    main()

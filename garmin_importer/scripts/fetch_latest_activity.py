import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../garmin_importer')))

from aws_utils import get_date_of_latest_activity

USERNAME = "<your username>"


def main():
    last_stored_activity = get_date_of_latest_activity(USERNAME)
    print(f'Last activity persisted: {str(last_stored_activity)}')


if __name__ == '__main__':
    main()

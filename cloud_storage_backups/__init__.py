import argparse
import json
import logging
import logging.handlers
import os
import tempfile
from configparser import ConfigParser

from google.cloud import storage
from google.oauth2 import service_account
from google.api_core import exceptions as google_api_core_exceptions

log = logging.getLogger(__name__)


def init_logging(path, fh_level='debug', ch_level='info'):
    # create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, ch_level.upper()))

    # create formatter
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)8s:%(name)s:%(filename)s:%(funcName)s:%(lineno)d:%(message)s')

    if fh_level:
        # create file handler
        fh = logging.handlers.RotatingFileHandler(path, mode='a',
                                                  maxBytes=200000000,
                                                  backupCount=5,
                                                  encoding='utf-8')
        fh.setLevel(getattr(logging, fh_level.upper()))

        # add formatter to fh
        fh.setFormatter(formatter)

        # add fh to logger
        logger.addHandler(fh)

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)


def load_config(config_file):
    config = ConfigParser()
    config.read(config_file)
    return config


class GoogleCloudStorage(object):

    def __init__(self, private_key_json_file, bucket, project_id=None):
        self.private_key_json_file = private_key_json_file
        self.project_id = project_id
        self.init_bucket(bucket)

    def init_bucket(self, bucket):
        with open(self.private_key_json_file) as source:
            info = json.load(source)
        self.storage_credentials = service_account.Credentials.from_service_account_info(info)
        self.storage_client = storage.Client(project=self.project_id if self.project_id else info['project_id'],
                                        credentials=self.storage_credentials)
        self.bucket = self.storage_client.get_bucket(bucket)

    def upload_backup(self, local_path, remote_path):
        blob = self.bucket.blob(remote_path)
        blob.upload_from_filename(local_path)

    def check_for_backup(self, remote_path):
        if self.bucket.get_blob(remote_path) is None:
            return False
        return True


def check_file_exists(filepath):
    if os.path.isfile(filepath):
        log.debug(f'config_file_path {filepath} is a file.')
        return True
    else:
        log.error(f'config_file_path {filepath} is not a file.')
    return False


def main():
    parser = argparse.ArgumentParser(description='Cloud Storage Backups APP')
    parser.add_argument('--console-log-level', action='store', dest='console_log_level', required=False,
                        type=str, choices=['debug', 'info', 'critical', 'error', 'warning'],
                        help='console log level', default='error')
    parser.add_argument('--file-log-level', action='store', dest='file_log_level', required=False,
                        type=str, choices=['debug', 'info', 'critical', 'error', 'warning'],
                        help='file log level', default=None)
    parser.add_argument('-l', '--log-path', action='store', dest='log_dir', required=False,
                        type=str, default=tempfile.gettempdir(),
                        help='/path/to/logs_dir')
    parser.add_argument('-c', '--config', action='store', dest='config_file_path', required=True,
                        type=str, help='/path/to/config.ini')
    parser.add_argument('--local-path', action='store', dest='local_path', required=True,
                        type=str, help='Local /path/to/backup')
    parser.add_argument('--remote-path', action='store', dest='remote_path', required=True,
                        type=str, help='remote (cloud) /path/to/backup')
    parser.add_argument('--google-project-id', action='store', dest='google_project_id', required=False,
                        type=str, help='google_project_id e.g. my-project-123456', default=None)
    parser.add_argument('--provider', action='store', dest='cloud_provider', required=True,
                        type=str, choices=['google'],
                        help='Cloud Provider e.g. google')

    args = parser.parse_args()
    log_path = os.path.join(args.log_dir, f'{os.path.basename(os.path.dirname(__file__))}.log')
    init_logging(log_path, ch_level=args.console_log_level, fh_level=args.file_log_level)
    local_path = args.local_path

    config_file_path = args.config_file_path
    if check_file_exists(config_file_path) is True:
        config = load_config(config_file_path)

        if os.path.isfile(local_path):
            log.debug(f'local_path {local_path} is a file.')
        else:
            log.error(f'local_path {local_path} is a not a file or does not exist.')
            raise SystemExit(f'local_path {local_path} is a not a file or does not exist.')

        cloud_provider = args.cloud_provider
        remote_path = args.remote_path
        if cloud_provider == 'google':
            google_project_id = args.google_project_id
            private_key_json_file = config.get('google', 'private_key_json_file')
            bucket = config.get('google', 'bucket')
            if check_file_exists(private_key_json_file) is True:
                gcs = GoogleCloudStorage(private_key_json_file=private_key_json_file, project_id=google_project_id,
                                         bucket=bucket)
                if gcs.check_for_backup(remote_path) is False:
                    try:
                        gcs.upload_backup(local_path, remote_path)
                    except google_api_core_exceptions.Forbidden:
                        log.exception(f'Failed to upload {local_path} to {remote_path} for provider {cloud_provider}.')
                    else:
                        log.info(f'Sucessfully uploaded {local_path} to {remote_path} for provider {cloud_provider}.')
                else:
                    log.warning(f'Backup {remote_path} allready exists in the cloud.')
            else:
                log.error(f'Unable to read private_key_json_file {private_key_json_file}'
                          f' cannot continue with provider {cloud_provider}.')
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

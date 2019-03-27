import os
import tempfile

import requests

from .configs import worker_config, server_url
from .util import md5sum


class APIError(Exception):
    pass


def get_auth_param():
    return worker_config['name'], worker_config['password']


def report_started(submission_id: int, work_id: str, hostname: str, pid: int):
    data = {'hostname': hostname, 'pid': pid}
    resp = requests.put('%sapi/submissions/%d/worker-started/%s' % (server_url, submission_id, work_id),
                        json=data, auth=get_auth_param())
    resp.raise_for_status()


def report_result(submission_id: int, work_id: str, data: dict):
    resp = requests.put('%sapi/submissions/%d/worker-result/%s' % (server_url, submission_id, work_id),
                        json=data, auth=get_auth_param())
    resp.raise_for_status()


def get_submission_and_config(submission_id: int, work_id: str):
    resp = requests.get(
        '%sapi/submissions/%d/worker-get-submission-and-config/%s' % (server_url, submission_id, work_id),
        auth=get_auth_param())
    resp.raise_for_status()
    return resp.json()


def download_material(material: dict, folder: str, chunk_size: int = 65536) -> str:
    resp = requests.get('%sapi/materials/%d/worker-download' % (server_url, material['id']), auth=get_auth_param(),
                        stream=True)
    resp.raise_for_status()

    name = material['name']
    name_parts = name.rsplit('.', 2)
    if len(name_parts) > 1:
        name_parts[0] = ''
        suffix = '.'.join(name_parts)
    else:
        suffix = None

    ffd = None
    try:
        fd, path = tempfile.mkstemp(suffix=suffix, dir=folder)
        ffd = os.fdopen(fd, 'wb')
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:
                ffd.write(chunk)
    finally:
        if ffd:
            ffd.close()

    if material['md5'] != md5sum(path):
        raise APIError('MD5 check of material "%s" failed' % material['name'])
    return os.path.relpath(path, folder)


def download_submission_file(submission_id: int, work_id: str, file: dict, local_save_path: str,
                             chunk_size: int = 65536):
    resp = requests.get('%sapi/submissions/%d/worker-submission-files/%s/%d' %
                        (server_url, submission_id, work_id, file['id']),
                        auth=get_auth_param(), stream=True)
    resp.raise_for_status()
    with open(local_save_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
    if file['md5'] != md5sum(local_save_path):
        raise APIError('MD5 check of submission file "%s" failed' % file['requirement']['name'])


def upload_output_files(submission_id: int, work_id: str, files: dict):
    resp = requests.post('%sapi/submissions/%d/worker-output-files/%s' %
                         (server_url, submission_id, work_id),
                         files=files, auth=get_auth_param())
    resp.raise_for_status()

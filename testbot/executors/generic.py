import os

from celery import Task

from testbot.api import report_started, get_submission_and_config, upload_output_files
from testbot.configs import data_folder
from testbot.executors.errors import ExecutorError


class GenericExecutor:
    def __init__(self, task: Task, submission_id: int, test_config_id: int):
        self.task = task
        self.submission_id = submission_id
        self.test_config_id = test_config_id

        self.submission = None
        self.test_config = None
        self.work_folder = None
        self.files_to_upload = {}

    def prepare(self):
        report_started(self.submission_id, self.task.request.id, self.task.request.hostname, os.getpid())

        # get submission info and test config
        info = get_submission_and_config(self.submission_id, self.task.request.id)

        submission = info['submission']
        if submission['id'] != self.submission_id:
            raise ExecutorError('Submission ID mismatch')
        self.submission = submission

        test_config = info['config']
        if test_config['id'] != self.test_config_id:
            raise ExecutorError('Test config ID mismatch')
        if not test_config['is_enabled']:
            raise ExecutorError('Test config is disabled')
        self.test_config = test_config

        # check data folder
        if not os.path.exists(data_folder):
            raise ExecutorError('Data folder does not exist')
        # check folder for all work
        works_folder = os.path.join(data_folder, 'test_works')
        if not os.path.exists(works_folder):
            raise ExecutorError('Folder for all work does not exist')
        # check work folder for the current task
        work_folder = os.path.join(works_folder, self.task.request.id)
        if os.path.lexists(work_folder):
            raise ExecutorError('Work folder already exists')
        self.work_folder = work_folder

    def run(self):
        pass

    def clean_up(self):
        if self.files_to_upload:
            upload_output_files(self.submission_id, self.task.request.id, self.files_to_upload)

    def start(self):
        self.prepare()
        try:
            return self.run()
        finally:
            self.clean_up()

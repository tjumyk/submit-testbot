import json
import os
import random
import shutil

from testbot.api import download_material, download_submission_file
from testbot.configs import data_folder
from testbot.executors.errors import ExecutorError
from testbot.executors.generic import GenericExecutor
from testbot.task import BotTask


class EnvironmentTestExecutor(GenericExecutor):
    EXIT_STATUS_TIMEOUT = 124

    def __init__(self, task: BotTask, submission_id: int, test_config_id: int):
        super().__init__(task=task, submission_id=submission_id, test_config_id=test_config_id)
        self.environment = None
        self.result_tag = None
        self.env_vars = {}

    def prepare(self):
        super(EnvironmentTestExecutor, self).prepare()

        test_environment = self.test_config.get('environment')
        if test_environment is None:
            raise ExecutorError('Test environment not specified')
        self.environment = test_environment

        # check environment folder
        env_folder = os.path.join(data_folder, 'test_environments')
        if not os.path.exists(env_folder):
            raise ExecutorError('Test environment folder does not exist')

        env_zip_path = self._prepare_env_zip(env_folder, test_environment)
        # unpack environment zip to work folder
        shutil.unpack_archive(os.path.join(env_folder, env_zip_path), self.work_folder)

        # download submission files into sub folder 'submission'
        submission_folder = os.path.join(self.work_folder, 'submission')
        if not os.path.lexists(submission_folder):
            os.mkdir(submission_folder)
        for file in self.submission['files']:
            local_save_path = os.path.join(self.work_folder, 'submission', file['requirement']['name'])
            download_submission_file(self.submission_id, self.task.request.id, file, local_save_path)

        # generate randomized result tag
        self.result_tag = '##RESULT%d##' % random.randint(100000, 999999)
        # generate additional environment variables
        self.env_vars = {'RESULT_TAG': self.result_tag}

    @staticmethod
    def _prepare_env_zip(env_folder: str, test_environment: dict) -> str:
        env_id = test_environment['id']
        env_md5 = test_environment['md5']

        # check cached environment
        env_meta_path = os.path.join(env_folder, '%d.json' % env_id)
        env_zip_path = None
        if os.path.isfile(env_meta_path):
            with open(env_meta_path) as f_meta:
                try:
                    env_meta = json.load(f_meta)
                    if env_meta['md5'] == env_md5:
                        env_zip_path = env_meta['path']
                except (TypeError, ValueError, KeyError):
                    pass
            if env_zip_path and not os.path.isfile(os.path.join(env_folder, env_zip_path)):
                env_zip_path = None

        # download environment if no cache found
        if not env_zip_path:
            env_zip_path = download_material(test_environment, env_folder)
            try:
                # use exclusive file lock to avoid race condition
                lock_path = os.path.join(env_folder, "%d.lock" % env_id)
                with open(lock_path, 'x'):
                    # save meta
                    with open(env_meta_path, 'w') as f_meta:
                        json.dump({
                            'path': env_zip_path,
                            'md5': env_md5
                        }, f_meta)
                os.remove(lock_path)
            except FileExistsError:
                pass
        return env_zip_path

    @staticmethod
    def extract_result(raw_output, result_tag):
        """
        Try to parse the last line that starts with the `result_tag` from the raw output as the result
        :param raw_output: raw output from the test script or command inside Docker
        :param result_tag: tag for the result line
        :return: result if parsed successfully
        """
        if not raw_output or not result_tag:
            return None
        if isinstance(raw_output, (bytes, bytearray)):
            raw_output = raw_output.decode()
        lines = raw_output.strip().split('\n')

        result = None
        for line in lines:
            line = line.strip()
            if line and line.startswith(result_tag):
                result = line[len(result_tag):].strip()

        if result is None:
            return None
        try:
            return json.loads(result)
        except (ValueError, TypeError):
            return result

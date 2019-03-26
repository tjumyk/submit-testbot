import os
import subprocess

from celery import Task

from .exec_env_test import EnvironmentTestExecutor
from .exec_generic import ExecutorError


class ScriptEnvironmentTestExecutor(EnvironmentTestExecutor):
    def __init__(self, task: Task, submission_id: int, test_config_id: int):
        super(ScriptEnvironmentTestExecutor, self).__init__(task=task, submission_id=submission_id,
                                                            test_config_id=test_config_id)
        self.run_script = None
        self.combined_env_vars = {}

    def prepare(self):
        super(ScriptEnvironmentTestExecutor, self).prepare()

        config_type = self.test_config['type']
        if config_type != 'run-script':
            raise ExecutorError('invalid config type for %s: %s' % (self.__class__.__name__, config_type))

        # Look for 'run.sh' and we will run it in the current environment directly, which has no system isolation or
        # time/resource/network restrictions.
        run_script = os.path.join(self.work_folder, 'run.sh')
        if not os.path.isfile(run_script):
            raise ExecutorError('Test script not found')
        self.run_script = run_script

        # make a copy of the current environment and add additional env vars
        env = os.environ.copy()
        env.update(self.env_vars)
        self.combined_env_vars = env

    def run(self):
        super(ScriptEnvironmentTestExecutor, self).run()

        proc_result = subprocess.run(['bash', os.path.abspath(self.run_script)], cwd=self.work_folder,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.combined_env_vars)
        if proc_result.stdout:
            self.files_to_upload['stdout.txt'] = proc_result.stdout
        if proc_result.stderr:
            self.files_to_upload['stderr.txt'] = proc_result.stderr

        if proc_result.returncode:
            if proc_result.returncode == self.EXIT_STATUS_TIMEOUT:
                raise TimeoutError('Test script timeout')
            raise ExecutorError('Test script returned non-zero exit status %d' % proc_result.returncode)
        return self.extract_result(proc_result.stdout, self.result_tag)

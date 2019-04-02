import os
import subprocess

from testbot.executors.env_test import EnvironmentTestExecutor
from testbot.executors.errors import ExecutorError
from testbot.task import BotTask


class ScriptEnvironmentTestExecutor(EnvironmentTestExecutor):
    def __init__(self, task: BotTask, submission_id: int, test_config_id: int):
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
            raise ExecutorError('Test script "run.sh" not found')
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

        return_code = proc_result.returncode
        if return_code:
            if return_code == self.EXIT_STATUS_TIMEOUT:
                raise TimeoutError('Test script timeout')
            errors = self.extract_errors(proc_result.stderr)
            if errors:
                raise RuntimeError(' \n'.join(errors))
            raise RuntimeError('Test returned exit code %d' % return_code)
        return self.extract_result(proc_result.stdout)

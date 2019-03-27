import requests

from testbot.configs import config
from testbot.executors.errors import ExecutorError
from testbot.executors.generic import GenericExecutor
from testbot.task import BotTask


class AntiPlagiarismExecutor(GenericExecutor):
    def __init__(self, task: BotTask, submission_id: int, test_config_id: int):
        super().__init__(task=task, submission_id=submission_id, test_config_id=test_config_id)

        self.api = None

    def prepare(self):
        super().prepare()

        config_type = self.test_config['type']
        if config_type != 'anti-plagiarism':
            raise ExecutorError('invalid config type for %s: %s' % (self.__class__.__name__, config_type))

        anti_plagiarism_config = config.get('ANTI_PLAGIARISM')
        if not anti_plagiarism_config:
            raise ExecutorError('config for anti-plagiarism not found')
        api = anti_plagiarism_config.get('api')
        if not api:
            raise ExecutorError('api address for anti-plagiarism not found')
        self.api = api

    def run(self):
        super().run()

        # use rid=4 for testing now as the main server has not added target rid in AutoTestConfig
        resp = requests.get('%s/api/check' % self.api, params=dict(rid=4, sid=self.submission_id))
        resp.raise_for_status()
        return resp.text

import json

import requests

from testbot.configs import config
from testbot.executors.errors import ExecutorError
from testbot.executors.generic import GenericExecutor
from testbot.task import BotTask


class AntiPlagiarismExecutor(GenericExecutor):
    def __init__(self, task: BotTask, submission_id: int, test_config_id: int):
        super().__init__(task=task, submission_id=submission_id, test_config_id=test_config_id)

        self.api = None
        self.file_requirement_id = None

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

        rid = self.test_config.get('file_requirement_id')
        if rid is None:
            raise ExecutorError('target file requirement id is not specified')
        self.file_requirement_id = rid

    def run(self):
        super().run()

        resp = requests.get('%s/api/check' % self.api, params=dict(rid=self.file_requirement_id,
                                                                   sid=self.submission_id))
        resp.raise_for_status()
        result = resp.text.split('\n', 1)

        if len(result) > 1:
            summary, report = result
        else:  # only one line or nothing
            summary = result
            report = None
        try:
            summary = json.loads(summary)
        except (TypeError, ValueError):
            pass

        if report:
            self.files_to_upload['report.txt'] = report
        return summary

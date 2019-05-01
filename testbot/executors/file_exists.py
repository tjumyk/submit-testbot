from testbot.executors.errors import ExecutorError
from testbot.executors.generic import GenericExecutor
from testbot.task import BotTask


class FileExistsExecutor(GenericExecutor):
    def __init__(self, task: BotTask, submission_id: int, test_config_id: int):
        super().__init__(task=task, submission_id=submission_id, test_config_id=test_config_id)

        self.file_requirement_id = None

    def prepare(self):
        super().prepare()

        config_type = self.test_config['type']
        if config_type != 'file-exists':
            raise ExecutorError('invalid config type for %s: %s' % (self.__class__.__name__, config_type))

        rid = self.test_config.get('file_requirement_id')
        if rid is None:
            raise ExecutorError('target file requirement id is not specified')
        self.file_requirement_id = rid

    def run(self):
        super().run()

        return any(file['requirement_id'] == self.file_requirement_id for file in self.submission['files'])

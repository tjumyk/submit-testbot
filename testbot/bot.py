import ssl

import celery

from testbot.configs import celery_config
from testbot.executors.anti_plagiarism import AntiPlagiarismExecutor
from testbot.executors.env_test_docker import DockerEnvironmentTestExecutor
from testbot.executors.env_test_script import ScriptEnvironmentTestExecutor
from testbot.task import BotTask

app = celery.Celery('submit', broker=celery_config['broker'], backend=celery_config['backend'])
app.conf.update(
    task_routes={
        'testbot.bot.run_env_test_script': {'queue': 'testbot_env_test_script'},
        'testbot.bot.run_env_test_docker': {'queue': 'testbot_env_test_docker'},
        'testbot.bot.run_anti_plagiarism': {'queue': 'testbot_anti_plagiarism'}
    },
    task_track_started=True
)
broker_ssl_config = celery_config.get('broker_use_ssl')
if broker_ssl_config:
    cert_reqs = broker_ssl_config.get('cert_reqs')
    if cert_reqs:
        broker_ssl_config['cert_reqs'] = getattr(ssl, cert_reqs)
    app.conf.update(broker_use_ssl=broker_ssl_config)


@app.task(bind=True, base=BotTask, name='testbot.bot.run_env_test_script')
def run_env_test_script(self: BotTask, submission_id: int, test_config_id: int):
    return ScriptEnvironmentTestExecutor(task=self, submission_id=submission_id, test_config_id=test_config_id).start()


@app.task(bind=True, base=BotTask, name='testbot.bot.run_env_test_docker')
def run_env_test_docker(self: BotTask, submission_id: int, test_config_id: int):
    return DockerEnvironmentTestExecutor(task=self, submission_id=submission_id, test_config_id=test_config_id).start()


@app.task(bind=True, base=BotTask, name='testbot.bot.run_anti_plagiarism')
def run_anti_plagiarism(self: BotTask, submission_id: int, test_config_id: int):
    return AntiPlagiarismExecutor(task=self, submission_id=submission_id, test_config_id=test_config_id).start()


# helper utilities for master server
task_entries = {
    'run-script': run_env_test_script,
    'docker': run_env_test_docker,
    'anti-plagiarism': run_anti_plagiarism
}

import ssl

import celery
from celery import Task

from .api import report_result
from .configs import celery_config
from .exec_env_test_docker import DockerEnvironmentTestExecutor
from .exec_env_test_script import ScriptEnvironmentTestExecutor

app = celery.Celery('submit', broker=celery_config['broker'], backend=celery_config['backend'])
app.conf.update(
    task_routes={
        'testbot.bot.run_env_test_script': {'queue': 'testbot_env_test_script'},
        'testbot.bot.run_env_test_docker': {'queue': 'testbot_env_test_docker'},
        'testbot.bot.run_anti_plagiarism': {'queue': 'testbot_anti_plagiarism'},
    },
    task_track_started=True
)
broker_ssl_config = celery_config.get('broker_use_ssl')
if broker_ssl_config:
    cert_reqs = broker_ssl_config.get('cert_reqs')
    if cert_reqs:
        broker_ssl_config['cert_reqs'] = getattr(ssl, cert_reqs)
    app.conf.update(broker_use_ssl=broker_ssl_config)


# noinspection PyAbstractClass
class MyTask(celery.Task):
    def on_success(self, result, work_id, args, kwargs):
        submission_id = args[0]
        report_result(submission_id, work_id, {
            'final_state': 'SUCCESS',
            'result': result
        })

    def on_failure(self, exc, work_id, args, kwargs, exc_info):
        submission_id = args[0]
        report_result(submission_id, work_id, {
            'final_state': 'FAILURE',
            'exception_class': type(exc).__name__,
            'exception_message': str(exc),
            'exception_traceback': exc_info.traceback
        })


@app.task(bind=True, base=MyTask, name='testbot.bot.run_env_test_script')
def run_env_test_script(self: Task, submission_id: int, test_config_id: int):
    return ScriptEnvironmentTestExecutor(task=self, submission_id=submission_id, test_config_id=test_config_id).start()


@app.task(bind=True, base=MyTask, name='testbot.bot.run_env_test_docker')
def run_env_test_docker(self: Task, submission_id: int, test_config_id: int):
    return DockerEnvironmentTestExecutor(task=self, submission_id=submission_id, test_config_id=test_config_id).start()


@app.task(bind=True, base=MyTask, name='testbot.bot.run_anti_plagiarism')
def run_anti_plagiarism(self: Task, submission_id: int, config_id: int):
    pass


# helper utilities for master server
task_entries = {
    'run-script': run_env_test_script,
    'docker': run_env_test_docker,
    'anti-plagiarism': run_anti_plagiarism
}

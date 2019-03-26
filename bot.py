import ssl

import celery
from celery import Task

from .api import report_result
from .configs import celery_config

app = celery.Celery('submit', broker=celery_config['broker'], backend=celery_config['backend'])
app.conf.update(
    task_routes={
        'testbot.bot.run_test': {'queue': 'auto-test'},
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


@app.task(bind=True, base=MyTask, name='testbot.bot.run_test')
def run_test(self: Task, submission_id: int, config_id: int):
    pass


@app.task(bind=True, base=MyTask, name='testbot.bot.run_anti_plagiarism')
def run_anti_plagiarism(self: Task, submission_id: int, config_id: int):
    pass

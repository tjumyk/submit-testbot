import json
import os

import docker
from celery import Task
from docker.errors import ContainerError, BuildError

from .exec_env_test import EnvironmentTestExecutor
from .exec_generic import ExecutorError


class DockerEnvironmentTestExecutor(EnvironmentTestExecutor):
    def __init__(self, task: Task, submission_id: int, test_config_id: int):
        super(DockerEnvironmentTestExecutor, self).__init__(task=task, submission_id=submission_id,
                                                            test_config_id=test_config_id)
        self.docker_client = docker.from_env()
        self.run_params = {}

    def prepare(self):
        super(DockerEnvironmentTestExecutor, self).prepare()

        config_type = self.test_config['type']
        if config_type != 'docker':
            raise ExecutorError('invalid config type for %s: %s' % (self.__class__.__name__, config_type))

        # 'Dockerfile' is required
        dockerfile = os.path.join(self.work_folder, 'Dockerfile')
        if not os.path.isfile(dockerfile):
            raise ExecutorError('Dockerfile not found')

        # get config for running the Docker container
        self._prepare_run_params()

    def _prepare_run_params(self):
        run_params = {
            'remove': True,  # by default, remove container after exit
            'environment': self.env_vars
        }
        # update docker configs
        for k, v in self.test_config.items():
            if v is None:
                continue
            if k == 'docker_auto_remove':
                run_params['remove'] = v
            elif k == 'docker_cpus':
                period = 100000
                run_params['cpu_period'] = period
                run_params['cpu_quota'] = int(v * period)
            elif k == 'docker_memory':
                run_params['mem_limit'] = '%dm' % v
            elif k == 'docker_network':
                run_params['network_disabled'] = not v

    def run(self):
        super(DockerEnvironmentTestExecutor, self).run()

        # build Docker image
        build_logs = None
        try:
            tag = 'submit-test-%s' % self.task.request.id
            image, build_logs = self.docker_client.images.build(path=self.work_folder, tag=tag)
        except BuildError as e:
            build_logs = e.build_log
            raise
        finally:
            if build_logs:
                self.files_to_upload['docker-build-logs.json'] = json.dumps(list(build_logs), indent=2)

        # run a Docker container with the specified limits and the new image
        try:
            # logs from stdout and stderr are combined due to the design of the API
            logs = self.docker_client.containers.run(image.id, name=tag, stdout=True, stderr=True, **self.run_params)
            if logs:
                self.files_to_upload['docker-run-logs.txt'] = logs
            result = self.extract_result(logs, self.result_tag)
        except ContainerError as e:
            if e.stderr:
                self.files_to_upload['docker-run-error.txt'] = e.stderr  # the error does not provide stdout
            if e.exit_status == self.EXIT_STATUS_TIMEOUT:
                raise TimeoutError('Test command timeout')
            raise ExecutorError('Test command returned non-zero exit status %d' % e.exit_status)

        if self.run_params.get('remove'):
            # If container should be removed, also try to remove the image
            # This operation may fail due to multiple repository references or other running containers
            try:
                self.docker_client.images.remove(image.id)
            except docker.errors.APIError as e:
                # keep the error message but do not treat it as a failure
                self.files_to_upload['docker-remove-image-error.txt'] = str(e)

        return result
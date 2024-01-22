# Test bot for Submission System

## Requirements

1. docker
2. submission system (https://github.com/tjumyk/submit)

## Setup

1. prepare python environment
```bash
# prepare a python virtual environment first
pip install -r requirements.txt
```

## Register testbot in submission system

1. In `config.json` of the submission system, add an entry in `workers` under `AUTO_TEST`, e.g.
```json
{
  "name": "test_worker_1",
  "password": "ALongPassword"
}
```

A random password can be generated by:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(12))'
```

You need to restart submission system server to let this take effect. 

You will need to add this block into local config as well (see below).

## Configuration

```bash
cp config.example.json config.json
# edit config.json
```

### Edit `config.json`

1. Update `AUTO_TEST_WORKER` according to the config in the section above
2. Edit `SITE` according to real setup
3. Delete `broker_use_ssl` in `AUTO_TEST`, update `broker` and `backend` if rabbitmq and redis is in a remote server. (if in remote server, also need to configure listen address of rabbitmq and redis and system firewall)

## Initialization

```bash
bash init.sh
```

## Run

```bash
celery -A testbot.bot worker -Q testbot_env_test_script,testbot_env_test_docker -l info -n 'testbot@%h' -c 2
```

Note: the user who runs this test bot need to be in the group `docker` to use docker without password.

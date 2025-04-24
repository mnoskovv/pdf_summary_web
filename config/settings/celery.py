import environ

env = environ.Env()
env.read_env(env.str('ENV_PATH', '.env'))

CELERY_BROKER_URL = f'amqp://{env("RABBITMQ_DEFAULT_USER")}:{env("RABBITMQ_DEFAULT_PASS")}@rabbitmq:5672/{env("RABBITMQ_DEFAULT_VHOST")}'

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'

CELERY_TIMEZONE = 'UTC'

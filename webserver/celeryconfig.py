CELERY_IMPORTS=("app", )
CELERY_BROKER_URL="amqp://saket:fedora13@localhost//"
CELERY_RESULT_BACKEND="amqp://saket:fedora13@localhost//"
SQLALCHEMY_DATABASE_URI="mysql://saket:fedora13@localhost/moca"
CELERYD_MAX_TASKS_PER_CHILD=10

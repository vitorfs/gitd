build:
	isort gitd
	black gitd
	flake8 gitd
	./manage.py makemigrations --check --dry-run

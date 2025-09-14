

.PHONY: start
start:
	docker-compose up --build -d
	poetry install
	poetry run python manage.py runserver

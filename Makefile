include .env

ifeq (shell, $(firstword $(MAKECMDGOALS)))
  RUN_ARGS := $(lastword $(MAKECMDGOALS))
  $(eval $(RUN_ARGS):;@:)
endif


up:
	docker-compose -f $(COMPOSE_FILE) up -d

down:
	docker-compose -f $(COMPOSE_FILE) down

build:
	docker-compose -f $(COMPOSE_FILE) build

rebuild:
	make down & make build

shell:
	docker-compose -f $(COMPOSE_FILE) exec $(RUN_ARGS) bash


collectstatic:
	docker-compose -f $(COMPOSE_FILE) exec web python manage.py collectstatic --noinput

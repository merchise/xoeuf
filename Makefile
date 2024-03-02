RYE_EXEC ?= rye run
CARGO_HOME ?= $(HOME)/.cargo
PATH := $(HOME)/.rye/shims:$(CARGO_HOME)/bin:$(PATH)
SHELL := /bin/bash

PYTHON_FILES := $(shell find src/ -type f -name '*.py')
RUN_RYE ?=
EXEC ?= rye run

ODOO_VERSION ?= 12.0
PYTHON_VERSION ?= 3.8

USE_UV ?= false
install:
	uv --version || curl -LsSf https://astral.sh/uv/install.sh | sh
	rye self update || curl -sSf https://rye-up.com/get | bash
	rye config --set-bool behavior.use-uv=$(USE_UV)
	rye pin --relaxed $(PYTHON_VERSION)
	rye sync
	cp -f requirements-dev.lock requirements-dev-py$$(echo $(PYTHON_VERSION) | sed "s/\.//").lock

	if [ -d ../odoo ]; then \
		$(EXEC) pip install -r ../odoo/requirements.txt; \
		$(EXEC) pip install -e ../odoo; \
	fi
.PHONY: install


format:
	@$(EXEC) isort src/
	@$(EXEC) ruff --fix src/
	@$(EXEC) ruff format src/
.PHONY: format-python

lint:
	@$(EXEC) ruff src/
	@$(EXEC) ruff format --check src/
	@$(EXEC) isort --check src/
.PHONY: lint

docs:
	@$(EXEC) pip install -r requirements-dev-py$$(echo $(PYTHON_VERSION) | sed "s/\.//").lock
	$(MAKE) SPHINXBUILD="$(EXEC) sphinx-build" -C docs html
	rye sync
	cp -f requirements-dev.lock requirements-dev-py$$(echo $(PYTHON_VERSION) | sed "s/\.//").lock

	if [ -d ../odoo ]; then \
		$(EXEC) pip install -r ../odoo/requirements.txt; \
		$(EXEC) pip install -e ../odoo; \
	fi
.PHONY: docs

CADDY_SERVER_PORT ?= 9999
caddy: docs
	@docker run --rm -p $(CADDY_SERVER_PORT):$(CADDY_SERVER_PORT) \
         -v $(PWD)/docs/build/html:/var/www -it caddy \
         caddy file-server --browse --listen :$(CADDY_SERVER_PORT) --root /var/www
.PHONY: caddy


# You can tweak these defaults in '.envrc' or by passing them to 'make'.
POSTGRES_USER ?= $(USER)
POSTGRES_PASSWORD ?= $(USER)
POSTGRES_HOST ?= pg
ODOO_MIRROR ?= https://gitlab.com/merchise-autrement/odoo.git
DOCKER_NETWORK_ARG ?= --network=host
RUN_RYE_ARG ?=

ifndef CI_JOB_ID
docker:
	docker build -t xoeuf \
	    --build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
	    --build-arg ODOO_VERSION=$(ODOO_VERSION) \
	    --build-arg ODOO_MIRROR=$(ODOO_MIRROR) \
        .

test: docker
	docker run --rm -it xoeuf /src/xoeuf/runtests-odoo.sh \
        -i $(ls src/tests/ | grep '^test_' | xargs | tr " " ",") \
		$(DOCKER_NETWORK_ARG) \
        --db_host=$(POSTGRES_HOST) \
        --db_user=$(POSTGRES_USER) \
        --db_password=$(POSTGRES_PASSWORD)
else
docker:
	echo ""

test: docker
	./runtests-odoo.sh $(RUN_RYE_ARG) -i $$(ls src/tests/ | grep '^test_' | xargs | tr " " ",")
endif

.PHONY: test docker

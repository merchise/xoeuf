SHELL := /bin/bash
PATH := $(HOME)/.rye/shims:$(PATH)

PYTHON_FILES := $(shell find xoeuf/ -type f -name '*.py')
RUN_RYE ?=
EXEC ?= rye run

install:
	rye sync
	if [ -d ../odoo ]; then \
		$(EXEC) pip install -r ../odoo/requirements.txt; \
		$(EXEC) pip install -e ../odoo; \
	fi
.PHONY: install


LINT_TOOL ?= ruff
LINT_PATHS ?= xoeuf/ tests/

format:
	@$(EXEC) $(LINT_TOOL) check --fix --preview $(LINT_PATHS)
	@$(EXEC) $(LINT_TOOL) format $(LINT_PATHS)
.PHONY: format-python

lint:
	@$(EXEC) $(LINT_TOOL) format --check $(LINT_PATHS)
	@$(EXEC) $(LINT_TOOL) check --preview $(LINT_PATHS)
.PHONY: lint


# You can tweak these defaults in '.envrc' or by passing them to 'make'.
POSTGRES_USER ?= $(USER)
POSTGRES_PASSWORD ?= $(USER)
POSTGRES_HOST ?= pg
ODOO_MIRROR ?= https://gitlab.com/merchise-autrement/odoo.git
PYTHON_VERSION ?= 3.8
ODOO_VERSION ?= 12.0
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
        -i $(ls tests/ | grep ^test_ | xargs | tr " " ",") \
		$(DOCKER_NETWORK_ARG) \
        --db_host=$(POSTGRES_HOST) \
        --db_user=$(POSTGRES_USER) \
        --db_password=$(POSTGRES_PASSWORD)
else
docker:
	echo ""

test: docker
	./runtests-odoo.sh $(RUN_RYE_ARG) -i $$(ls tests/ | grep ^test_ | xargs | tr " " ",")
endif

.PHONY: test docker

ARG PYTHON_VERSION=3.8
FROM python:$PYTHON_VERSION

ARG PYTHON_VERSION=3.8
ARG ODOO_VERSION=12.0
ARG ODOO_MIRROR=https://gitlab.com/merchise-autrement/odoo.git

COPY . /src/xoeuf
WORKDIR /src/xoeuf
RUN apt-get update && apt-get install -y build-essential \
    libxslt1-dev libxml2-dev libsasl2-dev \
    libjpeg-dev zlib1g-dev libldap2-dev libfreetype6-dev \
    libyaml-dev libgeos-dev libusb-dev \
    libssl-dev postgresql-client

RUN git clone -b merchise-develop-${ODOO_VERSION} --depth=1 ${ODOO_MIRROR} vendor/odoo \
    && cd vendor/odoo \
    && pip install -r requirements.txt \
    && pip install -e . \
    && cd ../../ \
    && pip install -r requirements-dev.lock

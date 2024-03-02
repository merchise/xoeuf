===================
 Development setup
===================

We use `rye`_ to setup a basic virtualenv.  Most of our tests run in the
Gitlab CI, but you can run the tests locally, provided that:

You should have a suitable PostgreSQL installation for which you can issue
``createdb``, ``dropdb`` without providing a user.  See `Recommended Postgres
setup`_.

Next to your worktree of ``xoeuf``, you have a clone of Odoo, in the branch
you want to test.  For example::

  cd ..
  git clone -b merchise-develop-12.0 https://gitlab.com/merchise-autrement/odoo.git
  cd xoeuf
  make install

This will create the virtual environment and install that branch of Odoo in
it.

The you should be able to run the tests::

  make test

Recommended Postgres setup
==========================

I recommend the following docker setup::

  #!/bin/bash

  container=pg
  image=postgis/postgis:15-3.3-alpine
  docker stop "$container" || true
  docker rm "$container" || true
  docker pull $image
  docker run \
       --detach \
       --name "$container" \
       --restart=unless-stopped \
       --shm-size 1g \
       -e POSTGRES_USER=$USER \
       -e POSTGRES_PASSWORD=$USER \
       -p 5432:5432 \
       --network host \
       -v /var/run/postgresql:/var/run/postgresql \
       "$image"


.. _rye: https://rye-up.com/

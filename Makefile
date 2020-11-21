all: test

setup:
	sudo apt install \
		libgirepository1.0-dev \
		libcairo2-dev \
		pkg-config \
		python3-dev \
		python3-venv
	python3 -m venv graft-env
	graft-env/bin/python -m pip install -r requirements.txt

test:
	graft-env/bin/python -m pytest -vv


test-full:
	graft-env/bin/python -m pytest \
		--quiet \
		--pep8 \
		--pylama \
		--pylint --pylint-rcfile=.pylintrc \

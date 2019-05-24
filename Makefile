.PHONY: build

MODULE:=ticts


all: dev style sdists doc test-unit test-coverage

dev: python setup.py develop

style: isort yapf

isort:
	isort -y

yapf:
	yapf $(MODULE)

flake8:
	python setup.py flake8

test-unit:
	py.test --cov $(MODULE) --cov-report term-missing

test-coverage:
	py.test  --cov $(MODULE) --cov-report term-missing --cov-report html

dists: sdist wheels

sdist:
	python setup.py sdist

wheels:
	python setup.py bdist_wheel

doc:
	python setup.py build_sphinx

publish:
	twine upload --repository-url https://upload.pypi.org/legacy/ dist/


clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts


clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -rf .pytest_cache/

# aliases to gracefully handle typos on poor dev's terminal
check: checks
devel: dev
develop: dev
dist: dists
install: install-system
pypi: publish
styles: style
test: test-unit
unittest: test-unit
wheel: wheels

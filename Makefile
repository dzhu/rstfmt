SHELL := bash

dist: clean
	unset stashed; \
	if [ -n "$$(git status --porcelain --ignored)" ]; then stashed=1; git stash push -qa; fi; \
	python setup.py bdist_wheel; \
	git clean -fdx -e dist; \
	if [ -n "$$stashed" ]; then git stash pop -q; fi
	twine check dist/*
	for f in dist/*.whl; do unzip -l "$$f"; done

upload:
	twine upload dist/*

test:
	rstfmt --check README.rst sample.rst
	rstfmt --test README.rst sample.rst
	black --check .
	find tests -name '*.rst' -print0 | xargs -0 rstfmt --test -v

clean:
	rm -rf build/ dist/

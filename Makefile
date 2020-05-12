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
	diff README.rst <(rstfmt README.rst)
	diff sample.rst <(rstfmt sample.rst)
	find tests -name '*.rst' -print0 | xargs -0 rstfmt --test -v

clean:
	rm -rf build/ dist/

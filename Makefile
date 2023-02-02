dist: clean
	unset stashed; \
	if [ -n "$$(git status --porcelain --ignored)" ]; then stashed=1; git stash push -qa; fi; \
	python setup.py sdist bdist_wheel; \
	python set-tgz-mtimes.py dist/*.tar.gz; \
	git clean -fdx -e dist; \
	if [ -n "$$stashed" ]; then git stash pop -q; fi
	for f in dist/*.whl; do unzip -l "$$f"; done
	for f in dist/*.tar.gz; do tar tvf "$$f"; done
	twine check dist/*

upload:
	twine upload dist/*

test:
	rstfmt --check README.rst sample.rst
	rstfmt --test README.rst sample.rst
	black --check .
	find tests -name '*.rst' -print0 | xargs -0 rstfmt --test -v

clean:
	rm -rf build/ dist/

test-upload:
	TWINE_PASSWORD=$$TEST_TWINE_PASSWORD twine upload --repository testpypi dist/*

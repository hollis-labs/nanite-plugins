PLUGINS := example bookmarks giphy oembed

.PHONY: all test lint dist plugins-json release-bundle clean

all: lint test dist

plugins-json:
	@python3 -c 'import json; print(json.dumps("$(PLUGINS)".split()))'

test:
	@for p in $(PLUGINS); do (cd $$p && GOWORK=off go test -race ./...) || exit 1; done

lint:
	@for p in $(PLUGINS); do (cd $$p && GOWORK=off go vet ./... && test -z "$$(gofmt -l .)") || exit 1; done
	python3 scripts/check-dependencies.py

dist:
	@for p in $(PLUGINS); do $(MAKE) -C $$p dist || exit 1; done

release-bundle:
	python3 scripts/release-bundle.py "$(PLUGIN)" "$(VERSION)"

clean:
	rm -rf dist

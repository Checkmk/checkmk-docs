#!/bin/bash

# Prerequisites
ifdef $(command -v asciidoctor)
$(error "no asciidoctor installed!")
endif

ifdef $(command -v slimrb)
$(error "no slim or even no ruby installed. Please run 'gem install slim'")
endif


DOCS=../checkmkdocs-styling
G_CSS=-a stylesheet=../$(DOCS)/assets/css/checkmk.css
L_CSS=-a stylesheet=../checkmk.css
TEMPLATES=$(DOCS)/templates
GENERIC_OPTIONS=-E slim -a toc=right

ATTRIBUTES=$(shell cat attributes/global_attr.adoc | sed -e "s/^\/\/.*//g" | sed -e "s/\"/\\\\\"/g" | sed -e "s/^:\([^:]*\): \(.*\)/-a \1=\"\2\"/g" | sed -e "s/^:\([^:]*\):/-a \1/g" | sed -z "s/\n/ /g" | sed -e "s/{base}/../g")

build:
	rsync -a images/ /var/www/docs/images/
	if [ -d $(DOCS) ]; then \
		rsync -a $(DOCS)/assets/ /var/www/docs/assets/; \
		asciidoctor $(G_CSS) $(ATTRBIUTES) -T $(TEMPLATES)/index $(GENERIC_OPTIONS) de/menu.asciidoc -D $(DOCS)/de/; \
		asciidoctor $(G_CSS) $(ATTRIBUTES) -T $(TEMPLATES)/index $(GENERIC_OPTIONS) en/menu.asciidoc -D $(DOCS)/en/; \
		asciidoctor $(G_CSS) $(ATTRIBUTES) -T $(TEMPLATES)/slim $(GENERIC_OPTIONS) de/$(ARTICLE).asciidoc -D /var/www/docs/de/; \
		asciidoctor $(G_CSS) $(ATTRIBUTES) -T $(TEMPLATES)/slim $(GENERIC_OPTIONS) en/$(ARTICLE).asciidoc -D /var/www/docs/en/; \
		rm -rf $(DOCS)/de; \
		rm -rf $(DOCS)/en; \
	else \
		asciidoctor $(L_CSS) $(ATTRIBUTES) de/$(ARTICLE).asciidoc; \
		asciidoctor $(L_CSS) $(ATTRIBUTES) en/$(ARTICLE).asciidoc; \
	fi

help:
	@echo "Usage:"
	@echo "make generate ARTICLE=[ARTICLENAME]"
	@echo ""
	@echo "Generates a html document from the given article in both languages and"
	@echo "puts them to '/var/www/docs/'. Take care, that you have a virtual server"
	@echo "installed to this directive."
	@echo "If there is also the styling repo available, the templates will be used."
	@echo "Otherwise the css in this repo is the fallback to generate a standalone"
	@echo "version of the given article."
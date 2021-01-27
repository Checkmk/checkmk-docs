#!/bin/bash

# Prerequisites
ifndef $(command -v asciidoctor)
$(error "no asciidoctor installed!")
endif

ifndef $(command -v slimrb)
$(error "no slim or even no ruby installed. Please run 'gem install slim'")
endif

DOCS=../checkmkdocs-styling
TEMPLATES=$(DOCS)/templates
GENERIC_OPTIONS=-E slim -a toc=right

# We want to replace the manual import of global_attr during the making of the html, but not now
#ATTRIBUTES=$(shell cat attributes/global_attr.adoc | sed -e "s/^\/\/.*//g" | sed -e "s/\"/\\\\\"/g" | sed -e "s/\</\\\\\</g" | sed -e "s/\>/\\\\\>/g" | sed -e "s/^:\([^:]*\): \(.*\)/-a \1=\"\2\"/g" | sed -e "s/^:\([^:]*\):/-a \1/g" | sed -z "s/\n/ /g" | sed -e "s/{base}/../g")
ATTRIBUTES=-a sectnums

ifneq ($(wildcard $(DOCS)),)
CSS=-a stylesheet=../$(DOCS)/assets/css/checkmk.css
OPTIONS_INDEX=$(CSS) $(ATTRIBUTES) -T $(TEMPLATES)/index $(GENERIC_OPTIONS)
OPTIONS_ARTICLE=$(CSS) $(ATTRIBUTES) -T $(TEMPLATES)/slim $(GENERIC_OPTIONS)
else
CSS=-a stylesheet=../checkmk.css
OPTIONS_ARTICLE=$(CSS) $(ATTRIBUTES) $(GENERIC_OPTIONS)
endif



default: help

html:

	@if [ -d $(DOCS) ]; then \
		@mkdir -p /var/www/docs/images; \
		@rsync -a images/ /var/www/docs/images/; \
		@mkdir -p /var/www/docs/assets; \
		rsync -a $(DOCS)/assets/ /var/www/docs/assets/; \
		asciidoctor $(OPTIONS_INDEX) de/menu.asciidoc -D $(DOCS)/de/; \
		asciidoctor $(OPTIONS_INDEX) en/menu.asciidoc -D $(DOCS)/en/; \
	fi

	asciidoctor $(OPTIONS_ARTICLE) de/$(ARTICLE).asciidoc -D ./localbuild/de/
	asciidoctor $(OPTIONS_ARTICLE) en/$(ARTICLE).asciidoc -D ./localbuild/en/

	@if [ -d $(DOCS) ]; then \
		rm -rf $(DOCS)/de; \
		rm -rf $(DOCS)/en; \
	fi


help:
	@echo "Usage:"
	@echo "make html ARTICLE=[ARTICLENAME]"
	@echo ""
	@echo "Generates a html document from the given article in both languages and"
	@echo "puts them to '/var/www/docs/'. Take care, that you have a virtual server"
	@echo "installed to this directive."
	@echo "If there is also the styling repo available, the templates will be used."
	@echo "Otherwise the css in this repo is the fallback to generate a standalone"
	@echo "version of the given article."
	@echo "The output files will be located in the folder ./localbuild/"

#!/bin/bash

G_CSS=-a stylesheet=../../docs.checkmk.com/assets/css/checkmk.css
L_CSS=-a stylesheet=../checkmk.css
DOCS=../docs.checkmk.com
TEMPLATES=$(DOCS)/templates
GENERIC_OPTIONS=-E slim -a toc=right

METADATA=-a base=.. \
	-a icons \
	-a imagesdir=../images \
	-a iconsdir=../images/icons \
	-a source-highlighter=highlightjs \
	-a sectnums \
	-a sectnumlevels=2 \
	-a toclevels=3 \
	-a sectanchors

PRODUCT_REPLACEMENTS=-a CMK=Checkmk \
	-a CRE="pass:q,m[image:CRE.svg[CRE,title=Checkmk Raw Edition,width=20] *Checkmk Raw Edition*]" \
	-a CFE="pass:q,m[image:CFE.svg[CFE,title=Checkmk Enterprise Free Edition,width=20] *Checkmk Enterprise Free Edition*]" \
	-a CSE="pass:q,m[image:CSE.svg[CSE,title=Checkmk Enterprise Standard Edition,width=20] *Checkmk Enterprise Standard Edition*]" \
	-a CME="pass:q,m[image:CME.svg[CME,title=Checkmk Enterprise Managed Services Edition,width=20] *Checkmk Enterprise Managed Services Edition*]" \
	-a CEE="pass:q,m[image:CEE.svg[CEE,title=Checkmk Enterprise Editions,width=20] *Checkmk Enterprise Editions*]"

IMAGES=-a image-left=.inline-image \
	-a image-border=.border

RELATED=-a related-start="<div class=\"dropdown dropdown__related\"><button class=\"btn btn-primary dropdown-toggle\" type=\"button\" id=\"relatedMenuButton\" data-toggle=\"dropdown\" aria-haspopup=\"true\" aria-expanded=\"false\">Related Articles</button><div class=\"dropdown-menu dropdown-menu-right\" aria-labelledby=\"relatedMenuButton\">" \
	-a related-end="</div></div>"

STATES=-a OK="pass:q[[.state0]\#OK\#]" \
	-a WARN="pass:q[[.state1]\#WARN\#]" \
	-a CRIT="pass:q[[.state2]\#CRIT\#]" \
	-a UNKNOWN="pass:q[[.state3]\#UNKNOWN\#]" \
	-a PEND="pass:q[[.statep]\#PEND\#]" \
	-a UP="pass:q[[.hstate0]\#UP\#]" \
	-a DOWN="pass:q[[.hstate1]\#DOWN\#]" \
	-a UNREACH="pass:q[[.hstate2]\#UNREACH\#]"

VERSIONS=-a v128="pass:q[[.new]\#1.2.8\#]" \
	-a v14="pass:q[[.new]\#1.4.0\#]" \
	-a v15="pass:q[[.new]\#1.5.0\#]" \
	-a v16="pass:q[[.new]\#1.6.0\#]" \
	-a v17="pass:q[[.new]\#1.7.0\#]"

BLOCKS=-a file="source,bash,subs=\"attributes,quotes,macros\""
	shell="source,shell,subs=\"quotes,macros,attributes\""
	shell-raw="source,shell,subs=\"verbatim,attributes\""
	sql="source,sql,subs=\"attributes\""
	c-user="user@host:~$"
	c-omd="pass:[<span class=\"hljs-meta\">OMD[mysite]:~$</span>]"
	c-local="OMD[central]:~$"
	c-remote1="OMD[remote1]:~$"
	c-remote2="OMD[remote2]:~$"
	c-root="root@linux\#""

ATTRIBUTES=$(METADATA) $(PRODUCT_REPLACEMENTS) $(IMAGES) $(RELATED) $(STATES) $(VERSIONS) $(BLOCKS)

build:
	if [ -d $(DOCS) ]; then \
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
	@echo "generate ARTICLE=myArticle.asciidoc			- Generates an html file of the given article"
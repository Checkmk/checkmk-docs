#!/bin/python3
# encoding: utf-8
# 2025 Esther Seyffarth for Checkmk GmbH

"""
Script to count different types of code blocks across the User Guide.

It reads the entire source directory of the User Guide and attempts to collect
all file and code blocks from each German asciidoc file.
For each category, a separate list of all code blocks with pointers to
their source files is generated.
In the lists, all blocks are presented with a copy button.

ATTENTION: When using this script, make sure that the list of
code and file block types is up to date. The categories used here should
be the same ones that you can find in checkmk-docs/src/includes/en/global_attr.adoc.
"""

from pathlib import Path
import re
import os


##############################################################################
# Path definitions
##############################################################################

SRCDIR = "{}/git/checkmk-docs/src".format(str(Path.home()))
OUTPATH_FILES = "{}/common/de/file_blocks_type_{}_per_user_guide_article.asciidoc".format(SRCDIR, "{}")
OUTPATH_CODES = "{}/common/de/code_blocks_type_{}_per_user_guide_article.asciidoc".format(SRCDIR, "{}")


##############################################################################
# File and block type definitions
##############################################################################

# Lists of file box types and code box types are populated from global_attr.adoc.
# Attention: When that file changes, update these lists here to make sure the
# script collects all relevant block types!
file_box_types = ["file",
                  "python",
                  "sql",
                  "apache",
                  "ini",
                  "yaml",
                  "psscript",
                  "bash"]
code_box_types = ["shell",
                  "shell-raw",
                  "powershell",
                  "cmd",
                  "pycon"]


##############################################################################
# Regex definitions
##############################################################################

# Pattern for a line with file block opening and optional attributes like highlighting
FILE_TYPE_LINE_PATTERN = r"(\[\{{({})\}}[^\]]*\]\s*\n)".format("|".join(file_box_types))

# Pattern for a line with file block opening, but no type specified
FILE_UNTYPED_LINE_PATTERN = r"(\[([^\]\{\}]*)\]\s*\n)"

# Pattern for an entire file block
FILE_BLOCK_PATTERN = re.compile(
    r"""

    (?<=\n) # must immediately follow a line break
    (\.[^\n]+\n)? # optional line containing a dot-prefixed file name
      ({}|{}) # calling .format() on this entire string inserts the FILE_TYPE_LINE_PATTERN and FILE_UNTYPED_LINE_PATTERN here to correctly recognize the block header
      ----\s*\n+ # file header separator line
      ([^\n]*?\n)+? # contents of the file itself (this is what we will want to copy later)
      ---- # file footer separator line
      """.format(FILE_TYPE_LINE_PATTERN, FILE_UNTYPED_LINE_PATTERN),
    re.VERBOSE
)

# Pattern for a line with code block opening and optional attributes like highlighting
CODE_TYPE_LINE_PATTERN = r"(\[\{{(({}))\}}[^\]]*\]\s*\n)".format("|".join(code_box_types))

# Pattern for an entire code block
CODE_BLOCK_PATTERN = re.compile(
    r"""

    (?<=\n) # must immediately follow a line break
    {} # calling .format() on this entire string inserts the CODE_TYPE_LINE_PATTERN here to correctly recognize the block header
      ----\s*\n+ # code block header separator line
      (([^\n]*?\n)+?) # contents of the code block itself
      ---- # code block footer separator line
   """.format(CODE_TYPE_LINE_PATTERN),
    re.VERBOSE
)


#################################################################################
# Logic starts here
##############################################################################

extracted_file_blocks = dict()
extracted_code_blocks = dict()

for root, dirs, files in os.walk(SRCDIR):
    for file in files:
        f = os.path.join(root, file)
        if f.endswith(".asciidoc") and "/de/" in f and not file.startswith("file_blocks_") and not file.startswith("code_blocks_"):
            with open(f, "r", encoding="utf8") as infile:
                current_file_blocks_count = 0
                current_code_blocks_count = 0
                content = infile.read()
                all_file_blocks = re.finditer(FILE_BLOCK_PATTERN, content)
                for file_block in all_file_blocks:
                    current_file_blocks_count += 1
                    file_block_str = file_block.group().strip()
                    file_type = re.search(FILE_TYPE_LINE_PATTERN, file_block_str)
                    if file_type is not None:
                        # If we encounter a known file type, we grab the type
                        # from the header line and use it to categorize the block.
                        file_type_str = file_type.group(2)
                    else:
                        # Otherwise, we assign the "uncategorized" type to this block.
                        file_header_line = re.search(FILE_UNTYPED_LINE_PATTERN, file_block_str)
                        if file_header_line is not None and file_header_line.group().strip() != "[...]":
                            file_type_str = "uncategorized"
                        else:
                            # We need to catch cases where "[...]" inside file
                            # blocks is incorrectly identified as a new file block
                            # header.
                            # print("Special case!\n{}".format(file_block_str))
                            file_type_str = "error"
                            # We ignore these incorrectly-collected blocks and
                            # move to the next iteration of the for loop.
                            # Comment out the "continue" command to instead collect
                            # these blocks in their own list file, with the type
                            # "error".
                            continue

                    file_contents = re.split("\n----", file_block_str)[1]
                    if file_type_str not in extracted_file_blocks:
                        extracted_file_blocks[file_type_str] = dict()
                    if f not in extracted_file_blocks[file_type_str]:
                        extracted_file_blocks[file_type_str][f] = []
                    extracted_file_blocks[file_type_str][f].append(file_block_str.strip())

                all_code_blocks = re.finditer(CODE_BLOCK_PATTERN, content)
                for code_block in all_code_blocks:
                    current_code_blocks_count += 1
                    code_block_str = code_block.group().strip()
                    code_type = re.search(CODE_TYPE_LINE_PATTERN, code_block_str).group(2)
                    code_contents = re.split("\n----", code_block_str)[1]
                    if code_type not in extracted_code_blocks:
                        extracted_code_blocks[code_type] = dict()
                    if f not in extracted_code_blocks[code_type]:
                        extracted_code_blocks[code_type][f] = []
                    extracted_code_blocks[code_type][f].append(code_block_str.strip())  

                print("Found {} file blocks and {} code blocks in file {}.".format(current_file_blocks_count, current_code_blocks_count, f))


##############################################################################
# Write results to outfiles
##############################################################################

for file_type in extracted_file_blocks:
    outpath = OUTPATH_FILES.format(file_type)
    with open(outpath, "w", encoding="utf8") as outfile:
        outfile.write("""// -*- coding: utf-8 -*-
include::global_attr.adoc[]
= {} file blocks extracted from User Guide articles
:title: {} file blocks extracted from user guide articles
:description: List of {} file blocks appearing across the user guide. For testing purposes.


""".format(file_type, file_type, file_type))
        for file in extracted_file_blocks[file_type]:
            outfile.write("=== {}\n(go to xref:{}#[article])\n".format(file.split(".")[0].rsplit("/", 1)[1], file.split(".")[0].rsplit("/", 1)[1]))
            for block in extracted_file_blocks[file_type][file]:
                block_with_button_markup = re.sub(r"({}|{})".format(FILE_TYPE_LINE_PATTERN, FILE_UNTYPED_LINE_PATTERN), r"[.copybutton]\n\1", block, 1)
                outfile.write("\n{}\n\n".format(block_with_button_markup.strip()))

for code_type in extracted_code_blocks:
    outpath = OUTPATH_CODES.format(code_type)
    with open(outpath, "w", encoding="utf8") as outfile:
        outfile.write("""// -*- coding: utf-8 -*-
include::global_attr.adoc[]
= {} code blocks extracted from User Guide articles
:title: {} code blocks extracted from user guide articles
:description: List of {} code blocks appearing across the user guide. For testing purposes.


""".format(code_type, code_type, code_type))
        for file in extracted_code_blocks[code_type]:
            outfile.write("=== {}\n(go to xref:{}#[article])\n".format(file.split(".")[0].rsplit("/", 1)[1], file.split(".")[0].rsplit("/", 1)[1]))
            for block in extracted_code_blocks[code_type][file]:
                block_with_button_markup = re.sub(CODE_TYPE_LINE_PATTERN, r"[.copybutton]\n\1", block, 1)
                outfile.write("\n{}\n\n".format(block_with_button_markup.strip()))
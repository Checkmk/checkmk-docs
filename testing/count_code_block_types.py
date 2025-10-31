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

ASTERISKY_COMMAND_PATTERN = re.compile(r"(?<=\n----\n)([^\n]*?\s\*[^*\n]*?\*( [^\n]*?)?)(?=\n)")

UNESCAPED_BACKTICK_PATTERN = re.compile(r"(?<!pass:\[)`(?!\])")

UNESCAPED_HASH_PATTERN = re.compile(r"(?<!pass:\[)#")
FUNCTIONAL_HASH_PATTERN = re.compile(r"\[(green|yellow|red|cpignore)\]#[^#]+#")

WINDOWSY_PROMPT_PATTERN = re.compile(r"(?<=\n)((PS|C:)[^>]*?>([^\n]*?))(?=\n)")

# Attention, this is yet another list that needs to match the list of
# macros defined in global_attr.adoc.
LINUXY_PROMPTS = ["c-user",
                  "c-omd",
                  "c-local",
                  "c-remote1",
                  "c-remote2",
                  "c-myremote1",
                  "c-myremote2",
                  "c-root",
                  "c-ubuntu"]
KNOWN_LINUXY_PROMPT_LINE_PATTERN = re.compile(r"(?<=\n)({{({})}})( +?[^\n]*?)?(?=\n)".format("|".join(LINUXY_PROMPTS)))

PYTHON_REPL_PATTERN = re.compile(r"(?<=\n)>>>([^\n]*?)(?=\n)")

#################################################################################
# Helper functions
##############################################################################
def add_to_collection(collection_dict, block_type, file, block):
    if block_type not in collection_dict:
        collection_dict[block_type] = dict()
    if file not in collection_dict[block_type]:
        collection_dict[block_type][file] = []
    collection_dict[block_type][file].append(block)
    return collection_dict

#################################################################################
# Logic starts here
##############################################################################

def collect_code_and_file_blocks(verbose=True):

    extracted_file_blocks = dict()
    extracted_code_blocks = {"shell": dict(),
                             "shell-raw": dict(),
                             "powershell": dict(),
                             "cmd": dict(),
                             "pycon": dict()}

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
                        extracted_file_blocks = add_to_collection(extracted_file_blocks, file_type_str, f, file_block_str.strip())

                    all_code_blocks = re.finditer(CODE_BLOCK_PATTERN, content)
                    for code_block in all_code_blocks:
                        current_code_blocks_count += 1
                        code_block_str = code_block.group().strip()
                        code_type = re.search(CODE_TYPE_LINE_PATTERN, code_block_str).group(2)
                        extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, f, code_block_str.strip())

                    if verbose:
                        print("Found {} file blocks and {} code blocks in file {}.".format(current_file_blocks_count, current_code_blocks_count, f))
    print("Collected all recognized code and file blocks from {}.".format(SRCDIR))
    return extracted_file_blocks, extracted_code_blocks


##############################################################################
# Write results to outfiles
##############################################################################

def write_results(extracted_file_blocks, extracted_code_blocks):
    for file_type in extracted_file_blocks:
        outpath = OUTPATH_FILES.format(file_type)
        with open(outpath, "w", encoding="utf8") as outfile:
            outfile.write("""// -*- coding: utf-8 -*-
include::global_attr.adoc[]
= {} file blocks extracted from User Guide articles
:title: {} file blocks extracted from user guide articles
:description: List of {} file blocks appearing across the user guide. For testing purposes.\n\n\n""".format(
        file_type, file_type, file_type))
            for file in extracted_file_blocks[file_type]:
                outfile.write("=== {}\n(go to xref:{}#[article])\n".format(file.split(".")[0].rsplit("/", 1)[1], file.split(".")[0].rsplit("/", 1)[1]))
                for block in extracted_file_blocks[file_type][file]:
                    block_with_button_markup = re.sub(r"({}|{})".format(FILE_TYPE_LINE_PATTERN, FILE_UNTYPED_LINE_PATTERN), r"[.copybutton]\n\1", block, 1)
                    outfile.write("\n{}\n\n".format(block_with_button_markup.strip()))
        print("Wrote file blocks of type '{}' to '{}'.".format(file_type, outpath))

    for code_type in extracted_code_blocks:
        outpath = OUTPATH_CODES.format(code_type)
        with open(outpath, "w", encoding="utf8") as outfile:
            outfile.write("""// -*- coding: utf-8 -*-
include::global_attr.adoc[]
= {} code blocks extracted from User Guide articles
:title: {} code blocks extracted from user guide articles
:description: List of {} code blocks appearing across the user guide. For testing purposes.\n\n\n""".format(
        code_type, code_type, code_type))
            for file in extracted_code_blocks[code_type]:
                outfile.write("=== {}\n(go to xref:{}#[article])\n(de) file for direct editing access: file://{}\n(en) file for direct editing access: file://{}\n".format(file.split(".")[0].rsplit("/", 1)[1], file.split(".")[0].rsplit("/", 1)[1], file, file.replace("/de/", "/en/")))
                for block in extracted_code_blocks[code_type][file]:
                    block_with_button_markup = re.sub(CODE_TYPE_LINE_PATTERN, r"[.copybutton]\n\1", block, 1)
                    outfile.write("\n{}\n\n".format(block_with_button_markup.strip()))
        print("Wrote code blocks of type '{}' to '{}'.".format(code_type, outpath))

###############################################################################
# Identify complicated blocks that need individual scrutiny
############################################################################### 
def collect_complicated_blocks(extracted_code_blocks, extracted_file_blocks):

    for orig_code_type in ["shell", "shell-raw", "powershell", "cmd", "pycon"]:
        for file in extracted_code_blocks[orig_code_type]:
            for block in extracted_code_blocks[orig_code_type][file]:
                if orig_code_type in ["powershell", "cmd"]:
                    code_type = None

                    # Handle powershell-type boxes that contain Python REPL elements like >>>
                    if re.search(PYTHON_REPL_PATTERN, block):
                        code_type = "{}-contains-python-repl".format(orig_code_type)
                        extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)

                    elif re.search(WINDOWSY_PROMPT_PATTERN, block):
                        # Handle blocks that contain an unescaped hash anywhere inside
                        if re.search(UNESCAPED_HASH_PATTERN, block):
                            functional_hashes_count = len(re.findall(FUNCTIONAL_HASH_PATTERN, block))*2
                            if functional_hashes_count < len(re.findall(UNESCAPED_HASH_PATTERN, block)):
                                code_type = "{}-has-hashes".format(orig_code_type)
                                extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)
                        
                        # Handle blocks that contain an unescaped backtick anywhere inside
                        if re.search(UNESCAPED_BACKTICK_PATTERN, block):  
                            code_type = "{}-has-backticks".format(orig_code_type)
                            extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)

                        # Handle blocks that contain formatting asterisks 
                        if re.search(ASTERISKY_COMMAND_PATTERN, block):
                            code_type = "{}-has-asterisks-in-commands".format(orig_code_type)
                            extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)

                        # Handle blocks that have prompts without commands following them
                        command_content = re.search(WINDOWSY_PROMPT_PATTERN, block).group(3)
                        if command_content is None or command_content.strip() == "":
                            code_type = "{}-prompt-lacks-command".format(orig_code_type)
                            extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)
                        
                        # Handle blocks with multiple prompt lines
                        prompt_lines = re.findall(WINDOWSY_PROMPT_PATTERN, block)
                        if len(prompt_lines) > 1:
                            code_type = "{}-multiple-prompt-lines".format(orig_code_type)
                            extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)
                
                if orig_code_type in ["shell", "shell-raw"]:
                    code_type = None

                    # Handle shell-type boxes that contain Python REPL elements like >>>
                    if re.search(PYTHON_REPL_PATTERN, block):
                        code_type = "{}-contains-python-repl".format(orig_code_type)
                        extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)

                    elif re.search(KNOWN_LINUXY_PROMPT_LINE_PATTERN, block):
                        # Handle blocks that contain an unescaped hash anywhere inside
                        if re.search(UNESCAPED_HASH_PATTERN, block):
                            functional_hashes_count = len(re.findall(FUNCTIONAL_HASH_PATTERN, block))*2
                            if functional_hashes_count < len(re.findall(UNESCAPED_HASH_PATTERN, block)):
                                code_type = "{}-has-hashes".format(orig_code_type)
                                extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)
                        
                        # Handle blocks that contain an unescaped backtick anywhere inside
                        if re.search(UNESCAPED_BACKTICK_PATTERN, block):
                            code_type = "{}-has-backticks".format(orig_code_type)
                            extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)

                        # Handle blocks that contain formatting asterisks
                        if re.search(ASTERISKY_COMMAND_PATTERN, block):
                            code_type = "{}-has-asterisks-in-commands".format(orig_code_type)
                            extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)

                        # Handle blocks that have prompts without commands following them
                        command_content = re.search(KNOWN_LINUXY_PROMPT_LINE_PATTERN, block).group(3)
                        if command_content is None or command_content.strip() == "":
                            code_type = "{}-prompt-lacks-command".format(orig_code_type)
                            extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)

                        # Handle blocks with multiple prompt lines
                        prompt_lines = re.findall(KNOWN_LINUXY_PROMPT_LINE_PATTERN, block)
                        if len(prompt_lines) > 1:
                            code_type = "{}-multiple-prompt-lines".format(orig_code_type)
                            extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)

                    # Handle shell boxes without a macro-based prompt
                    else:
                        code_type = "{}-lacks-macro-prompts".format(orig_code_type)
                        # Handle blocks that match a windows-style prompt
                        if re.search(WINDOWSY_PROMPT_PATTERN, block):
                            code_type = "{}-needs-cmd".format(orig_code_type)
                        extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)

                if orig_code_type in ["pycon"]:
                    code_type = None

                    # Handle pycon-type boxes that contain Python REPL elements like >>>
                    if re.search(PYTHON_REPL_PATTERN, block):
                        # Handle blocks that contain an unescaped hash anywhere inside
                        if re.search(UNESCAPED_HASH_PATTERN, block):
                            functional_hashes_count = len(re.findall(FUNCTIONAL_HASH_PATTERN, block))*2
                            if functional_hashes_count < len(re.findall(UNESCAPED_HASH_PATTERN, block)):
                                code_type = "{}-has-hashes".format(orig_code_type)
                                extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)
                        
                        # Handle blocks that contain an unescaped backtick anywhere inside
                        if re.search(UNESCAPED_BACKTICK_PATTERN, block):
                            code_type = "{}-has-backticks".format(orig_code_type)
                            extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)

                        # Handle blocks that contain formatting asterisks 
                        if re.search(ASTERISKY_COMMAND_PATTERN, block):
                            code_type = "{}-has-asterisks-in-commands".format(orig_code_type)
                            extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)

                        # Handle blocks that have prompts without commands following them
                        command_content = re.search(PYTHON_REPL_PATTERN, block).group(1)
                        if command_content is None or command_content.strip() == "":
                            code_type = "{}-prompt-lacks-command".format(orig_code_type)
                            extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)
                        
                        # Handle blocks with multiple prompt lines
                        prompt_lines = re.findall(PYTHON_REPL_PATTERN, block)
                        if len(prompt_lines) > 1:
                            code_type = "{}-multiple-prompt-lines".format(orig_code_type)
                            extracted_code_blocks = add_to_collection(extracted_code_blocks, code_type, file, block)

    return extracted_code_blocks, extracted_file_blocks

if __name__ == "__main__":
    extracted_file_blocks, extracted_code_blocks = collect_code_and_file_blocks(False)
    extracted_code_blocks, extracted_file_blocks = collect_complicated_blocks(extracted_code_blocks, extracted_file_blocks)
    write_results(extracted_file_blocks, extracted_code_blocks)
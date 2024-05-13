#!/usr/bin/env python3
# encoding: utf-8
"""Tool to check missing translations"""

from sys import argv as sysargs
from sys import stdout as sysout
from sys import exit as sysexit
from os import listdir, system
from pathlib import Path
from subprocess import check_output as check
from datetime import datetime
import argparse
import git
from typing import NamedTuple

DOCS_ROOT = git.Repo("./", search_parent_directories=True)
DOCS = git.Git(DOCS_ROOT.working_dir)
EXCLUDES = (
    "check_",
    "draft_",
    "cma_",
    "legacy_",
    ".",
    "internal_",
    "missing",
    "index",
    "deprecated_",
    "training_",
    "global_attr",
)
DEFAULT_LANGUAGES = ["de", "en"]
MARKER = ("only-de", "only-en", "translated", "content_sync", "content-sync")
MARKER_LANG = dict(de=MARKER[0], en=MARKER[1])
DOC_TYPES = ["common", "includes", "onprem", "saas"]


class GitCommits:
    def __init__(self):
        self.Commit = NamedTuple(
            "Commit", [("name", str), ("date", str), ("id", str), ("message", str)]
        )
        self.Translate = NamedTuple(
            "Translate", [("id", str), ("date", str), ("files", dict)]
        )
        self.translated_markers = list()
        self.last_translation = dict()
        self.commits = list()
        self.default_branch = (
            check("git branch --show-current", shell=True).decode("utf-8").strip("\n")
        )

    def _create_translated_file_list(self):
        for _id, new_date, files in self.translated_markers:
            for article in files:
                article = (
                    article.replace("./", "").replace("de/", "").replace("en/", "")
                )
                self.last_translation.setdefault(article, new_date)
                date = self.last_translation[article]
                date = max(date, new_date)
        return self.last_translation

    def get_translated_markers(self, branch=None):
        if not branch:
            branch = self.default_branch
        commits = DOCS_ROOT.iter_commits(
            branch,
            paths=f"{DOCS_ROOT.working_dir}",
            grep=r"^translated\|^content-sync\|^content_sync",
        )
        for commit in commits:
            self.translated_markers.append(
                self.Translate(commit.hexsha, commit.committed_date, commit.stats.files)
            )
        return self._create_translated_file_list()

    def _get_log_as_list_of_dicts(self, max_age, pretty, file):
        commits = list()
        raw = DOCS.log(f"--since={max_age}", pretty, "--", file)
        raw_list = raw.replace("\n", "").split("||||")
        for entry in raw_list:
            if not entry:
                continue
            name, date, id, summary = entry.split("||")
            commits.append(dict(name=name, date=date, id=id[:6], summary=summary))

        return commits

    def get_file_commits(self, file, lang, max_age, branch=None):
        file_commits = list()
        commit_hashes = list()
        commit_messages = list()
        if not branch:
            branch = self.default_branch
        commits = self._get_log_as_list_of_dicts(
            max_age,
            "--pretty=format:%an||%ct||%H||%s||||",
            f"{DOCS_ROOT.working_dir}/{lang}/{file}",
        )
        for commit in commits:
            commit_hashes.append(commit.get("id"))
            commit_messages.append(commit.get("summary"))
            file_commits.append(
                self.Commit(
                    commit.get("name"),
                    commit.get("date"),
                    commit.get("id"),
                    commit.get("summary"),
                )
            )

        return commit_messages, commit_hashes, file_commits


class Article:
    def __init__(self, filename):
        self.filename = filename
        self.paths = dict()
        self.lang = list()
        self.last_translation = "1104537600"
        self.commits = dict()
        self.commits_clean = True
        self.untranslated = dict(de=False, en=False)


class ColorizedOutput(object):
    """Write out fancy stuff to the command line"""

    def __init__(self, box_size=90, tty=True):
        self.box_size = box_size
        bold = "\033[1m"
        self.colors = dict(
            bold=bold,
            normal="\033[0m",
            black="\033[30m",
            red=bold + "\033[31m",
            green=bold + "\033[32m",
            yellow=bold + "\033[33m",
            blue=bold + "\033[34m",
            magenta=bold + "\033[35m",
            cyan=bold + "\033[36m",
            white=bold + "\033[37m",
            bg_red="\033[41m",
            bg_blue="\033[44m",
            de="Deutsch",
            en="English",
            box_top="┌" + "─" * box_size + "┐\n",
            box_separator="├" + "─" * box_size + "┤\n",
            box_bottom="└" + "─" * box_size + "┘\n",
            box_borders="\033[500D|\033[{}C|\n".format(box_size),
            box_size=box_size,
            box_size_half=box_size / 2,
        )

        if not tty:
            self.colors = {key: "" for key in self.colors}

        self.languages = dict(
            de="{bg_red}{black} ⚒ {yellow}{de}{black} ⚒ {normal}".format(**self.colors),
            en="{bg_blue}{white} ✭ {white}{en}{white} ✭ {normal}".format(**self.colors),
        )
        self.colors.update(de=self.languages["de"], en=self.languages["en"])

    def line(self, line, **kwargs):
        """Write out a single line."""
        colors = self.colors.copy()
        colors.update(kwargs)
        try:
            return sysout.write(line.format(**colors))
        except:  # noqa E722
            print(colors)
            raise

    def box_element(self, box_element):
        """Write Box elements"""
        return sysout.write(self.colors[box_element])

    def article_details(self, commits, lang):
        if lang == "de":
            self.line("| {de}{box_borders}")
        else:
            self.line("| {en}{box_borders}")

        self.line("|{box_borders}")
        for entry in commits:
            prefix = entry[0]
            commit = entry[1]
            message_length = self.box_size - 39
            attr = dict(
                prefix=prefix,
                commit=commit,
                message=commit.message[:message_length],
                commit_date=datetime.fromtimestamp(int(commit.date)).strftime(
                    "%Y-%m-%d %H:%M"
                ),
            )

            summary = (
                "{magenta}{commit.id} {blue}{commit_date} {yellow}{commit.name}"
                + "\033[500D|\033[38C {normal}{message}{box_borders}"
            )
            if prefix:
                self.line("| {green}c " + summary, **attr)
            else:
                self.line("| {red}d " + summary, **attr)

    def summary_details(
        self,
        commits,
        untranslated=False,
        filename=None,
        dirty_commits=0,
        write=False,
        last_translation=None,
    ):

        for entry in commits:
            clean = entry[0]
            if not clean:
                dirty_commits += 1

            if clean or untranslated:
                continue

        if dirty_commits >= 1 and write:
            hint = f" - {dirty_commits} commits are untranslated"
            self.line(
                "| {bold}{filename}{normal} "
                + "\033[500D|\033[30C{red}dirty{normal}{bold}{hint}{normal}{box_borders}",
                **dict(filename=filename, hint=hint),
            )
        elif write:
            if last_translation == "1104537600":
                hint = " - Never marked as translated"
            else:
                date = datetime.fromtimestamp(int(last_translation)).strftime(
                    "%Y-%m-%d %H:%M"
                )
                hint = f" - last full translation: {date}"
            self.line(
                "| {bold}{filename}{normal} \033[500D|\033[30C{green}clean{normal}{bold}{hint}"
                + "{normal}{box_borders}",
                **dict(filename=filename, hint=hint),
            )

        return dirty_commits


def parse_arguments(argv):
    """Usage: translate [ARTICLE [COMMIT-NR]]"""
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "article_or_hash",
        type=str,
        help="Article name or commit hash. The"
        + " script tries to detect wether"
        + " it's one or another and creates the corresponding output.",
        nargs="?",
    )
    parser.add_argument(
        "-a", "--article", default="", help="A specific article to show"
    )
    parser.add_argument(
        "-c",
        "--commit",
        default="",
        help="Show the diff of an entry of an articles details",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Activate debugging")
    parser.add_argument(
        "-w",
        "--width",
        default=85,
        help="Adjust the width to use more of your screen. Default is set to 85 characters",
    )

    return parser.parse_args(argv)


def get_article_names():
    article_names = dict()
    for doc_type in DOC_TYPES:
        for lang in DEFAULT_LANGUAGES:
            for article in sorted(
                listdir(f"{DOCS_ROOT.working_dir}/src/{doc_type}/{lang}")
            ):
                article = article.replace(".asciidoc", "")
                if article.startswith((EXCLUDES)):
                    continue
                article_names.setdefault(article, list())
                article_names[article].append(lang)
    return article_names


def get_articles(article=None) -> list:
    articles = list()

    if article:
        article_exists = False
        instance = Article(f"{article}.asciidoc")
        for language in DEFAULT_LANGUAGES:
            article_path = f"{language}/{article}.asciidoc"
            instance.paths[language] = article_path
            for doc_type in DOC_TYPES:
                if Path(
                    f"{DOCS_ROOT.working_dir}/src/{doc_type}/{article_path}"
                ).exists():
                    article_exists = True
            instance.lang.append(language)
        if article_exists:
            articles.append(instance)
        else:
            sysexit(f'Article "{article}" does not exist!')
    else:
        article_names = get_article_names()
        for article, languages in article_names.items():
            instance = Article(f"{article}.asciidoc")
            for language in DEFAULT_LANGUAGES:
                if language in languages:
                    instance.paths[language] = f"{language}/{article}.asciidoc"
                    instance.lang.append(language)
            articles.append(instance)

    return articles


def dirty_commit(commit, test_ids, test_messages, except_marker):
    message_to_check = commit.message.split("\n")[0]
    if commit.id in test_ids:
        return False
    elif message_to_check.startswith(MARKER) and not message_to_check.startswith(
        except_marker
    ):
        return False

    for message in test_messages:
        if message_to_check[:20] == message[:20]:
            return False

    return True


def get_article_diff(article):
    commits = dict(de=list(), en=list())
    state = True
    for combination in [("de", "en"), ("en", "de")]:
        lang, test = combination
        for commit in article.commits.get(lang, []):
            if dirty_commit(
                commit,
                article.commits.get(f"{test}_ids", []),
                article.commits.get(f"{test}_messages", []),
                MARKER_LANG[test],
            ):
                if not article.commits.get(f"{test}_ids"):
                    article.untranslated[lang] = True
                commits[lang].append((False, commit))
                state = False
            else:
                commits[lang].append((True, commit))

    return state, commits


def identify_positional(argument, for_type):
    if argument in get_article_names() and for_type == "article":
        return argument
    elif for_type == "commit":
        import re

        unknown = re.compile(r"[0-9a-f]{6,64}")
        if unknown.search(argument):
            return argument
    return ""


def main():
    """Show info depending on input data"""
    opts = parse_arguments(sysargs[1:])

    repo = GitCommits()
    repo.get_translated_markers()
    write = ColorizedOutput(box_size=int(opts.width), tty=sysout.isatty())

    if opts.article_or_hash:
        opt_commit = identify_positional(opts.article_or_hash, for_type="commit")
        opt_article = identify_positional(opts.article_or_hash, for_type="article")
    else:
        opt_commit = opts.commit
        opt_article = opts.article

    if opt_commit:
        if opt_article:
            command = f"git diff {opt_commit} -- {opt_article}"
        else:
            command = f"git show {opt_commit}"

        write.line("Executing: {command}", **dict(command=command))
        system(command)
    elif opt_article:
        article = get_articles(opt_article)[0]
        last_translation = repo.last_translation.get(article.filename)
        if last_translation:
            article.last_translation = last_translation

        for lang in article.lang:
            (
                article.commits[f"{lang}_messages"],
                article.commits[f"{lang}_ids"],
                article.commits[lang],
            ) = repo.get_file_commits(
                article.filename, lang, max_age=article.last_translation
            )
        state, commits = get_article_diff(article)

        write.line("{box_top}")
        if state:
            summary_line = (
                "| {bold}{filename}{normal}"
                + " " * 20
                + "{green}clean{normal}{box_borders}"
            )
        else:
            summary_line = (
                "| {bold}{filename}{normal}"
                + " " * 20
                + "{red}dirty{normal}{box_borders}"
            )
        write.line(
            summary_line,
            **dict(filename=article.filename.replace(".asciidoc", ""), clean=state),
        )
        write.line("{box_separator}")
        write.article_details(commits["de"], "de")
        write.line("{box_separator}")
        write.article_details(commits["en"], "en")
        write.line("{box_bottom}")

    else:
        articles = get_articles()
        without_translation_marker = list()
        write.line("{box_top}")
        for article in articles:
            last_translation = repo.last_translation.get(article.filename)
            if last_translation:
                article.last_translation = last_translation
            else:
                without_translation_marker.append(
                    article.filename.replace(".asciidoc", "")
                )
            for lang in article.lang:
                (
                    article.commits[f"{lang}_messages"],
                    article.commits[f"{lang}_ids"],
                    article.commits[lang],
                ) = repo.get_file_commits(
                    article.filename, lang, article.last_translation
                )

            state, commits = get_article_diff(article)
            if state and not opts.debug:
                continue

            dirty_count = write.summary_details(
                commits["de"],
                untranslated=article.untranslated["de"],
                filename=article.filename,
            )
            if not state or opts.debug:
                write.summary_details(
                    commits["en"],
                    untranslated=article.untranslated["de"]
                    or article.untranslated["en"],
                    filename=article.filename.replace(".asciidoc", ""),
                    dirty_commits=dirty_count,
                    write=True,
                    last_translation=article.last_translation,
                )
            write.line("{box_separator}")
        write.line("{box_bottom}")
        if without_translation_marker:
            broken_articles = ", ".join(without_translation_marker)
            write.line(
                "{red}Without translation marker{normal}: {articles}\n",
                **dict(articles=broken_articles),
            )


main()

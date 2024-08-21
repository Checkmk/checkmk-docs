#!/usr/bin/env python3
# encoding: utf-8
"""Tool for checking missing translations"""

from datetime import datetime
import logging
from pydantic import BaseModel
from os import listdir
from sys import argv, stdout, exit
from subprocess import check_output
from typing import Any
import argparse
import git

TRANSLATE_REGEX: str = r"^translated\|^content-sync\|^content_sync"
DEFAULT_DATE: int = 1104537600
EXCLUDE_COMMIT_PREFIX: tuple = (
    "translated",
    "content-sync",
    "content_sync",
    "only-de",
    "only-en",
)
UTF8: str = "utf-8"
NEWLINE: str = "\n"
VERBOSITY = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}
LOGFORMAT = "%(asctime)s Zeile %(lineno)s %(funcName)s %(levelname)s: %(message)s"
ASCIIDOC_EXTENSION: str = ".asciidoc"
CURRENT_BRANCH: str = "git branch --show-current"
INCLUDE_DOCS_TYPES: tuple = ("common", "onprem", "saas", "includes")
INCLUDE_LANGUAGES: tuple = ("de", "en")


class DocsSrcPaths(BaseModel):
    docs_root: Any = git.Repo("./", search_parent_directories=True)
    docs_repo: Any = git.Git(docs_root.working_dir)
    base: str = f"{docs_root.working_dir}/src"
    legacy: str = docs_repo


DOCSSRCPATHS = DocsSrcPaths()


class Box(BaseModel):
    size: int = 120
    half_size: float = size / 2
    top: str = "┌" + "─" * size + "┐\n"
    separator: str = "├" + "─" * size + "┤\n"
    bottom: str = "└" + "─" * size + "┘\n"
    borders: str = "\033[500D|\033[{}C|\n".format(size)


class BoxColors(BaseModel):
    bold: str = "\033[1m"
    normal: str = "\033[0m"
    black: str = "\033[30m"
    red: str = bold + "\033[31m"
    green: str = bold + "\033[32m"
    yellow: str = bold + "\033[33m"
    blue: str = bold + "\033[34m"
    magenta: str = bold + "\033[35m"
    cyan: str = bold + "\033[36m"
    white: str = bold + "\033[37m"
    bg_red: str = "\033[41m"
    bg_blue: str = "\033[44m"
    clean: str = bold + "\033[32m"
    dirty: str = bold + "\033[31m"


class BoxText(BaseModel):
    de: str = (
        "| {colors.bg_red}{colors.black} "
        + "⚒ {colors.yellow}Deutsch{colors.black} ⚒ "
        + "{colors.normal}{box.borders}"
        + "|{box.borders}"
    )
    en: str = (
        "| {colors.bg_blue}{colors.white} "
        + "✭ {colors.white}English{colors.white} ✭ "
        + "{colors.normal}{box.borders}"
        + "|{box.borders}"
    )
    docs_type_header: str = "| -------- {colors.bold}{type} --------{box.borders}"
    header: str = (
        "| {colors.bold}{article.name}{colors.normal} "
        + "\033[500D|\033[50C{color}{article.state}{colors.normal}"
        + "{colors.bold}{article.hint}{colors.normal}{box.borders}"
    )
    commit_clean: str = "| {colors.green}c "
    commit_dirty: str = "| {colors.red}d "
    commit_details: str = (
        "{colors.magenta}{commit_id} "
        + "{colors.blue}{commit_date} {colors.yellow}{commit_author}"
        + "\033[500D|\033[50C {colors.normal}{commit_message}{box.borders}"
    )
    hint_last_full_translation: str = (
        " - last full translation: {last_full_translation}"
    )
    hint_never_marked: str = " - Never marked as translated"
    hint_dirty_commits: str = " - {dirty_commit_count} commits are untranslated"


BASIC_LINE_PARAMETERS: dict[str, BoxColors | Box] = {
    "colors": BoxColors(),
    "box": Box(),
}


class Exclude(BaseModel):
    article_starts: tuple = (
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
        "featured_",
        "landingpage",
        "most_",
        "recently_",
    )


class CommitProperties(BaseModel):
    date: int = DEFAULT_DATE
    author: str = ""
    msg: str = ""
    state: str = "clean"


class ArticleCommit(BaseModel):
    commit_id: str = ""
    properties: CommitProperties = CommitProperties()


class CommitsByLanguage(BaseModel):
    de: list[ArticleCommit] = []
    en: list[ArticleCommit] = []


class Article(BaseModel):
    name: str = ""
    hint: str = ""
    state: str = "clean"
    dirty_commit_count: int = 0
    last_full_translation: int = DEFAULT_DATE
    commits_by_language: dict = {"de": [], "en": []}
    commit_ids: dict[str, list] = {"de": [], "en": []}
    commit_msgs: dict[str, list] = {"de": [], "en": []}


class ColorizedOutput:
    def __init__(self, box_size=90):
        Box.size = box_size

    def _line(self, line: str, additional_parameters: dict = {}) -> None:
        stdout.write(
            line.format(
                **additional_parameters,
                **BASIC_LINE_PARAMETERS,
            )
        )

    def _get_color_str(self, state: str):
        return BoxColors().model_dump().get(state)

    def _docs_type_header(self, docs_type: str) -> None:
        self._line(Box().top)
        self._line(
            BoxText().docs_type_header,
            additional_parameters={"type": docs_type.upper()},
        )
        self._line(Box().separator)

    def summary(self, data, complete):
        for article_name, properties in data.items():
            if properties.state == "clean" and not complete:
                continue
            self._line(
                BoxText().header,
                additional_parameters={
                    "color": self._get_color_str(properties.state),
                    "article": properties,
                },
            )
            self._line(Box().separator)
        self._line(Box().bottom)

    def details(self, article):
        text = BoxText()
        box = Box()
        msg_length = box.size - 39
        self._line(box.top)
        self._line(
            text.header,
            additional_parameters={
                "color": self._get_color_str(article.state),
                "article": article,
            },
        )
        self._line(box.separator)
        for lang, commits in article.commits_by_language.items():
            self._line(text.model_dump().get(lang))
            for commit in commits:
                if commit.properties.state == "clean":
                    prefix = text.commit_clean
                else:
                    prefix = text.commit_dirty
                self._line(
                    prefix + text.commit_details,
                    additional_parameters={
                        "commit_id": commit.commit_id,
                        "commit_date": datetime.fromtimestamp(
                            commit.properties.date
                        ).strftime("%Y-%m-%d %H:%M"),
                        "commit_author": commit.properties.author,
                        "commit_message": commit.properties.msg[:msg_length],
                    },
                )
            self._line(box.separator)

    def all_summary(self, data, complete=False):
        for docs_type in INCLUDE_DOCS_TYPES:
            if not data.get(docs_type):
                continue
            self._docs_type_header(docs_type)
            self.summary(data[docs_type], complete)

    def details_for_all_docs_type(self, data, article_name):
        for docs_type in INCLUDE_DOCS_TYPES:
            if not data.get(docs_type):
                continue
            article = data[docs_type][article_name]
            self._docs_type_header(docs_type)
            self.details(article)

    def details_for_docs_type(self, data, article_name, docs_type):
        article = data[docs_type][article_name]
        self._docs_type_header(docs_type)
        self.details(article)


class GitCommits:
    def __init__(self):
        self.default_branch = (
            check_output(CURRENT_BRANCH, shell=True).decode(UTF8).strip(NEWLINE)
        )
        self.pretty_git_log = "--pretty=format:%an||%ct||%H||%s||||"
        self.pretty_split_four = "||||"
        self.pretty_split_two = "||"

    def _split_path_to_variables(self, file):
        filepath = file.split("/")
        if len(filepath) == 2:  # old path structure
            return None, filepath[0], filepath[1]
        return filepath[1:]

    def get_translated_marker(self, article_list, path: str = DOCSSRCPATHS.base):
        commits = DOCSSRCPATHS.docs_root.iter_commits(
            self.default_branch, paths=path, grep=TRANSLATE_REGEX
        )

        for commit in commits:
            for file in commit.stats.files:
                if not str(file).endswith(ASCIIDOC_EXTENSION):
                    continue

                docs_type, language, filename = self._split_path_to_variables(file)
                logging.debug(f"Checking {docs_type} / {language} / {filename}")
                article_name = filename.replace(ASCIIDOC_EXTENSION, "")
                commit_date = commit.committed_date
                logging.debug(f"Last full translation: {commit_date}")

                if docs_type and docs_type in article_list.keys():
                    if article_properties := article_list[docs_type].get(article_name):
                        logging.debug(
                            f"article properties before change: {article_properties.model_dump()}"
                        )
                        article_translation = article_properties.last_full_translation
                    else:
                        continue  # Skipping not moved or excluded articles for now
                else:
                    continue  # Skipping legacy paths for now

                article_properties.last_full_translation = max(
                    article_translation, commit_date
                )
                logging.debug(
                    f"article properties after change: {article_properties.model_dump()}"
                )

    def _get_commits_of_file(self, article: Article, path, language):
        raw = DOCSSRCPATHS.docs_repo.log(
            f"--since={article.last_full_translation}", self.pretty_git_log, "--", path
        )
        raw_list = raw.replace(NEWLINE, "").split(self.pretty_split_four)
        for entry in raw_list:
            if not entry:
                continue
            name, date, id, summary = entry.split(self.pretty_split_two)
            article.commits_by_language[language].append(
                ArticleCommit(
                    commit_id=id[:6],
                    properties=CommitProperties(
                        date=date, author=name, msg=str(summary).lower()
                    ),
                )
            )
            article.commit_ids[language].append(id[:6])
            article.commit_msgs[language].append(summary.lower())

    def get_article_commits(self, article_list):
        for docs_type, articles in article_list.items():
            for article_name, article_properties in articles.items():
                base_dir = f"{DOCSSRCPATHS.docs_root.working_dir}/src/{docs_type}"
                for lang in INCLUDE_LANGUAGES:
                    self._get_commits_of_file(
                        article_properties,
                        f"{base_dir}/{lang}/{article_name}{ASCIIDOC_EXTENSION}",
                        lang,
                    )


class ArticleDatabase:
    def __init__(self):
        self.src_path = DocsSrcPaths().base
        self.article_list = {}

    def _get_all_files(self, language_path, docs_type):
        for article in listdir(language_path):
            if not article.endswith(ASCIIDOC_EXTENSION):
                continue
            article_name = article.replace(ASCIIDOC_EXTENSION, "")
            self.article_list[docs_type][article_name] = Article(
                docs_type=docs_type, name=article_name
            )

    def _get_file(self, language_path, docs_type, article):
        for article_file in listdir(language_path):
            if not article_file.startswith(article):
                continue
            article_name = article_file.replace(ASCIIDOC_EXTENSION, "")
            self.article_list[docs_type][article_name] = Article(
                docs_type=docs_type, name=article_name
            )

    def _get_all_languages(self, type_path, docs_type):
        for language in listdir(type_path):
            if language not in INCLUDE_LANGUAGES:
                continue
            self._get_all_files(f"{type_path}/{language}", docs_type)

    def _get_languages(self, type_path, docs_type, article):
        for language in listdir(type_path):
            if language not in INCLUDE_LANGUAGES:
                continue
            self._get_file(f"{type_path}/{language}", docs_type, article)

    def get_all_articles(self, specific_docs_type=None):
        for docs_type in listdir(self.src_path):
            if docs_type not in INCLUDE_DOCS_TYPES:
                continue
            if specific_docs_type and docs_type != specific_docs_type:
                continue
            self.article_list.setdefault(docs_type, {})
            self._get_all_languages(f"{self.src_path}/{docs_type}", docs_type)

    def get_article(self, article, specific_docs_type=None):
        for docs_type in listdir(self.src_path):
            if docs_type not in INCLUDE_DOCS_TYPES:
                continue
            if specific_docs_type and docs_type != specific_docs_type:
                continue
            self.article_list.setdefault(docs_type, {})
            self._get_languages(f"{self.src_path}/{docs_type}", docs_type, article)

    def _get_article_diff(self, article: Article):
        article_state = "clean"
        for commit in article.commits_by_language["de"]:
            logging.debug(f"Checking: {commit}")
            if commit.properties.msg.startswith(EXCLUDE_COMMIT_PREFIX):
                commit.properties.state = "clean"
            elif commit.commit_id not in article.commit_ids["en"]:
                commit.properties.state = "dirty"
                article.dirty_commit_count += 1
                article_state = "dirty"
            elif commit.properties.msg not in article.commit_msgs["en"]:
                commit.properties.state = "dirty"
                article.dirty_commit_count += 1
                article_state = "dirty"
            else:
                commit.properties.state = "clean"

        for commit in article.commits_by_language["en"]:
            if commit.properties.msg.startswith(EXCLUDE_COMMIT_PREFIX):
                commit.properties.state = "clean"
                continue
            elif commit.commit_id not in article.commit_ids["de"]:
                commit.properties.state = "dirty"
                article.dirty_commit_count += 1
                article_state = "dirty"
            elif commit.properties.msg not in article.commit_msgs["de"]:
                commit.properties.state = "dirty"
                article.dirty_commit_count += 1
                article_state = "dirty"
            else:
                commit.properties.state = "clean"

        article.state = article_state

    def get_diff(self):
        for _docs_type, articles in self.article_list.items():
            for _name, properties in articles.items():
                self._get_article_diff(properties)
                if properties.dirty_commit_count >= 1:
                    properties.hint = BoxText().hint_dirty_commits.format(
                        **{"dirty_commit_count": properties.dirty_commit_count}
                    )
                elif properties.last_full_translation == DEFAULT_DATE:
                    properties.hint = BoxText().hint_never_marked
                else:
                    properties.hint = BoxText().hint_last_full_translation.format(
                        **{
                            "last_full_translation": datetime.fromtimestamp(
                                properties.last_full_translation
                            ).strftime("%Y-%m-%d %H:%M")
                        }
                    )


def parse_arguments(argv):
    """Usage: translate [ARTICLE [COMMIT-NR]]"""
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "article",
        type=str,
        default="all",
        help="Article name to analyze",
        nargs="?",
    )
    parser.add_argument(
        "-t",
        "--docs-type",
        default="all",
        help="The type of docs that will be build. "
        + "Valid values are: common, onprem, saas, includes, all_types",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="Activate with single and increase by specifying multiple times",
    )
    parser.add_argument(
        "-w",
        "--width",
        default=85,
        help="Adjust the width to use more of your screen. Default is set to 85 characters",
    )
    parser.add_argument(
        "-c",
        "--complete",
        action="store_true",
        default=False,
        help="Only usable when listing summaries and not specific articles",
    )

    return parser.parse_args(argv)


def _prepare_data(db: ArticleDatabase, git: GitCommits):
    git.get_translated_marker(db.article_list)
    git.get_article_commits(db.article_list)
    db.get_diff()


WRITE = ColorizedOutput()


def main():
    opts = parse_arguments(argv[1:])
    if opts.verbose:
        logging.basicConfig(level=VERBOSITY.get(opts.verbose, 2), format=LOGFORMAT)
    else:
        logging.basicConfig(level=VERBOSITY[0], format=LOGFORMAT)
    article = opts.article
    docs_type = opts.docs_type
    git = GitCommits()
    db = ArticleDatabase()

    if article == "all" and docs_type == "all":
        # get all articles from all types
        db.get_all_articles()
        _prepare_data(db, git)
        WRITE.all_summary(db.article_list, complete=opts.complete)
    elif article == "all":
        # get all articles from specific type
        db.get_all_articles(docs_type)
        _prepare_data(db, git)
        WRITE.all_summary(db.article_list, complete=opts.complete)
    elif docs_type == "all":
        # get specific article from all types
        db.get_article(article)
        _prepare_data(db, git)
        WRITE.details_for_all_docs_type(db.article_list, article)
    else:
        # get specific article from specific type
        db.get_article(article, docs_type)
        _prepare_data(db, git)
        WRITE.details_for_docs_type(db.article_list, article, docs_type)


if __name__ == "__main__":
    exit(main())

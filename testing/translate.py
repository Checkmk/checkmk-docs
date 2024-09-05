#!/usr/bin/env python3
# encoding: utf-8
"""Tool for checking missing translations"""

from datetime import datetime
import logging
from pydantic import BaseModel
from os import listdir
import shutil
from sys import argv, stdout
from subprocess import check_output
import textwrap
from typing import Any
import argparse
import git

TRANSLATE_REGEX: str = r"^translated\|^content-sync\|^content_sync"
DEFAULT_DATE: int = (
    1704063599  # set to 2023-12-31 23:59:59; need to adjust if including legacy articles
)
DATEFORMAT_HUMAN_READABLE: str = "%Y-%m-%d %H:%M"
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
ALL_ARTICLES: str = "all"
EXCLUDE_ARTICLES: tuple = (
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


class LangComparision(BaseModel):
    src: str
    rel: str


class Languages(BaseModel):
    DE: str = "de"
    EN: str = "en"
    include: tuple[str, str] = (DE, EN)
    check_de: LangComparision = LangComparision(src=DE, rel=EN)
    check_en: LangComparision = LangComparision(src=EN, rel=DE)


class States(BaseModel):
    dirty: str = "dirty"
    clean: str = "clean"
    ignored: str = "ignored"


class DocsSrcPaths(BaseModel):
    docs_root: Any = git.Repo("./", search_parent_directories=True)
    docs_repo: Any = git.Git(docs_root.working_dir)
    base: str = f"{docs_root.working_dir}/src"
    default_branch: str = (
        check_output(CURRENT_BRANCH, shell=True).decode(UTF8).strip(NEWLINE)
    )


LANGUAGES = Languages()
STATES = States()
DOCSSRCPATHS = DocsSrcPaths()


class Box(BaseModel):
    size: int = shutil.get_terminal_size().columns - 2
    size_fourty: int = max(int(size * 0.4), 49)
    top: str = "┌" + "─" * size + "┐\n"
    separator: str = "├" + "─" * size + "┤\n"
    bottom: str = "└" + "─" * size + "┘\n"
    borders: str = f"\033[500D|\033[{size}C|\n"


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
    clean: str = green
    dirty: str = red


BASIC_LINE_PARAMETERS: dict[str, Any] = {
    "colors": BoxColors(),
    "box": Box(),
}


class BoxText(BaseModel):
    de: str = (
        "| {colors.bg_red}{colors.black} ⚒ "
        + "{colors.yellow}Deutsch"
        + "{colors.black} ⚒ "
        + "{colors.normal}{box.borders}"
        + "|{box.borders}"
    )
    en: str = (
        "| {colors.bg_blue}{colors.white} ✭ "
        + "{colors.white}English"
        + "{colors.white} ✭ "
        + "{colors.normal}{box.borders}"
        + "|{box.borders}"
    )
    docs_type_header: str = (
        "| {colors.bold}-------- "
        + "{colors.cyan}{type}{colors.normal} "
        + "{colors.bold}--------"
        + "{colors.normal}{box.borders}"
    )
    summary_header: str = (
        "| {colors.bold}{article.name}{colors.normal} "
        + "(Since: {article.commits_since}) "
        + "\033[500D|\033[{box.size_fourty}C "
        + "{color}{article.state}{colors.normal}"
        + "{colors.bold}{article.hint}"
        + "{colors.normal}{box.borders}"
    )
    all_clean: str = (
        "| All articles are so fresh and so clean{box.borders}{box.separator}"
    )
    commit_clean: str = "| {colors.green}c "
    commit_dirty: str = "| {colors.red}d "
    commit_ignored: str = "| {colors.normal}- "
    commit_details: str = (
        "{colors.magenta}{commit_id} "
        + "{colors.blue}{commit_date} "
        + "{colors.yellow}{commit_author}"
        + "\033[500D|\033[49C "
        + "{colors.normal}{commit_message}"
        + "{colors.normal}{box.borders}"
    )
    hint_last_full_translation: str = (
        " - last full translation: " + "{last_full_translation}"
    )
    hint_never_marked: str = " - Never marked as translated"
    hint_dirty_commits: str = " - {dirty_commit_count} commits are untranslated"
    no_missing_markers: str = "| No articles without translation marker{box.borders}"
    missing_markers_header: str = (
        "| {colors.bold}Articles without translation marker:"
        + "{colors.normal}{box.borders}"
    )
    missing_translation_markers_articles: str = "| {articles}{box.borders}"


class CommitProperties(BaseModel):
    date: int = DEFAULT_DATE
    author: str = ""
    msg: str = ""
    state: str = "clean"


class ArticleCommit(BaseModel):
    commit_id: str = ""
    properties: CommitProperties = CommitProperties()


class Article(BaseModel):
    name: str = ""
    hint: str = ""
    state: str = "clean"
    complete: bool = False
    legacy: bool = False
    dirty_commit_count: int = 0
    commits_since: int = DEFAULT_DATE
    last_full_translation: int = DEFAULT_DATE
    commits_by_language: dict = {"de": [], "en": []}
    commit_ids: dict[str, list] = {"de": [], "en": []}
    commit_msgs: dict[str, list] = {"de": [], "en": []}


def _get_hr_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime(DATEFORMAT_HUMAN_READABLE)


class GitCommits:
    def __init__(self):
        self.pretty_git_log = "--pretty=format:%an||%ct||%H||%s||||"
        self.pretty_split_four = "||||"
        self.pretty_split_two = "||"
        self.default_since = 1409294383
        self.since = "--since={since}"
        self.default_src_dir = f"{DOCSSRCPATHS.docs_root.working_dir}/src/"

    @staticmethod
    def _split_path_to_variables(file: str) -> tuple:
        filepath = file.split("/")
        if len(filepath) == 2:  # old path structure
            return None, filepath[0], filepath[1]
        return tuple(filepath[1:])

    def get_translated_marker(
        self, article_list: dict[str, dict[str, Article]], path: str = DOCSSRCPATHS.base
    ):
        logging.info("Fetching translation marker in git history")
        commits = DOCSSRCPATHS.docs_root.iter_commits(
            DOCSSRCPATHS.default_branch, paths=path, grep=TRANSLATE_REGEX
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

    def _get_commits_of_file(
        self, article: Article, path: str, language: str, legacy_path: bool = False
    ):
        raw = DOCSSRCPATHS.docs_repo.log(
            self.since.format(since=article.commits_since),
            self.pretty_git_log,
            "--",
            path,
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
                        date=date,
                        author=name,
                        msg=str(summary).lower(),
                    ),
                )
            )
            article.commit_ids[language].append(id[:6])
            article.commit_msgs[language].append(summary.lower())

    def get_article_commits(self, article_list: dict[str, dict[str, Article]], legacy):
        logging.info("Fetching commits of articles")
        for docs_type, articles in article_list.items():
            for article_name, article_properties in articles.items():
                logging.debug(f"Fetching commits for {article_name}")
                base_dir = f"{self.default_src_dir}{docs_type}"
                article_properties.commits_since = (
                    self.default_since
                    if article_properties.complete or article_properties.legacy
                    else article_properties.last_full_translation
                )
                for lang in LANGUAGES.include:
                    file_path = f"{lang}/{article_name}{ASCIIDOC_EXTENSION}"
                    if legacy:
                        self._get_commits_of_file(
                            article_properties,
                            f"{DOCSSRCPATHS.docs_root.working_dir}/{file_path}",
                            lang,
                            legacy_path=True,
                        )
                        continue
                    self._get_commits_of_file(
                        article_properties,
                        f"{base_dir}/{file_path}",
                        lang,
                    )


class ArticleDatabase:
    def __init__(self, complete: bool, legacy: bool, evaluate: bool):
        self.src_path = DocsSrcPaths().base
        self.article_list: dict[str, dict[str, Article]] = {}
        self.articles_without_translation_marker: dict[str, list] = {}
        self.complete: bool = complete
        self.legacy: bool = legacy
        self.evaluate: bool = evaluate

    def _get_all_files(self, language_path: str, docs_type: str):
        for article in listdir(language_path):
            if not article.endswith(ASCIIDOC_EXTENSION) or article.startswith(
                EXCLUDE_ARTICLES
            ):
                continue
            article_name = article.replace(ASCIIDOC_EXTENSION, "")
            self.article_list[docs_type][article_name] = Article(name=article_name)

    def _get_file(self, language_path: str, docs_type: str, article: str):
        for article_file in listdir(language_path):
            if article_file != f"{article}{ASCIIDOC_EXTENSION}":
                continue
            article_name = article_file.replace(ASCIIDOC_EXTENSION, "")
            self.article_list[docs_type][article_name] = Article(
                name=article_name, complete=self.complete, legacy=self.legacy
            )

    def _get_all_languages(self, type_path: str, docs_type: str):
        for language in listdir(type_path):
            if language not in LANGUAGES.include:
                continue
            self._get_all_files(f"{type_path}/{language}", docs_type)

    def _get_languages(self, type_path: str, docs_type: str, article: str):
        for language in listdir(type_path):
            if language not in LANGUAGES.include:
                continue
            self._get_file(f"{type_path}/{language}", docs_type, article)

    def get_all_articles(self, specific_docs_type: str | None):
        for docs_type in listdir(self.src_path):
            if docs_type not in INCLUDE_DOCS_TYPES:
                continue
            if specific_docs_type and docs_type != specific_docs_type:
                continue
            self.article_list.setdefault(docs_type, {})
            self._get_all_languages(f"{self.src_path}/{docs_type}", docs_type)

    def get_article(self, article: str, specific_docs_type: str | None):
        for docs_type in listdir(self.src_path):
            if docs_type not in INCLUDE_DOCS_TYPES:
                continue
            if specific_docs_type and docs_type != specific_docs_type:
                continue
            self.article_list.setdefault(docs_type, {})
            self._get_languages(f"{self.src_path}/{docs_type}", docs_type, article)

    def _check_commits(self, article: Article, check: LangComparision) -> str:
        language_state = STATES.clean
        for commit in article.commits_by_language[check.src]:
            if (
                commit.properties.date < article.last_full_translation
                and not self.evaluate
            ):
                commit.properties.state = STATES.ignored
                continue

            if (
                commit.properties.msg.startswith(EXCLUDE_COMMIT_PREFIX)
                or commit.commit_id in article.commit_ids[check.rel]
                or commit.properties.msg in article.commit_msgs[check.rel]
            ):
                commit.properties.state = STATES.clean
                continue

            commit.properties.state = STATES.dirty
            article.dirty_commit_count += 1
            language_state = STATES.dirty
        return language_state

    def _get_article_diff(self, article: Article):
        state_de = self._check_commits(article=article, check=LANGUAGES.check_de)
        state_en = self._check_commits(article=article, check=LANGUAGES.check_en)

        article.state = state_de if state_en == STATES.clean else state_en

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
                            "last_full_translation": _get_hr_timestamp(
                                properties.last_full_translation
                            )
                        }
                    )

    def get_articles_without_translation_marker(self):
        for docs_type, articles in self.article_list.items():
            self.articles_without_translation_marker.setdefault(docs_type, [])
            for name, properties in articles.items():
                if properties.last_full_translation == DEFAULT_DATE:
                    self.articles_without_translation_marker[docs_type].append(name)


class ColorizedOutput:
    def __init__(self):
        self.box: Box = BASIC_LINE_PARAMETERS["box"]
        self.colors: BoxColors = BASIC_LINE_PARAMETERS["colors"]
        self.box_text: BoxText = BoxText()

    @staticmethod
    def _line(line: str, additional_parameters: dict = {}) -> None:
        stdout.write(
            line.format(
                **additional_parameters,
                **BASIC_LINE_PARAMETERS,
            )
        )

    def _get_color_str(self, state: str):
        return self.colors.model_dump().get(state)

    def _docs_type_header(self, docs_type: str) -> None:
        self._line(self.box.top)
        self._line(
            self.box_text.docs_type_header,
            additional_parameters={"type": docs_type.upper()},
        )
        self._line(self.box.separator)

    def _docs_summary_header(self, article: Article):
        article.commits_since = _get_hr_timestamp(article.commits_since)
        self._line(
            self.box_text.summary_header,
            additional_parameters={
                "color": self._get_color_str(article.state),
                "article": article,
            },
        )
        self._line(self.box.separator)

    def _missing_translation_marker_articles(self, missing: list[str]):
        if len(missing) == 0:
            self._line(self.box_text.no_missing_markers)
            return
        missing_text = textwrap.wrap(", ".join(missing), self.box.size)
        self._line(self.box_text.missing_markers_header)
        for text in missing_text:
            self._line(
                self.box_text.missing_translation_markers_articles,
                additional_parameters={"articles": text},
            )

    def _article_summary(self, data: dict[str, Article], complete: bool = False):
        all_clean = True
        for article_name, article in sorted(data.items()):
            if article.state == "clean" and not complete:
                continue
            all_clean = False
            self._docs_summary_header(article)
        if all_clean:
            self._line(self.box_text.all_clean)

    def _article_details(self, article: Article):
        msg_length: int = self.box.size - 50
        self._line(self.box.top)
        self._docs_summary_header(article)
        for lang, commits in article.commits_by_language.items():
            self._line(str(self.box_text.model_dump().get(lang)))
            for commit in commits:
                if commit.properties.state == STATES.clean:
                    prefix = self.box_text.commit_clean
                elif commit.properties.state == STATES.ignored:
                    prefix = self.box_text.commit_ignored
                else:
                    prefix = self.box_text.commit_dirty
                self._line(
                    prefix + self.box_text.commit_details,
                    additional_parameters={
                        "commit_id": commit.commit_id,
                        "commit_date": _get_hr_timestamp(commit.properties.date),
                        "commit_author": commit.properties.author,
                        "commit_message": commit.properties.msg[:msg_length],
                    },
                )
            self._line(self.box.separator)

    def _wrapper(
        self,
        data: dict[str, dict[str, Article]],
        article_name: str | None = None,
        complete: bool = False,
        missing_translation: dict[str, list] = {},
    ):
        for docs_type in INCLUDE_DOCS_TYPES:
            if not data.get(docs_type):
                continue

            self._docs_type_header(docs_type)
            if article_name:
                properties = data[docs_type][article_name]
                self._article_details(properties)
            else:
                self._article_summary(data[docs_type], complete=complete)
                self._missing_translation_marker_articles(
                    missing_translation.get(docs_type, [])
                )
                self._line(self.box.bottom)

    def summary(self, db: ArticleDatabase):
        data = db.article_list
        self._wrapper(
            data,
            complete=db.complete,
            missing_translation=db.articles_without_translation_marker,
        )

    def details(self, data: dict[str, dict[str, Article]], article_name: str):
        self._wrapper(data, article_name=article_name)


def _parse_arguments(argv: list) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "article",
        type=str,
        default=ALL_ARTICLES,
        help="Article name to analyze",
        nargs="?",
    )
    parser.add_argument(
        "-t",
        "--docs-type",
        default=None,
        help="The type of docs that will be build. "
        + "Valid values are: common, onprem, saas, includes, all",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        help="Activate with single and increase by specifying multiple times",
    )
    parser.add_argument(
        "-c",
        "--complete",
        action="store_true",
        default=False,
        help="Lists all articles in summaries and all commits in details",
    )
    parser.add_argument(
        "-l",
        "--legacy",
        action="store_true",
        default=False,
        help="Uses legacy paths instead of new directory structure",
    )
    parser.add_argument(
        "-e",
        "--evaluate",
        action="store_true",
        default=False,
        help="Evaluate commits prio to last full translation",
    )

    return parser.parse_args(argv)


def _prepare_data(db: ArticleDatabase, git: GitCommits):
    git.get_translated_marker(db.article_list)
    git.get_article_commits(db.article_list, db.legacy)
    db.get_diff()
    db.get_articles_without_translation_marker()


def _set_logging(verbosity: int):
    if verbosity:
        logging.basicConfig(level=VERBOSITY.get(verbosity, 2), format=LOGFORMAT)
    else:
        logging.basicConfig(level=VERBOSITY[0], format=LOGFORMAT)


WRITE = ColorizedOutput()


def main():
    opts = _parse_arguments(argv[1:])
    _set_logging(opts.verbose)

    git = GitCommits()
    db = ArticleDatabase(
        complete=opts.complete, legacy=opts.legacy, evaluate=opts.evaluate
    )

    if opts.article == ALL_ARTICLES:
        db.get_all_articles(opts.docs_type)
        _prepare_data(db, git)
        WRITE.summary(db)
    else:
        db.get_article(opts.article, opts.docs_type)
        _prepare_data(db, git)
        WRITE.details(db.article_list, opts.article)


if __name__ == "__main__":
    main()

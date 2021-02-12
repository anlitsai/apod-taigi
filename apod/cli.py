import json
import os
import re
from pathlib import Path, PurePath

import click
import pendulum
from bs4 import BeautifulSoup
from markdownify import markdownify

from apod.blogger import Blogger


@click.group()
def cli():
    pass


@cli.command()
@click.option("-o", "--output_folder")
@click.option(
    "-f",
    "--output_format",
    default="YYYY/MM/YYYYMMDD",
    help="Paht format for output files",
)
@click.option("-b", "--blog_id", envvar="BLOGGER_BLOG_ID")
@click.option(
    "-i",
    "--client_id",
    envvar="GCP_CLIENT_ID",
    help="OAuth 2.0 Client ID from Credentials of GCP APIs & Services",
)
@click.option(
    "-s",
    "--client_secret",
    envvar="GCP_CLIENT_SECRET",
    help="OAuth 2.0 Client ID from Credentials of GCP APIs & Services",
)
@click.option(
    "-t",
    "--refresh_token",
    envvar="GCP_REFRESH_TOKEN",
    help="Refresh token to workaround OAuth 2.0 process",
)
@click.option(
    "-k",
    "--api_key",
    envvar="GCP_API_KEY",
    help="API Key from Credentials of GCP APIs & Services",
)
def backup(
    output_folder,
    output_format,
    blog_id,
    client_id,
    client_secret,
    refresh_token,
    api_key,
):
    """
    Save blogger posts as json files
    """
    blogger = Blogger(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        api_key=api_key,
    )

    for post in blogger.list(blog_id):
        path = PurePath(post["url"])
        try:
            publish_time = pendulum.from_format(path.name.split(".")[0], "YYYYMMDD")
        except ValueError:
            continue

        output_path = Path(
            os.path.join(output_folder, f"{publish_time.format(output_format)}.json")
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as fp:
            json.dump(post, fp, indent=2, ensure_ascii=False)
            fp.write("\n")  # add newline to end of file
            click.echo(f"Saved: {output_path}")


def _convert_blogger_post_to_markdown(post):
    soup = BeautifulSoup(post["content"], "html.parser")
    soup.br.extract()

    def find_subtitle(subtitle):
        return soup.find(text=re.compile(f"\\[{subtitle}\\]"))

    def find_content(from_title, to_title):
        lines = soup.prettify().split("\n")
        start = [i for i, line in enumerate(lines) if from_title in line][0]
        end = [i for i, line in enumerate(lines) if to_title in line][0]
        target = "".join(lines[start + 1 : end - 1])
        return markdownify(target)

    # meta
    title = post["title"].split("-")[0].strip()
    date = pendulum.parse(post["published"]).in_timezone("Asia/Taipei")
    tags = post["labels"]

    try:
        image = soup.find(href=re.compile("https://1.bp.blogspot.com/")).get("href")
    except Exception:
        image = None
        video = soup.find(src=re.compile("https://youtube.com/embed")).get("src")

    source = soup.find(href=re.compile("https://apod.nasa.gov/apod/ap"))
    source_title = source.text.strip()
    source_url = source.get("href").strip()

    meta_str = find_content(source_title, "[漢羅]").strip()
    meta_str = re.sub(r"[ ]*：[ ]*", "：", meta_str)
    meta_str = re.sub(r"[ ]*\[", "[", meta_str)
    meta_str = re.sub(r"[ ]{2,}", "\t", meta_str)
    meta = meta_str.split("\t")
    meta = [m for m in meta if "###" not in m]

    # 漢羅
    hanlo_title = find_subtitle("漢羅")
    hanlo = find_content("[漢羅]", "[POJ]").strip()
    hanlo = hanlo.replace("  ", "")
    hanlo = re.sub(r"[ ]*，[ ]*", "，", hanlo)
    hanlo = re.sub(r"[ ]*。[ ]*", "。", hanlo)

    # POJ
    poj_title = find_subtitle("POJ")
    poj = find_content("[POJ]", "[KIP]").strip()

    # KIP
    kip_title = find_subtitle("KIP")
    kip = find_content("[KIP]", "[English]").strip()

    # English
    eng_title = find_subtitle("English")
    eng = find_content("[English]", "詞彙學習").strip()
    eng = " ".join(eng.split())

    words_title = "詞彙學習（台語漢字/POJ/KIP/華語漢字/English）"
    words_str = find_content("詞彙學習", "啥物是 APOD").strip()
    words_str = re.sub(r"[ ]*/[ ]*", "/", words_str)
    words_str = re.sub(r"[ ]{2,}", "  ", words_str)
    words = words_str.split("  ")

    summary = hanlo.split("。")[0] + "。"
    summary = summary.replace("[", "").replace("]", "")
    summary = re.sub(r"\(.*\)", "", summary)

    newline = "\n"
    markdown = f"""---
title: {title}
description:
date: {date.format("YYYY-MM-DD")}
tags: {tags}
image: {image or video}
summary: {summary}
---

- [{source_title}]({source_url})
{newline.join(['- ' +m for m in meta])}

## {hanlo_title}

{hanlo}

## {poj_title}

{poj}

## {kip_title}

{kip}

## {eng_title}

{eng}

## {words_title}

{newline.join(['- ' +w for w in words])}

"""
    return markdown


@cli.command()
@click.option("-i", "--input_file", type=click.Path(exists=True, dir_okay=False))
def convert_blogger_post_to_markdown(input_file):
    with open(input_file) as fp:
        post = json.load(fp)
    markdown = _convert_blogger_post_to_markdown(post)
    print(markdown)


@cli.command()
@click.option("-i", "--input_path", type=click.Path(exists=True, dir_okay=True))
@click.option("-o", "--output_path", type=click.Path(dir_okay=True))
def convert_blogger_posts_to_markdown(input_path, output_path):
    input_folder = Path(input_path)
    output_folder = Path(output_path)
    for input_file in input_folder.glob("**/*.json"):
        with open(input_file) as fp:
            post = json.load(fp)
        try:
            markdown = _convert_blogger_post_to_markdown(post)
        except Exception:
            print(input_file)
            raise

        output_file = output_folder.joinpath(input_file.relative_to(input_folder))
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file = str(output_file).replace(".json", ".md")
        with open(output_file, "w") as fp:
            fp.write(markdown)

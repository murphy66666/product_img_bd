from pathlib import Path

from app.db.mysql import mysql_utf8mb4_url

TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".sql",
    ".toml",
    ".ts",
    ".vue",
}


def test_backend_text_sources_are_utf8_decodable() -> None:
    source_roots = [Path("app"), Path("tests")]
    source_files = [
        path
        for source_root in source_roots
        for path in source_root.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
    ]

    assert source_files
    for source_file in source_files:
        source_file.read_text(encoding="utf-8")


def test_mysql_url_adds_utf8mb4_charset() -> None:
    url = mysql_utf8mb4_url("mysql+aiomysql://user:password@127.0.0.1:3306/product_ai")

    assert url.endswith("?charset=utf8mb4")


def test_mysql_url_preserves_existing_utf8mb4_charset() -> None:
    url = mysql_utf8mb4_url(
        "mysql+aiomysql://user:password@127.0.0.1:3306/product_ai?charset=utf8mb4"
    )

    assert url.count("charset=utf8mb4") == 1

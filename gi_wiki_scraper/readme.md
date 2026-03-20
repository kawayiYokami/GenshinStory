# 先抓取/更新链接
uv run python -m gi_wiki_scraper.link_parsers.generate_links

# 再执行增量抓取与解析
uv run python -m gi_wiki_scraper.run_all_parsers_incremental

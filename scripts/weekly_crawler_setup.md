# 每 7 天自动执行爬虫与内容生成（systemd）

## 已提供文件

- `scripts/run_weekly_crawlers.sh`
- `scripts/systemd/genshinstory-crawler-refresh.service`
- `scripts/systemd/genshinstory-crawler-refresh.timer`

## 目标流程

每次触发时自动按顺序执行：

1. `gi_wiki_scraper.link_parsers.generate_links`
2. `hsr_wiki_scraper.link_parsers.generate_links`
3. `gi_wiki_scraper.run_all_parsers_incremental`
4. `hsr_wiki_scraper.run_all_parsers_incremental`
5. `scripts.generate_all_content`

## 服务器启用步骤

以下示例假设仓库路径为 `/opt/GenshinStory`，部署用户是 `ubuntu`。

1. 复制并修改 service 模板：

```bash
cd /opt/GenshinStory
cp scripts/systemd/genshinstory-crawler-refresh.service /tmp/genshinstory-crawler-refresh.service
sed -i 's#<deploy-user>#ubuntu#g' /tmp/genshinstory-crawler-refresh.service
sed -i 's#<deploy-group>#ubuntu#g' /tmp/genshinstory-crawler-refresh.service
sed -i 's#<repo-absolute-path>#/opt/GenshinStory#g' /tmp/genshinstory-crawler-refresh.service
sudo mv /tmp/genshinstory-crawler-refresh.service /etc/systemd/system/genshinstory-crawler-refresh.service
```

2. 复制 timer 文件：

```bash
sudo cp scripts/systemd/genshinstory-crawler-refresh.timer /etc/systemd/system/genshinstory-crawler-refresh.timer
```

3. 给脚本执行权限并启用 timer：

```bash
sudo chmod +x scripts/run_weekly_crawlers.sh
sudo systemctl daemon-reload
sudo systemctl enable --now genshinstory-crawler-refresh.timer
```

4. 检查状态：

```bash
systemctl status genshinstory-crawler-refresh.timer
systemctl list-timers | grep genshinstory-crawler-refresh
```

## 手动触发一次（调试用）

```bash
sudo systemctl start genshinstory-crawler-refresh.service
sudo journalctl -u genshinstory-crawler-refresh.service -n 200 --no-pager
```

## 关闭自动任务

```bash
sudo systemctl disable --now genshinstory-crawler-refresh.timer
```

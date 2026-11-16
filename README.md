# 恩平冯氏族谱（网站）

《恩平冯氏族谱》在线查阅站：https://enping.fengshizupu.com

- `data/toc.json`：全书目录数据（依原书目录逐条转录：634 条；支系 247 个、村庄 163 个）。
- `scripts/generate.py`：静态站生成器，输出到 `site/`。
- `.github/workflows/build.yml`：GitHub Actions 构建——生成 HTML、按原书 SHA-256 和渲染脚本版本复用分页图，验证链接和浏览器操作后部署到 GitHub Pages。分页图不进 git 仓库。
- Logo / favicon 与 fengshizupu.com 同款（深红底奶油色「冯」字）。

## 原书页码和阅读

- `data/book-pagination.json` 是原书页码表。按扫描顺序记录卷首、两组目录、正文、附表和封底。没有印页码的原图直接显示名称或区段内第几张。
- `reader.html?p=` 始终表示扫描顺序，已发布的网址继续打开同一张图。两组目录各印 1–13。数字搜索与原书跳页优先使用后组目录，以保持以前的跳转目标。正文编号照原书显示。
- 扫描第 1299 张是目录标为 1269 的汉字繁简对照表，1300 张是续页，1301 张是封底。目录引用和原图上实际印出的页码分别记录。
- 首页、原书目录和阅读器使用统一页码表。鼠标或键盘使用跳页、翻页与模式切换时，两种阅读器共用控制逻辑。原书连看只保留当前附近页。
- 首页按需加载原书索引。各册新版的姓名和编号共用各自的 `person-index.json`。首页纯数字按原书页码处理，`p1` 和 `p000001` 查同一个人物。各册查姓名入口也支持直接输入 `1`。

## 本地验证

```sh
python3 scripts/generate.py
python3 scripts/check_site.py --without-scans
```

完整发布检查使用 `python3 scripts/check_site.py`，校验 1301 张原书分页图、站内链接、锚点、搜索索引和站点地图。桌面及手机浏览器测试维护在 `tests/browser.cjs`。

## 村庄更新资料

在 `data/village-editions.json` 登记村庄、房支、年份及档案编号。`bookVillage` 对应原书村庄索引中的名称，可省略。村庄总页和按年目录由这份清单生成。

每册资料位于 `editions/<村庄编号>/<年份>/<档案编号>/`。将档案、谱页、人物、关系和出处 JSON 放入 `data/`，原谱图、图式谱页、封面凡例、姓名索引和 PDF 放入 `media/`。新版本使用新条目，已发布的路径和编号用于旧链接。原谱图在构建中按源数据的 SHA-256 核验。

2026 年小湴村凝斋房的初始资料取自 fengshizupu-site `d6ac2f112197fc3b7dd7c9c116c62a4325ea099b`。恩平站内更新这册资料时以这里的对应目录为准。

## 两站共用样式

`assets/genealogy-theme.css` 与主站 `public/assets/genealogy-theme.css` 同步。公共字号、配色、容器、搜索、阅读和页脚从主站样式源更新，再将同一份复制到本仓库。构建会为共享样式添加内容版本号。

# 恩平冯氏族谱（网站）

《恩平冯氏族谱》在线查阅站：https://enping.fengshizupu.com

- `data/toc.json`：全书目录数据（依原书目录逐条转录：632 条；支系 247 个、村庄 163 个）。
- `scripts/generate.py`：静态站生成器，输出到 `site/`。
- `.github/workflows/build.yml`：GitHub Actions 构建——从 Release（标签 b-20261114）下载原书 PDF，200 DPI 逐页转 WebP，再生成并部署到 GitHub Pages。分页图不进 git 仓库。
- Logo / favicon 与 fengshizupu.com 同款（深红底奶油色「冯」字）。

全书页码口径：站内一律用书页码（原书印刷页码），PDF 页 = 书页 + 30。

## 村庄更新资料

在 `data/village-editions.json` 登记村庄、房支、年份及档案编号。`bookVillage` 对应原书村庄索引中的名称，可省略。村庄总页和按年目录由这份清单生成。

每册资料位于 `editions/<村庄编号>/<年份>/<档案编号>/`。将档案、谱页、人物、关系和出处 JSON 放入 `data/`，原谱图、图式谱页、封面凡例、姓名索引和 PDF 放入 `media/`。新版本使用新条目，已发布的路径和编号用于旧链接。原谱图在构建中按源数据的 SHA-256 核验。

2026 年小湴村凝斋房的初始资料取自 fengshizupu-site `d6ac2f112197fc3b7dd7c9c116c62a4325ea099b`。恩平站内更新这册资料时以这里的对应目录为准。

## 两站共用样式

`assets/genealogy-theme.css` 与主站 `public/assets/genealogy-theme.css` 同步。公共字号、配色、容器、搜索、阅读和页脚从主站样式源更新，再将同一份复制到本仓库。构建会为共享样式添加内容版本号。

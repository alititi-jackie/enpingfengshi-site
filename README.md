# 恩平冯氏族谱（网站）

《恩平冯氏族谱》在线查阅站：https://enping.fengshizupu.com

- `data/toc.json`：全书目录数据（依原书目录逐条转录：632 条；支系 247 个、村庄 163 个）。
- `scripts/generate.py`：静态站生成器，输出到 `site/`。
- `.github/workflows/build.yml`：GitHub Actions 构建——从 Release（标签 b-20261114）下载原书 PDF，200 DPI 逐页转 WebP，再生成并部署到 GitHub Pages。分页图不进 git 仓库。
- Logo / favicon 与 fengshizupu.com 同款（深红底奶油色「冯」字）。

全书页码口径：站内一律用书页码（原书印刷页码），PDF 页 = 书页 + 30。

# PDF：基础抽取（MVP）

从 PDF 中抽取纯文本，并写入结构化 JSON。

输出：

- `extracted.json`（按页组织的文本）
- `manifest.json`（provenance：输入来源、运行环境、产物 hash 等）

## 输入参数

- `--pdf`（必填）：PDF 文件路径
- `--project`（可选）：默认 `default`

## 运行命令

```bash
python3 run.py --pdf "/path/to/paper.pdf" --project demo
```

## 常见报错（1 行修复）

- `ModuleNotFoundError: fitz`
  修复：`python3 -m pip install --user pymupdf`

## 冒烟测试（< 60s）

```bash
python3 - <<'PY'
import fitz
from pathlib import Path
p=Path("/tmp/scienceclaw_pdf_extract_basic_smoke.pdf")
d=fitz.open()
pg=d.new_page()
pg.insert_text((72,72), "Hello PDF\\nThis is a smoke test.")
d.save(p)
print(p)
PY

python3 run.py --pdf /tmp/scienceclaw_pdf_extract_basic_smoke.pdf --project selfcheck --no-llm
```

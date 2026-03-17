# ScienceClaw 技能包

> 一个可安装到 OpenClaw 的“科研技能包”集合（Skills Pack），每次执行都会产出一个可审计的 `runDir` 产物包。

## 🧭 这是什么？

- **目标**：让科研型任务（PDF抽取、文献检索、VCF注释等）变成可组合、可复现、可审计的「技能（skill）」。
- **项目形式**：每个技能都独立在 `skills/<skill_name>/` 下，通常包含 `run.py`、`SKILL.md` 以及相关依赖。
- **交付产物**：技能运行后会输出一个 `runDir`（通常包含 `artifacts/`、`manifest.json`、`logs/` 等）。

## 🚀 快速开始（3 步）

### 1) 克隆仓库

```bash
git clone https://github.com/hazelian0619/Medrixclaw.git
cd Medrixclaw
```

### 2) 安装依赖（推荐）

本仓库包含一个安装/自检脚本：`skills/scienceclaw_installer/run.sh`

```bash
bash skills/scienceclaw_installer/run.sh
```

> 该脚本会：
> - 检查 Python 环境
> - 在线安装必要的 pip 依赖（如 `requests`, `pymupdf`）
> - 运行 `scienceclaw_selfcheck` 生成一个可审计的 `runDir`

### 3) 运行一个示例技能

```bash
cd skills/scienceclaw_selfcheck
python run.py
```

成功后，会生成一个 `artifacts/` 目录，并包含 `manifest.json`、`logs/` 等审计信息。

---

## 🗂 目录结构（核心部分）

- `skills/`：核心技能集合（每个技能独立目录）
- `docs/`：面向使用者的文档（规范 & 参考）
- `scripts/`：辅助脚本（部署、打包等）
- `COMPETITOR_MATRIX.md`：功能对标分析
- `THIRD_PARTY_NOTICES.md`：第三方许可证和依赖说明

---

## 🧰 如何使用技能

1. 进入你感兴趣的技能目录，例如：

   ```bash
   cd skills/literature_pubmed_search
   ```

2. 阅读 `SKILL.md`（包含输入/输出说明、参数、示例命令）
3. 运行：

   ```bash
   python run.py [--your-args]
   ```

> 大多数技能会在运行目录下生成一个 `runDir/`（或 `artifacts/`），其中包含可审计的输出。

---

## 🌟 关键能力（代表性技能）

- 文献检索 & 结构化：`literature_pubmed_search`
- PDF 抽取（文本/结构/表格）：`pdf_extract_basic`、`scienceclaw_pdf_extract_structured`、`scienceclaw_table_extract_from_pdf`
- 数据处理 & 校验：`scienceclaw_format_convert`、`scienceclaw_data_profile`、`scienceclaw_json_validate`
- 产物包复现 & 校验：`scienceclaw_repro_export`、`scienceclaw_bundle_lint`
- 工作流与简报：`scienceclaw_workflow_lit_brief`、`scienceclaw_workflow_vcf_annotate_brief`

---

## 🧩 如何贡献

1. Fork 并创建新分支
2. 运行相关技能验证效果（通常在 `skills/<name>/run.py`）
3. 提交 PR，说明修改目的与验证方法

---

> :white_check_mark: 本仓库仅保留对外使用/开发者文档，已移除过程性/运营性材料。

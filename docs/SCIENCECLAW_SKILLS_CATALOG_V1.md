# ScienceClaw Skills Catalog v1

目的：把当前仓库中的 skills 体系整理成一份可运营、可上架、可在 OpenClaw/飞书内部分发的产品目录。

本文只解决三件事：

1. 员工会看到什么
2. 平台会注册什么
3. 哪些能力只作为内部底座存在

## 1. 目标产品形态

ScienceClaw 不再按“仓库来源”组织，而按“员工使用视角”组织：

- 入口层：员工默认入口
- 工作流层：面向结果的正式服务
- 通用工具层：对高级用户开放的科研工具
- 专业工具层：对专业团队开放的领域能力
- 治理层：隐藏式后台能力
- Vendor 层：第三方能力源，不直接上架

一句话定义：

**ScienceClaw = 1 个总入口 + 1 个分层技能库 + 1 套自动治理底座**

## 2. 分层目录

### 2.1 Entry Layer

员工不知道怎么选时，从这里进入。

| 员工名称 | Skill | 是否员工可见 | 角色 |
| --- | --- | --- | --- |
| ScienceClaw 助手 | `scienceclaw_orchestrator` | 是 | 总入口；理解请求并路由到正确工作流/工具 |

设计规则：

- 这是默认入口
- 它不是唯一入口，但必须是最强入口
- 后续飞书/OpenClaw 的默认技能卡片应优先指向它

### 2.2 Workflow Layer

这层面向“拿结果”，是员工最容易理解的正式服务层。

| 员工名称 | Skill | 是否员工可见 | 开放级别 | 主要输出 |
| --- | --- | --- | --- | --- |
| 科研文献简报 | `scienceclaw_workflow_lit_brief` | 是 | 通用开放 | `brief.md + citations.bib + evidence.json` |
| PDF 证据简报 | `scienceclaw_workflow_pdf_brief` | 是 | 通用开放 | `brief.md + citations.bib + evidence.json` |
| PDF 表格提取 | `scienceclaw_workflow_table_to_csv` | 是 | 通用开放 | `tables.csv/json + evidence.json` |
| 变异注释简报 | `scienceclaw_workflow_vcf_annotate_brief` | 是 | 专业开放 | `variants.annotated.* + brief + repro bundle` |
| 组学分析启动包 | `scienceclaw_workflow_omics_kickoff` | 是 | 专业开放 / 模板型 | 模板化 run bundle |

设计规则：

- Workflow 是“服务”，不是“工具零件”
- 员工侧优先展示这层
- 专业 workflow 允许上架，但要显式标记“专业”

### 2.3 General Tool Layer

这层是“全面解锁”的核心。全部开放，但在产品上标记为“高级工具”。

| 员工名称 | Skill | 是否员工可见 | 角色 |
| --- | --- | --- | --- |
| 文件纳管 | `scienceclaw_fs_ingest` | 是 | 把本地文件纳入当前 run bundle |
| 安全下载 | `scienceclaw_http_fetch` | 是 | 可控外链下载；支持 offline plan |
| 格式转换 | `scienceclaw_format_convert` | 是 | 办公/数据常见格式转换 |
| 数据概览 | `scienceclaw_data_profile` | 是 | CSV/JSON 画像 |
| PubMed 检索 | `literature_pubmed_search` | 是 | 文献检索底座 |
| PMID/PMCID 解析 | `scienceclaw_lit_resolve_id` | 是 | 文献 ID 解析与规范化 |
| PMC PDF 获取 | `scienceclaw_lit_pdf_fetch_pmc` | 是 | PMC PDF best-effort 获取 |
| PDF 文本抽取 | `pdf_extract_basic` | 是 | 基础文本抽取 |
| PDF 结构化抽取 | `scienceclaw_pdf_extract_structured` | 是 | 结构化 PDF 解析 |
| PDF 表格抽取 | `scienceclaw_table_extract_from_pdf` | 是 | 表格抽取底座 |
| 引用整理 | `scienceclaw_citation_normalize` | 是 | 引用/证据规范化与导出 |

设计规则：

- 这层对高级用户开放
- 不要和 workflow 混排
- 前台命名用任务名/工具名，不用工程 skill 名

### 2.4 Professional Tool Layer

面向专业团队的领域能力。允许开放，但必须单独成区。

| 员工名称 | Skill | 是否员工可见 | 角色 |
| --- | --- | --- | --- |
| VCF 质量检查 | `scienceclaw_bio_vcf_validate` | 是 | VCF 前置质检 |
| VCF 注释 | `scienceclaw_bio_vcf_annotate` | 是 | 结构化变异注释 |

设计规则：

- 与通用工具层分区展示
- 建议在员工目录上加“专业”标签

### 2.5 Governance Layer

平台必须具备，但不应出现在员工目录中。

| Skill | 是否员工可见 | 角色 |
| --- | --- | --- |
| `scienceclaw_json_validate` | 否 | JSON 结构校验 |
| `scienceclaw_repro_export` | 否 | 导出复现包 |
| `scienceclaw_report_compose_md` | 否 | 组装交付报告 |
| `scienceclaw_pack_validate` | 否 | 校验 pack/allowlist |
| `scienceclaw_bundle_lint` | 否 | run bundle 质量门禁 |
| `scienceclaw_installer` | 否 | 安装器 |
| `scienceclaw_selfcheck` | 否 | 自检 |
| `scienceclaw_meta` | 否 | 包元信息 |

设计规则：

- 这层应自动挂在前台能力后面
- 员工不应主动调用这层

### 2.6 Vendor Source Layer

第三方能力源，不是产品入口。

| Skill | 是否员工可见 | 角色 |
| --- | --- | --- |
| `vendor_openclaw_scientific_skill` | 否 | 第三方开源 scientific skill 素材仓/参考仓 |

设计规则：

- 可以复用、封装、吸收
- 不直接上架给员工

## 3. 推荐注册策略

### 3.1 员工目录应注册

- `scienceclaw_orchestrator`
- `scienceclaw_workflow_lit_brief`
- `scienceclaw_workflow_pdf_brief`
- `scienceclaw_workflow_table_to_csv`
- `scienceclaw_workflow_vcf_annotate_brief`
- `scienceclaw_workflow_omics_kickoff`
- `scienceclaw_fs_ingest`
- `scienceclaw_http_fetch`
- `scienceclaw_format_convert`
- `scienceclaw_data_profile`
- `literature_pubmed_search`
- `scienceclaw_lit_resolve_id`
- `scienceclaw_lit_pdf_fetch_pmc`
- `pdf_extract_basic`
- `scienceclaw_pdf_extract_structured`
- `scienceclaw_table_extract_from_pdf`
- `scienceclaw_citation_normalize`
- `scienceclaw_bio_vcf_validate`
- `scienceclaw_bio_vcf_annotate`

### 3.2 只在后台保留，不进入员工目录

- `scienceclaw_json_validate`
- `scienceclaw_repro_export`
- `scienceclaw_report_compose_md`
- `scienceclaw_pack_validate`
- `scienceclaw_bundle_lint`
- `scienceclaw_installer`
- `scienceclaw_selfcheck`
- `scienceclaw_meta`
- `vendor_openclaw_scientific_skill`

## 4. 自动治理底座（必须默认挂载）

对所有 Workflow Layer 和员工直达的高级工具，系统默认追加以下后台链路：

1. `scienceclaw_citation_normalize`
2. `scienceclaw_report_compose_md`
3. `scienceclaw_repro_export`
4. `scienceclaw_bundle_lint`

要求：

- 员工看到的是最终结果，不是治理过程
- 治理失败时，应在前台返回可读错误，而不是暴露底层命令

## 5. 为什么这个结构参考 ClawBio

我们参考的不是它的具体技能名，而是它的产品结构：

- **统一总入口**：`bio-orchestrator`
- **大量专科技能可单独运行**
- **最终仍然收敛到 reproducibility bundle**

公开仓库：

- ClawBio: `https://github.com/ClawBio/ClawBio`
- OpenClaw: `https://github.com/openclaw/openclaw`
- ClawHub: `https://github.com/openclaw/clawhub`
- sciClaw: `https://github.com/drpedapati/sciclaw`
- LabClaw: `https://github.com/wu-yc/LabClaw`

这些项目对我们的启发分别是：

- sciClaw：少而硬的 baseline + 审计式工作区 + 办公交付链
- ClawBio：orchestrator + specialist skills + repro contract
- LabClaw：大规模技能目录的信息架构与分组方式
- OpenClaw/ClawHub：skills registry / 版本 / 发现机制

## 6. 当前仓库的产品判断

按“企业科研技能库产品”看，ScienceClaw 当前状态可概括为：

- 已有较强的治理底座：`manifest/artifacts/logs + citations/evidence + report/repro/lint`
- 已有可用的 workflow 层：文献/PDF/表格/VCF
- 已有一批可独立使用的通用工具
- 还缺少的不是基本能力，而是 catalog 产品化、员工命名体系、目录前台与搜索/分层体验

一句话结论：

**ScienceClaw 现在已经是“治理很硬的科研技能发行版雏形”，接下来要补的是 catalog 与分层开放，而不是再回到只做 3 个 workflow。**

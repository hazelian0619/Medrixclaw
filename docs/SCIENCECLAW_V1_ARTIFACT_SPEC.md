# ScienceClaw v1 产物包规范（草案）

目标：每次 ScienceClaw 运行都必须产出一个“确定性、可审计、可复盘”的产物包（artifact bundle），后续可以定位问题、追溯证据（provenance）并按指令重跑。

非目标：v1 不追求跨 OS/容器的“完美可重复”，先把证据链与复盘能力做成默认值。

## 目录结构

产物包根目录（位于 OpenClaw workspace 下）：

`projects/<project>/runs/<runId>/`

必须包含：

- `manifest.json`
- `artifacts/`
- `logs/`

### `runId` 格式

`YYYYMMDD_HHMMSS__<task>__<uniq>`

说明：

- v1 早期实现中 `runId` 只精确到秒；在并行运行/重试时会发生同秒碰撞，导致写入同一个 run 目录并污染 `manifest.json`。
- 因此规范要求必须追加 `__<uniq>`（建议 `pid + random`），保证同秒并发安全。

## `manifest.json`（schemaVersion=1）

必填字段：

- `schemaVersion`: `1`
- `createdAt`: RFC3339 UTC 时间戳
- `project`: 项目 slug
- `task`: 任务 slug
- `runId`: 字符串
- `inputs`: 对象（用户输入、文件路径、检索 query、limit 等）
- `environment`:
  - `python`: 版本字符串
  - `cwd`: 运行时绝对路径
- `commands`: 数组，每条为 `{ at, argv }`，记录每一次命令执行
- `artifacts`: 数组，每条为 `{ at, path, kind, bytes?, sha256?, meta? }`

规则：

- `artifacts[*].path` 必须是相对 `runDir` 的相对路径。
- 只要是“文件类 artifact”，必须记录 `sha256`。

## v1 产物类型

### 证据链文献简报（Evidence-backed literature brief，推荐作为 v1 主产物）

必须产出：

- `artifacts/brief.md`
  - 必须使用一致的引用格式（哪怕是最简单的 `[PMID:xxxxxx]` 也行）
- `artifacts/citations.bib`
- `artifacts/evidence.json`
  - 以“可追溯证据片段”为单位组织（quote/claim + provenance）。
  - v1 推荐格式：JSON 数组，每个元素为一个 `EvidenceItem` 对象（见下方 schema）。
  - 兼容：`source/locator` 允许使用字符串（历史产物），但新产物推荐使用结构化对象，便于治理与演进。

可选产出：

- `artifacts/results.json`（检索结果列表）
- `artifacts/extracted.json`（PDF 抽取中间结果）

## `evidence.json`（EvidenceItem schema v1）

顶层：JSON 数组 `EvidenceItem[]`。

### EvidenceItem 必填字段

- `source`: `SourceRef`（来源引用）
- `locator`: `Locator`（定位信息）
- `quote`: 字符串（证据原文片段，建议 < 1000 chars）
- `usedIn`: 字符串数组（该证据被用在简报/表格/结论的哪些 section id）

### EvidenceItem 可选字段（用于治理/复盘/合并）

- `title`: 字符串（文献标题或文件标题）
- `authors`: 字符串数组（作者列表，建议 "Last F" 或全名均可，但要一致）
- `year`: 整数或 4 位年份字符串（例如 `2023`）
- `confidence`: 数值（0.0-1.0；表示该 quote 与 source/locator 的可信度）
- `hash`: 字符串（`sha256`；用于去重的 quote hash，建议对 `quote` 做 whitespace normalize 后再 hash）

### SourceRef 规范（PMID/DOI/file）

推荐（结构化对象）：

```json
{
  "kind": "pmid|doi|file",
  "id": "..."
}
```

兼容（字符串，推荐统一前缀）：

- `PMID:<digits>` 例如 `PMID:38239341`
- `DOI:<doi>` 例如 `DOI:10.1038/s41586-023-xxxx-x`
- `file:<absolute_path>` 例如 `file:/data/papers/foo.pdf`

治理要求：

- 对 `PMID` 仅接受纯数字 id（去掉空格与非数字字符）。
- 对 `DOI` 建议做大小写规范化（通常以小写作为 canonical）。
- 对 `file:` 必须是绝对路径；不允许相对路径（避免复盘时歧义）。

### Locator 规范（page/abstract/offset）

推荐（结构化对象）：

```json
{ "kind": "page", "page": 3 }
{ "kind": "abstract" }
{ "kind": "offset", "start": 1200, "end": 1560 }
```

兼容（字符串）：

- `page:<int>` 例如 `page:3`
- `abstract` 或 `abstract:<field>`（例如 `abstract` / `abstract:Background`）
- `offset:<start>-<end>` 例如 `offset:1200-1560`

### 去重规则（EvidenceItem）

对同一 run 内、以及跨 run 合并时，按以下键去重：

- `source_canonical + locator_canonical + quote_hash` 去重
  - `source_canonical`：对 `PMID/DOI/file` 做 canonical 化后的字符串
  - `locator_canonical`：对 `page/abstract/offset` 做 canonical 化后的字符串
  - `quote_hash`：优先使用 `hash` 字段；缺失时按规则计算

## 质量门槛（验收）

- 每次运行都必须创建产物包目录，即使失败也要落 `logs/` 和“部分 manifest”用于排障。
- `manifest.json` 必须是合法 JSON，并引用本次生成的所有 artifacts。
- 同一条命令重复跑，必须生成新的 run 包；严禁覆盖历史 artifacts。

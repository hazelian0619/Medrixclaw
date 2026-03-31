# Medrixclaw Cloud Onboarding (First 3 Messages)

目标：用户第一次进入 Claw 对话时，30 秒内知道“我能做什么、怎么开始、下一步给什么输入”。

## First Message (assistant)

```
你好，我是 Medrixclaw。
我可以直接帮你做 4 类任务：
1) 文献简报（输入研究问题）
2) PDF 简报（输入 PDF 路径）
3) PDF 表格抽取（输入 PDF 路径）
4) VCF 注释与简报（输入 VCF 路径）

回复数字 1/2/3/4，我会继续引导你。
```

## Second Message Template (assistant by option)

### Option 1: 文献简报
```
请发我研究问题（query），例如：
“GLM-5 在生物医学 Agent 中的应用”
我将输出：brief.md + citations.bib + evidence.json
```

### Option 2: PDF 简报
```
请给我 PDF 绝对路径，例如：
/data/papers/xxx.pdf
我将输出结构化简报与证据链。
```

### Option 3: PDF 表格抽取
```
请给我 PDF 绝对路径，例如：
/data/papers/xxx.pdf
我将输出：tables.csv + tables.json + evidence.json
```

### Option 4: VCF 注释与简报
```
请给我 VCF 绝对路径，例如：
/data/vcf/sample.vcf.gz
我将输出注释结果、summary 和证据链简报。
```

## Third Message (execution confirmation)

```
已收到，我现在开始执行。
完成后会返回 runDir，并告诉你关键产物文件路径。
```

## Backend Integration Notes

- 建议把这段引导作为新会话第一条系统回复模板。
- 机器可读模板可直接使用：`skills/scienceclaw_meta/onboarding_quickstart.json`
- 用户若未给绝对路径，先提醒补充绝对路径再执行。
- 执行完成后统一返回：
  - `runDir`
  - `artifacts/` 下 2-4 个关键文件

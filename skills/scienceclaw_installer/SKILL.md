---
name: scienceclaw_installer
description: Install the ScienceClaw runtime dependencies and run the minimum selfcheck. Use when provisioning a new machine, repairing a broken ScienceClaw environment, or preparing a VM for first use.
---

# ScienceClaw：安装与自检（Installer）

目的：把 ScienceClaw v1 所需依赖一次性安装好，并做最小自检（selfcheck），确保用户首次成功时间（TTFR）可控。

## 适用场景

- 新机器第一次安装 ScienceClaw skills 包
- 升级 skills 包后跑一次自检
- 遇到运行报错但不确定缺什么依赖

## 做什么

- 安装 Python 依赖（requests、pymupdf 等）
- 打印一份可复制的环境信息（python 版本、pip 位置）
- 运行最小 smoke test（只验证脚本能跑、能落产物包，不追求内容质量）
- 输出 `packVersion` 与 selfcheck 的 `runDir`（用于部署验收与自动化）

## 运行命令（服务器上）

```bash
bash run.sh
```

## 说明（pip root warning 处理）

ScienceClaw 默认部署场景是云端 OpenClaw VM（通常以 `root` 用户运行）。本 installer 选择：

- 使用 `pip install --user` 把依赖安装到 `$HOME/.local`（避免污染系统 Python）。
- 追加 `--root-user-action=ignore` 抑制 pip 的 root warning，保证安装日志干净。

取舍：

- 优点：速度快、依赖位置稳定（不需要额外创建/激活 venv），更利于 TTFR 与运维脚本化。
- 缺点：不是“强隔离”的虚拟环境；如果未来技能依赖复杂化，可以升级为 venv 策略。

## 常见报错（1 行修复）

- `python3: command not found`
  修复：`sudo apt update && sudo apt install -y python3 python3-pip`

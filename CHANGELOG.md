# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

- 待补充真实 live 验证记录
- 待补充常见故障排查说明
- 待继续收敛 discovery → shareId 自动提取方案

## [0.1.0] - 2026-06-02

### Added

- 初始公开仓库结构
- `SKILL.md` 入口说明
- 官方知识库问答 wrapper
- 官方知识库页 bridge 注入脚本
- 本地 bridge server
- 候选知识库巡检脚本
- 中文优先 README
- 基础 `.gitignore`、`LICENSE`、`references/README.md`

### Changed

- Git 作者信息统一为公开匿名身份
- README 改为中文优先说明
- `ima_discover_candidates.py` 改为支持更可移植的 `ima_api.cjs` 查找策略

### Notes

- 当前版本更适合作为技术桥接基础设施
- 若要提升对外可信度，下一步优先补真实 live 验证记录

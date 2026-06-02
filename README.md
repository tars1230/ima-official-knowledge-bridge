# IMA 官方知识库 Bridge

面向腾讯 IMA 桌面端官方知识库页面的程序化桥接方案。

这个仓库的目标很明确：尽量不依赖 GUI 点按、截图坐标、剪贴板轮询，转而直接利用 `ima.copilot.app` 里**官方知识库页面本身**的会话与问答链路，完成更稳的自动化调用。

## 适合什么场景

- 对某个个人知识库直接提问
- 在同一个知识库会话里连续追问
- 已知 `shareId` 时，不加入也能先试问共享知识库
- 通过 IMA OpenAPI 辅助查看当前可达知识库候选

## 项目亮点

- 官方知识库页问答 bridge
- 支持同会话追问复用
- 支持已知 `shareId` 的共享知识库直问
- 支持候选知识库巡检
- 采用临时 patch / 自动恢复，不做永久扩展注入

## 当前状态

当前成熟度可以诚实地概括为两句话：

- **架构和实现已经就位**
- **真实闭环仍依赖有效的 IMA 本地登录态与真实知识库上下文**

已完成部分：

- 仓库结构、脚本和 skill 入口已整理
- Python / JavaScript 静态校验已通过
- 方案已明确绑定到 IMA 官方知识库扩展页内部的 presenter / session 链路
- 已补充基础防呆逻辑，避免 placeholder `shareId` 导致长时间空等

尚未完全闭环的部分：

- 发现市场里共享知识库的 `shareId` 自动提取
- 带真实 `knowledgeBaseId` / `shareId` 的公开可复现实测样例

## 这是什么

这个仓库包含：

- skill 入口：[`SKILL.md`](./SKILL.md)
- 官方知识库页 bridge 注入脚本
- 本地 bridge server
- 一键知识库问答 wrapper
- 候选知识库巡检脚本

核心文件：

- [`scripts/ima_knowledge_ask.py`](./scripts/ima_knowledge_ask.py)
- [`scripts/ima_official_knowledge_bridge.js`](./scripts/ima_official_knowledge_bridge.js)
- [`scripts/ima_knowledge_bridge_server.py`](./scripts/ima_knowledge_bridge_server.py)
- [`scripts/ima_discover_candidates.py`](./scripts/ima_discover_candidates.py)

## 这不是什么

这个项目**不是**：

- 通用 IMA 逆向工具箱
- 通用 GUI 自动化方案
- 非官方 IMA 云服务
- 绕过 IMA 权限或账号体系的工具
- 用 OpenAPI 假装等价替代官方知识库问答

## 设计目标

主要目标：

- 让 IMA 官方知识库问答能被外部自动化稳定调用
- 让同主题追问尽量复用一个知识库会话
- 降低桌面坐标流自动化的脆弱性
- 保持实现可读、可审计、可继续迭代

非目标：

- 一次性打通 IMA 所有产品面
- 把“发现”市场里所有共享知识库能力完全自动化
- 用本地 RAG 冒充 IMA 官方知识库结果

## 整体思路

当前首选链路：

1. 临时 patch IMA 官方知识库扩展
2. 导出页面 DI container
3. 在 IMA App 内打开官方知识库扩展页
4. 通过页面内部 presenter / store / session 链路发问
5. 从官方 section 更新流中回收最终答案
6. 自动恢复原始扩展文件

这条路线的价值在于：它尽量贴近真实产品行为，而不是在产品外层硬猜。

## 架构概览

- `ima_knowledge_ask.py`
  - 主入口 wrapper
  - 负责临时 patch、打开 IMA、启动本地 bridge server、等待结果、恢复文件

- `ima_knowledge_bridge_server.py`
  - 本地短生命周期控制通道
  - 下发 job、回收结果

- `ima_official_knowledge_bridge.js`
  - 运行在 IMA 官方知识库页内部
  - 负责接入官方页面上下文并触发知识库问答

- `ima_discover_candidates.py`
  - 用 IMA OpenAPI 辅助查看 owned / addable 知识库候选

## 环境要求

- macOS
- 已安装腾讯 IMA 桌面端
- IMA 桌面端处于登录状态
- 本机可访问 IMA 扩展目录：
  `~/Library/Application Support/com.tencent.imamac/Default/Extensions/`
- Python 3
- Node.js

可选但推荐：

- 有效的 IMA OpenAPI 凭证，用于候选知识库巡检

## 安装说明

当前仓库本质上是一个可独立使用的 skill 目录。

使用方式：

1. clone 或下载本仓库
2. 保持目录结构不变
3. 确保本机具备 Python 3 与 Node.js
4. 如你的自动化框架依赖固定路径，再按需调整路径配置

当前版本不需要额外安装第三方 Python 包。

## 快速开始

### 1. 对个人知识库提问

```bash
python3 scripts/ima_knowledge_ask.py \
  '请基于这个知识库给我一个简短判断' \
  --knowledge-base-id '<kb_id>' \
  --timeout 120
```

### 2. 复用同一个知识库会话继续追问

```bash
python3 scripts/ima_knowledge_ask.py \
  '继续追问三条最关键风险' \
  --knowledge-base-id '<kb_id>' \
  --session-id '<returned_session_id>' \
  --timeout 120
```

### 3. 已知 `shareId` 时直接试问共享知识库

```bash
python3 scripts/ima_knowledge_ask.py \
  '这个共享知识库最擅长回答什么问题？' \
  --share-id '<share_id>' \
  --knowledge-base-id '<kb_id_if_known>' \
  --timeout 120
```

说明：

- 共享模式下 `knowledgeBaseId` 可选
- 但如果已经知道，传上会更稳

### 4. 查看当前可达知识库候选

```bash
python3 scripts/ima_discover_candidates.py \
  --query '' \
  --limit 10
```

查看 addable 列表：

```bash
python3 scripts/ima_discover_candidates.py \
  --mode addable \
  --limit 10
```

## 安全与维护说明

- 该方案会**临时 patch 本机 IMA 扩展文件**
- wrapper 在 `finally` 中会尽量恢复原始文件
- 不建议同时并发跑多个针对同一扩展页的 bridge 调用
- 明显占位的假 `shareId` 会被直接拒绝，避免空跑等待

## 当前限制

- “发现”市场里的 `shareId` 还没有完全自动提取
- live 成功仍依赖真实 IMA 登录态与真实知识库上下文
- IMA 扩展版本变化后，可能需要跟进维护
- 当前实现是基于一个已核实版本，而不是对未来所有版本自动兼容

## 仓库结构

```text
.
├── README.md
├── SKILL.md
├── LICENSE
├── .gitignore
├── references/
└── scripts/
    ├── ima_discover_candidates.py
    ├── ima_knowledge_ask.py
    ├── ima_knowledge_bridge_server.py
    └── ima_official_knowledge_bridge.js
```

## Roadmap

近期值得补强的方向：

- 增加一条真实 live 成功样例
- 补一节常见故障排查说明
- 缩小 discovery → `shareId` 自动提取的缺口
- 增加不同 IMA 扩展版本的兼容记录

## 发布后优先验证项

当前最值得优先补齐的公开验证材料，是一条真实 IMA 环境下的 live 成功样例。

建议内容包括：

- 用真实 `knowledgeBaseId` 或真实 `shareId` 跑一次 fresh live 验证
- 保存一条可复现的成功样例
- 在 `references/` 下补一个简短验证记录

这样做的价值在于：

- 该仓库的主要价值不在“概念成立”，而在“官方页面桥接在真实 IMA 环境里稳定成立”
- 一条真实验证记录，能显著提升可信度、可维护性和后续协作效率
- 对外部读者而言，这比继续扩展说明文字更有说服力

建议后续将验证记录沉淀到：

- [`references/verification.md`](./references/verification.md)
- [`CHANGELOG.md`](./CHANGELOG.md)

如需对外发布或小范围分发，可参考：

- [`references/release-plan.md`](./references/release-plan.md)

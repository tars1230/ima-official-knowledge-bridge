# 验证记录

这个文件用于记录真实 IMA 环境中的有效验证结果。

建议每次新增记录都包含以下字段：

## 记录模板

### 日期

- YYYY-MM-DD

### IMA 环境

- App 版本：
- 知识库扩展版本：
- 是否已登录：

### 验证目标

- 个人知识库问答 / 共享知识库试问 / 同会话追问 / 候选巡检

### 输入

- question：
- knowledgeBaseId：
- shareId：
- sessionId：

### 命令

```bash
# 在这里贴实际执行命令
```

### 结果

- 是否成功：
- finalText：
- sessionId：
- sessionReused：

### 备注

- 是否存在环境依赖
- 是否需要人工前置操作
- 是否发现版本差异

## 当前状态

当前公开仓库已经补充 1 条真实 live 巡检记录，但尚未附带一条完整的“真实知识库问答成功样例”。

这意味着当前证据层已经可以证明：

- 候选知识库巡检脚本能在真实 IMA 环境下跑通
- OpenAPI 链路可达，脚本结构和账号态没有整体失效

但仍建议继续补齐：

- 个人知识库问答成功样例
- 或已知 `shareId` 的共享知识库试问成功样例

## 已记录样例

### 2026-06-02

#### IMA 环境

- App 版本：未记录
- 知识库扩展版本：4.27.12_0
- 是否已登录：是

#### 验证目标

- 候选巡检（owned / addable）

#### 输入

- query：空字符串
- limit：5

#### 命令

```bash
python3 scripts/ima_discover_candidates.py --query '' --limit 5 --json-only
python3 scripts/ima_discover_candidates.py --mode addable --limit 5 --json-only
```

#### 结果

- 是否成功：是
- owned.count：0
- addable.count：0
- cursor：均返回非空 cursor

#### 备注

- 这是一次真实 live 调用，不是 dry-run
- 当前账号上下文下，owned / addable 列表均为空，但脚本执行成功且返回结构有效
- 该记录更适合作为“链路可用性”证据，而不是“知识库问答成功”证据

## 如何补充公开可发布的问答验证记录

如需继续补一条真实知识库问答成功样例，建议：

1. 先本地执行一次真实问答并保存 `--raw` 输出
2. 使用 `scripts/format_verification_record.py` 生成脱敏记录
3. 仅公开安全可展示的问题、回答和截断后的 ID

示例：

```bash
python3 scripts/ima_knowledge_ask.py \
  '请只回答六个字：知识库桥接成功' \
  --knowledge-base-id '<真实kb_id>' \
  --raw > /tmp/ima-kb-verify.json

python3 scripts/format_verification_record.py \
  /tmp/ima-kb-verify.json \
  --date 2026-06-02 \
  --target personal_qa \
  --question '请只回答六个字：知识库桥接成功' \
  --command "python3 scripts/ima_knowledge_ask.py '请只回答六个字：知识库桥接成功' --knowledge-base-id '<已脱敏>' --raw"
```

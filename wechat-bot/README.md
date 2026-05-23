# wechat-bot — Windows 微信自动回复机器人

Mac 架构的 Windows 移植版。五节点链路：**读数据库 → 解压消息 → 增量追踪 → LLM推理 → GUI发送**。

## 架构

```
 微信客户端 (Weixin.exe)
     │
     │ SQLCipher 加密写入
     ▼
 MSG0.db ~ MSG12.db  ──(每2秒轮询)──▶  bridge.py
                                          │
                                          ├─ 1. SQLCipher 解密
                                          ├─ 2. zlib 解压消息体
                                          ├─ 3. local_id 增量判断
                                          ├─ 4. IsSender 过滤（防自回复第1层）
                                          ├─ 5. 静默期检查   （防自回复第2层）
                                          ├─ 6. 连续回复限制 （防自回复第3层）
                                          │
                                          ▼
                                      mock_llm.py / API
                                          │
                                          ▼
                          send_layer.py (pywinauto GUI自动化)
                                          │
                                          ▼
                                    微信发送回复
```

## 目录结构

```
wechat-bot/
├── bridge.py              ← 主守护进程
├── config.py              ← 配置中心
├── extract_key.py         ← SQLCipher 密钥提取
├── db_schema.py           ← 数据库读写层
├── mock_llm.py            ← LLM 推理层（mock/API）
├── send_layer.py          ← pywinauto GUI发送层
├── simulate_message.py    ← 消息注入模拟器
├── install.bat            ← 一键安装依赖
├── run.bat                ← 一键启动
├── requirements.txt       ← Python 依赖
└── README.md
```

## 快速开始

### 1. 安装依赖

双击 `install.bat`，或手动执行：

```bash
pip install pymem pysqlcipher3 pywinauto pyperclip httpx
```

> **注意**: pysqlcipher3 需要 Visual C++ Build Tools。
> 如果安装失败，尝试 `pip install pysqlcipher3-binary`

### 2. 运行

```bash
# 演练模式（只读取消息日志，不发送回复）
python bridge.py --dry-run

# 正式模式（会真的发送微信消息！）
python bridge.py

# 模拟测试（用 mock 消息测试完整链路，不需要真实微信）
python simulate_message.py --loop    # 开启消息注入
python bridge.py --dry-run            # 另一个终端运行 bridge
```

### 3. 配置

编辑 `config.py`：

- **LLM 切换**: `LLM_MODE = "mock"` → `"api"`，填上 `LLM_API_KEY`
- **回复风格**: 修改 `SYSTEM_PROMPT` 里的 prompt
- **轮询间隔**: `POLL_INTERVAL_SEC = 2`
- **自然语言开关**: `ENABLE_KEYWORDS` / `DISABLE_KEYWORDS`

## 三层防自回复

| 层 | 机制 | 说明 |
|---|---|---|
| 1 | `IsSender` 字段 | 只处理 IsSender=0 的消息 |
| 2 | 静默期 | 发完消息后 SILENCE_AFTER_SEND_SEC 秒内不回复同一聊天 |
| 3 | 重复限制 | 同一聊天短时间内最多连续回复 MAX_AUTO_REPLIES_PER_CHAT 次 |

## 自然语言开关

在聊天中说「我去开会了」关闭自动回复，「我回来了」开启。
开关时自动跳过积压消息（从当前 local_id 继续，不处理旧消息）。

## 注意事项

1. **微信版本**: 目前适配微信 4.x 版本。大版本更新后可能需要更新 extract_key.py 中的内存偏移量
2. **管理员权限**: 密钥提取需要管理员权限（pymem 读进程内存）
3. **微信界面**: 发送消息时微信窗口必须可见（不能最小化到托盘）
4. **遵守用户协议**: 自动化操作微信可能违反微信用户协议，请合理使用

## 许可

MIT

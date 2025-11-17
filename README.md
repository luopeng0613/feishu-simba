# 🤖 飞书团队机器人 (Feishu Simba)

一个功能强大、易于扩展的飞书团队管理机器人,采用**插件化架构**设计，支持快速开发和部署新功能。

## ✨ 核心特性

- 🔌 **插件化架构** - 所有功能模块化，支持热插拔
- 💬 **双模式交互** - 支持对话命令和URL卡片交互
- 🎯 **开箱即用** - 内置值日抽签、随机抽奖、质量跟踪等常用功能
- 🚀 **快速扩展** - 简单几步即可开发新插件
- 📊 **数据持久化** - 自动保存数据，重启不丢失
- 🛡️ **稳定可靠** - 完善的错误处理和日志记录

## 📁 项目结构

```
feishu-simba/
├── app.py                      # 主入口文件
├── config.py                   # 配置管理
├── requirements.txt            # Python依赖
├── .env.example               # 环境变量模板
├── README.md                  # 项目文档
├── PLUGIN_DEVELOPMENT.md      # 插件开发指南
│
├── core/                      # 核心框架
│   ├── bot.py                # 机器人核心
│   ├── plugin_manager.py     # 插件管理器
│   ├── message_handler.py    # 消息处理器
│   └── feishu_client.py      # 飞书API客户端
│
├── plugins/                   # 插件目录
│   ├── base_plugin.py        # 插件基类
│   ├── duty_lottery/         # 值日抽签插件
│   ├── lucky_draw/           # 随机抽奖插件
│   └── quality_tracker/      # 质量跟踪插件
│
├── data/                      # 数据存储
└── logs/                      # 日志目录
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 飞书应用配置

#### 2.1 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 `App ID` 和 `App Secret`

#### 2.2 配置应用权限

在应用管理后台添加以下权限：

**消息相关权限：**
- `im:message` - 获取与发送单聊、群组消息
- `im:message:send_as_bot` - 以应用身份发消息
- `im:chat` - 获取群组信息

**通讯录权限：**
- `contact:user.base:readonly` - 获取用户基本信息

#### 2.3 配置事件订阅

1. 配置事件订阅URL：
   ```
   http://your-domain.com/webhook/event
   ```

2. 订阅事件：`im.message.receive_v1`

3. 配置卡片回调URL：
   ```
   http://your-domain.com/webhook/card
   ```

### 3. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑.env文件，填入飞书应用信息
```

### 4. 启动机器人

```bash
# 开发环境
python app.py

# 生产环境（使用gunicorn）
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 🎮 内置功能

### 1. 值日抽签 (`/duty`)

- `/duty draw` - 抽取今日值日人员
- `/duty today` - 查看今日值日人员
- `/duty list` - 查看值日历史
- `/duty stats` - 查看值日统计

### 2. 随机抽奖 (`/lottery`)

- `/lottery create <奖品> <人数>` - 创建抽奖
- `/lottery join` - 参与抽奖
- `/lottery draw` - 开奖
- `/lottery list` - 查看进行中的抽奖

### 3. 项目质量跟踪 (`/quality`)

- `/quality bug add <级别> <描述>` - 记录Bug
- `/quality bug list` - 查看Bug列表
- `/quality bug close <ID>` - 关闭Bug
- `/quality report` - 生成质量报告

## 🔧 插件开发

详细文档请参考 [PLUGIN_DEVELOPMENT.md](PLUGIN_DEVELOPMENT.md)

### 快速示例

```python
# plugins/hello_world/plugin.py
from plugins.base_plugin import BasePlugin

class HelloWorldPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "你好世界"

    @property
    def description(self) -> str:
        return "一个简单的示例插件"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def author(self) -> str:
        return "Your Name"

    def handle_command(self, command, args, event):
        if command == "hello":
            name = args[0] if args else "世界"
            return self.create_text_response(f"你好，{name}！")
        return None
```

## 📡 API接口

- `GET /health` - 健康检查
- `GET /api/plugins` - 查看插件列表
- `POST /api/plugins/{name}/reload` - 重新加载插件

## 🐛 常见问题

**Q: 机器人收不到消息？**
A: 检查事件订阅URL、权限配置、机器人是否在群里

**Q: 插件没有加载？**
A: 检查插件目录结构、类继承、查看日志

**Q: 如何调试？**
A: 设置 `DEBUG=True`，使用 `self.logger` 输出日志

## 📝 许可证

MIT License

---

**Happy Coding! 🎉**

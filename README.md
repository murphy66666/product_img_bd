# Product Image Backend

FastAPI backend scaffold for the Vue AI product image generation frontend.

## Start

```bash
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Verify

```bash
uv run python -m compileall app
uv run pytest
uv run ruff check .
```

Open `http://localhost:8000/docs` for OpenAPI docs.

**技术栈：**

- **框架**: FastAPI (Python ≥3.11)
- **数据库**: MySQL (aiomysql + SQLAlchemy)
- **缓存**: Redis
- **认证**: JWT (PyJWT) + passlib/bcrypt
- **AI 集成**: LangChain
- **监控**: Watchdog (文件目录监听)
- **包管理**: uv (pyproject.toml)

**项目结构：**

```text
app/
├── main.py               # FastAPI 应用入口
├── api/
│   ├── deps.py           # 依赖注入
│   └── v1/
│       ├── router.py     # 路由注册
│       ├── health.py     # 健康检查
│       ├── auth.py       # 认证端点
│       ├── sessions.py   # 会话管理
│       ├── gallery.py    # 图库管理
│       └── generation.py # 图片生成
├── core/
│   ├── config.py         # 配置管理 (pydantic-settings)
│   ├── logging.py        # 日志配置
│   └── security.py       # 安全工具
├── db/
│   └── mysql.py          # MySQL 数据库连接
├── cache/
│   └── redis.py          # Redis 缓存
├── models/               # 数据模型
├── schemas/              # Pydantic 模式
│   ├── auth.py, session.py, gallery.py, generation.py
├── services/             # 业务逻辑层
│   ├── auth_service.py
│   ├── session_service.py
│   ├── gallery_service.py
│   ├── generation_service.py
│   ├── langchain_service.py
│   └── providers/        # AI 提供商抽象
│       ├── base.py       # 基类
│       ├── mock.py       # Mock 实现
│       └── factory.py    # 工厂模式
└── watchers/
    └── image_directory_watcher.py  # 图片目录监听
```


"""BioAgent 智能体后端包。

目录名带连字符（与前端 frontend/biovision-agent 保持一致），无法用 `import`
语句直接导入，因此在 app.py 中通过 importlib 按名字加载：

    importlib.import_module("biovision-agent.router")

包内模块之间统一使用相对导入（from . import config），避免污染顶层模块名。
"""

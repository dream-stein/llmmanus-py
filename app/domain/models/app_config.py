#!/usr/bin/eny python
# -*- coding: utf-8 -*-
"""
@Time    :2025/11/29 21:18
#Author  :Emcikem
@File    :app_config.py
"""
from pydantic import BaseModel, ConfigDict, Field


class LLMConfig(BaseModel):
    """语言模型配置"""
    base_url: str = "https://api.deepseek.com"  # 基础URL地址
    api_key: str = ""  # APi秘钥
    model_name: str = "deepseek-reasoner"  # 推理模型让给传递了tools底层会自动切换到deepseek-chat
    temperature: float = Field(default=0.7)  # 温度
    max_tokens: int = Field(default=8192, ge=0)  # 最大输出token数


class AgentConfig(BaseModel):
    """Agent通用配置"""
    max_iterations: int = Field(default=100, gt=0, lt=100)  # 最大迭代次数
    max_retries: int = Field(default=3, gt=1, lt=10)  # LLM/工具最大重试次数
    max_search_result: int = Field(default=10, gt=1, lt=30)  # 最大搜索结果数


class AppConfig(BaseModel):
    """应用配置信息，包含Agent配置、LLM提供商、A2A网络、MCP服务配置等"""
    llm_config: LLMConfig  # 语言模型配置
    agent_config: AgentConfig  # Agent通用配置

    # Pydantic配置，允许传递额外的字段初始化
    model_config = ConfigDict(extra="allow")

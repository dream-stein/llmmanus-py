#!/usr/bin/eny python
# -*- coding: utf-8 -*-
"""
@Time    :2025/12/7 14:26
#Author  :Emcikem
@File    :event.py
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Literal, List, Any, Union

from pydantic import BaseModel, Field

from .plan import Plan
from .plan import Step


class PlanEventStatus(str, Enum):
    """规划事件状态"""
    CREATED = "created"  # 已创建
    UPDATED = "updated"  # 已更新
    COMPLETED = "completed"  # 已完成


class StepEventStatus(str, Enum):
    """步骤事件状态"""
    STATED = "stated"  # 已开始
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 已失败


class BaseEvent(BaseModel):
    """基础事件类型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # 事件id
    type: Literal[""] = ""  # 事件类型
    created_at: datetime = Field(default_factory=lambda: datetime.now)  # 事件创建时间


class PlanEvent(BaseEvent):
    """规划事件类型"""
    type: Literal["plan"] = "plan"
    plan: Plan  # 规划
    status: PlanEventStatus = PlanEventStatus.CREATED  # 规划事件状态


class TitleEvent(BaseEvent):
    """标题事件类型"""
    type: Literal["title"] = "title"
    title: str = ""  # 标题


class StepEvent(BaseEvent):
    """子任务/步骤事件"""
    type: Literal["step"] = "step"
    step: Step  # 步骤信息
    status: StepEventStatus = StepEventStatus.STATED  # 步骤状态


class MessageEvent(BaseEvent):
    """消息类型，包含人类消息和AI消息"""
    type: Literal["message"] = "message"
    role: Literal["user", "assistant"] = "assistant"  # 消息角色
    message: str = ""  # 消息本身
    # todo:附件文件结构待完善
    attachments: List[Any] = Field(default_factory=list)  # 附件列表信息


class ToolEvent(BaseEvent):
    """工具事件"""
    # todo:工具事件等待工具模块接入后完善
    type: Literal["tool"] = "tool"


class WaitEvent(BaseEvent):
    """等待事件，等待用户输入确认"""
    type: Literal["wait"] = "wait"


class ErrorEvent(BaseEvent):
    """错误事件"""
    type: Literal["error"] = "error"
    error: str = ""  # 错误信息


class DoneEvent(BaseEvent):
    """结束事件类型"""
    type: Literal["done"] = "done"


# 定义应用事件类型申明
Event = Union[
    PlanEvent,
    TitleEvent,
    StepEvent,
    MessageEvent,
    ToolEvent,
    WaitEvent,
    ErrorEvent,
    DoneEvent,
]

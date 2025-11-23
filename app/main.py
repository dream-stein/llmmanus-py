#!/usr/bin/eny python
# -*- coding: utf-8 -*-
"""
@Time    :2025/11/23 17:57
#Author  :Emcikem
@File    :main.py
"""
from fastapi import FastAPI

from core.config import get_settings

# 1.加载配置信息
settings = get_settings()

app = FastAPI()

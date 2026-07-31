"""企业官网适配器集合。

导出适配器基类与各企业具体适配器，便于在入口脚本中统一调度。
"""
from .base_adapter import BaseCompanyAdapter
from .bytedance import ByteDanceAdapter
from .alibaba import AlibabaAdapter
from .tencent import TencentAdapter
from .zhaopin import ZhaopinAdapter
from .boss import BossAdapter
from .iguopin import IguopinAdapter

#: 全部已实现的企业适配器，供 run.py 遍历调度
ALL_ADAPTERS = [
    ByteDanceAdapter,
    AlibabaAdapter,
    TencentAdapter,
    ZhaopinAdapter,
    BossAdapter,
    IguopinAdapter,
]

__all__ = [
    "BaseCompanyAdapter",
    "ByteDanceAdapter",
    "AlibabaAdapter",
    "TencentAdapter",
    "ZhaopinAdapter",
    "BossAdapter",
    "IguopinAdapter",
    "ALL_ADAPTERS",
]

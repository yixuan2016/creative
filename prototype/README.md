# ADS Work Context Reference Prototype

这是 ADS-WORK-04 的本地逻辑验证原型。它使用 Python 3.10+ 标准库，不连接真实企业系统、不访问外部网络、不执行业务写回。

## 1. 目录内容

- `ads_context_engine.py`：事件接入、幂等去重、权威状态重建、冲突保留、授权校验、上下文包生成。
- `test_ads_context_engine.py`：自动化测试。
- `../examples/project-delivery-seed-data.json`：虚构项目交付场景数据。

## 2. 运行环境

- Python 3.10 或以上版本
- 无第三方依赖

## 3. 运行演示

在仓库根目录：

~~~bash
cd prototype
python ads_context_engine.py
~~~

演示将输出：
1. 各事件的接入状态；
2. 重复事件被识别为 duplicate；
3. 项目状态的权威来源和冲突线索；
4. 授权范围内的任务级上下文包；
5. 上下文生成审计记录。

## 4. 运行测试

~~~bash
python -m unittest -v
~~~

测试覆盖：
- 事件幂等；
- 权威状态优先和非权威冲突保留；
- 受限数据过滤；
- 对象范围授权；
- 处理目的授权；
- 未知对象引用拒绝；
- 租户边界检查。

## 5. 核心规则

- 项目状态的权威来源由 seed 中的 authority_rules 显式配置。
- meeting-notes 的推断不能覆盖 project-system 的权威状态。
- classification 不在授权范围内的事件不会进入上下文包。
- 请求对象必须是授权 grant 的 scope_object_ids 子集。
- Agent 只获得 grant 中列出的 allowed_actions；高风险动作单独列入 approval_required_for。
- 原型状态只存在于当前进程内，重新运行会从 seed 重建。

## 6. 重要限制

这不是生产服务，也不是安全边界。它没有实现真实身份认证、数据库持久化、并发控制、分布式幂等、字段级授权、加密、连接器、缓存撤销、模型调用或生产级审计。上线前必须由 ADS 架构、业务数据责任人、安全和合规团队评审并补齐。

示例项目、事件、角色和数据均为虚构内容。

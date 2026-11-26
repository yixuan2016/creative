# V0.5.0 Alpha 测试报告

**Pytest：** 96 passed  
**OpenAPI：** 55 paths  
**静态检查：** Python compileall、UI JavaScript node --check 均通过  
**Fresh ZIP extraction：** 96 passed

## 覆盖范围
- V0.1–V0.4 回归：事件采集、审核、RDF 投影、PALOS 只读 Profile、Connector Worker、Source Lifecycle、Event Fusion 和 Agent Runtime。
- Memory：手动创建、证据支持、有效时间、版本修订、确认/拒绝/撤回/替代。
- Reflection：已确认事件筛选、四类事件映射、候选物化、幂等和来源引用。
- Intent：创建、激活、阻塞、暂停、恢复、完成、取消、重开、revalidate 和审计。
- State：当前重点、目标、承诺、阻塞、下一步、长期记忆和版本化快照。
- Source Purge：Evidence 失效、Memory needs_review、Intent review_required、Agent 上下文隐藏。
- 动态复核：事件 disputed 后派生对象被隐藏；事件重新确认后由用户确认/重新验证。
- Agent Context：用途、敏感度、来源有效性和 Token 撤销验证。
- API：Memory、Intent、Reflection、Personal State 和 Agent Context。

测试只验证本地原型的确定性行为与合成数据，不代表真实长期记忆准确率、生产安全认证、PALOS 兼容或多机可靠性。

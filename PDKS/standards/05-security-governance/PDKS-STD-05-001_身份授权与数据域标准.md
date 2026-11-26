# PDKS-STD-05-001：身份、授权与数据域标准

## 身份
区分 Owner、Agent、Source Account、Organization 和第三方数据主体。一个 Owner 可授权多个 Agent，但授权范围不可隐式继承。

## Consent Grant 最小字段
consent_id、owner_ref、source_kind、source_account_ref、domains、data_categories、purposes、allowed_operations、granted_at、expires_at（如适用）、revoked_at、policy_version。

## 授权粒度
安装、初始化 Vault、连接来源、历史回填、实时采集、AI 分析、跨 Agent 共享、云备份和删除分别授权。用户同意安装不代表同意采集或云同步。

## 数据域
至少区分 work、life、health、finance、identity、other。数据域分类不等于访问许可；权限必须单独判断。

## 默认拒绝
Consent 缺失、授权状态不确定、来源账号不匹配或权限不足时必须 fail closed。撤销授权后停止未来采集，并生成可审计记录。

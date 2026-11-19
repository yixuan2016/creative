from __future__ import annotations

import re

# Public personal event keys documented by DingTalk DWS. Values are display-only
# descriptions, not PDKS Event Taxonomy codes. Availability does not imply tenant enablement.
DWS_EVENT_CATALOG = {
    # IM: 16
    "user_im_message_receive_at": "im.message.received.at_me",
    "user_im_message_receive_o2o": "im.message.received.direct",
    "user_im_message_receive_group": "im.message.received.group",
    "user_im_message_receive_user": "im.message.received.from_user",
    "user_im_message_receive_o2o_all": "im.message.received.all_direct",
    "user_im_message_receive_group_all": "im.message.received.all_group",
    "user_im_message_read_o2o": "im.message.read.direct",
    "user_im_message_read_group": "im.message.read.group",
    "user_im_message_recall_o2o": "im.message.recalled.direct",
    "user_im_message_recall_group": "im.message.recalled.group",
    "user_im_message_reaction_o2o": "im.message.reaction.direct",
    "user_im_message_reaction_group": "im.message.reaction.group",
    "user_im_group_updated": "im.group.updated",
    "user_im_group_member_added": "im.group.member_added",
    "user_im_group_member_exited": "im.group.member_exited",
    "user_im_group_disbanded": "im.group.disbanded",
    # OA: 7
    "user_oa_approval_task_created": "oa.approval.task_created",
    "user_oa_approval_task_finished": "oa.approval.task_finished",
    "user_oa_approval_task_redirected": "oa.approval.task_redirected",
    "user_oa_approval_instance_started": "oa.approval.instance_started",
    "user_oa_approval_instance_cc": "oa.approval.instance_cc",
    "user_oa_approval_instance_terminated": "oa.approval.instance_terminated",
    "user_oa_approval_instance_finished": "oa.approval.instance_finished",
    # Other personal events: 10
    "user_voip_call_receive_invite": "voip.call.received_invite",
    "user_todo_task_create": "todo.task.created",
    "user_todo_task_update": "todo.task.updated",
    "user_todo_task_delete": "todo.task.deleted",
    "user_contact_friend_request_received": "contact.friend_request.received",
    "user_contact_friend_added": "contact.friend.added",
    "user_card_action_triggered": "card.action.triggered",
    "user_minutes_task_created": "minutes.task.created",
    "user_minutes_summary_generated": "minutes.summary.generated",
    "user_calendar_event_changed": "calendar.event.changed",
}

IM_EVENT_KEYS = {key for key in DWS_EVENT_CATALOG if key.startswith("user_im_")}
USER_TARGET_EVENT_KEYS = {
    "user_im_message_receive_o2o", "user_im_message_receive_user",
    "user_im_message_read_o2o", "user_im_message_recall_o2o",
    "user_im_message_reaction_o2o",
}
GROUP_TARGET_EVENT_KEYS = {
    "user_im_message_receive_group", "user_im_message_read_group",
    "user_im_message_recall_group", "user_im_message_reaction_group",
    "user_im_group_updated", "user_im_group_member_added",
    "user_im_group_member_exited", "user_im_group_disbanded",
}
TODO_EVENT_KEYS = {
    "user_todo_task_create", "user_todo_task_update", "user_todo_task_delete",
}
CALENDAR_EVENT_KEY = "user_calendar_event_changed"
MINUTES_SUMMARY_EVENT_KEY = "user_minutes_summary_generated"


def validate_consume_spec(
    event_keys: list[str],
    *,
    user: str | None = None,
    open_dingtalk_id: str | None = None,
    group: str | None = None,
    role_types: list[str] | None = None,
    calendar_ids: list[str] | None = None,
    change_types: list[str] | None = None,
) -> list[str]:
    if not event_keys:
        raise ValueError("At least one DWS event key is required")
    if len(set(event_keys)) != len(event_keys):
        raise ValueError("Duplicate event keys are not allowed")
    unknown = sorted(set(event_keys) - set(DWS_EVENT_CATALOG))
    if unknown:
        raise ValueError(f"Unsupported DWS personal event keys: {unknown}")
    if user and open_dingtalk_id:
        raise ValueError("--user and --open-dingtalk-id are mutually exclusive")
    if user and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9:_-]{0,179}", user):
        raise ValueError("--user must be a DWS userId, not a name or free-form query")
    if open_dingtalk_id and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9@._:-]{0,179}", open_dingtalk_id):
        raise ValueError("--open-dingtalk-id contains unsupported characters")
    if group and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9@._:-]{0,179}", group):
        raise ValueError("--group must be a resolved openConversationId")
    for label, values in (("calendar_ids", calendar_ids), ("change_types", change_types)):
        if values is not None and (not values or any(not isinstance(v, str) or not v for v in values)):
            raise ValueError(f"{label} must be a non-empty list when provided")
    if calendar_ids and any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9@._:-]{0,179}", v) for v in calendar_ids):
        raise ValueError("Calendar IDs contain unsupported characters")
    allowed_change_types = {"eventCreated", "eventUpdated", "eventCancelled"}
    if change_types and (len(set(change_types)) != len(change_types) or set(change_types) - allowed_change_types):
        raise ValueError("Unsupported or duplicate calendar change type")

    keys = set(event_keys)
    has_calendar = CALENDAR_EVENT_KEY in keys
    if has_calendar and len(keys) != 1:
        raise ValueError("The DWS calendar event must run in its own consumer process")
    if has_calendar and (user or open_dingtalk_id or group or role_types):
        raise ValueError("Calendar events do not accept user, group or role filters")
    if not has_calendar and (calendar_ids or change_types):
        raise ValueError("Calendar filters can only be used with the calendar event")

    user_keys = keys & USER_TARGET_EVENT_KEYS
    group_keys = keys & GROUP_TARGET_EVENT_KEYS
    if user_keys and group_keys:
        raise ValueError("User-target and group-target event keys must use separate consumer processes")
    if user_keys and not (user or open_dingtalk_id):
        raise ValueError("These event keys require --user or --open-dingtalk-id")
    if group_keys and not group:
        raise ValueError("These event keys require --group")
    if user and not user_keys:
        raise ValueError("--user is not applicable to the selected event keys")
    if open_dingtalk_id and not user_keys:
        raise ValueError("--open-dingtalk-id is not applicable to the selected event keys")
    if group and not group_keys:
        raise ValueError("--group is not applicable to the selected event keys")

    if role_types:
        if not keys.issubset(TODO_EVENT_KEYS):
            raise ValueError("--role-types is only supported for a Todo-only consumer")
        allowed_roles = {"creator", "executor", "participant"}
        if len(set(role_types)) != len(role_types):
            raise ValueError("Duplicate Todo role types are not allowed")
        invalid_roles = sorted(set(role_types) - allowed_roles)
        if invalid_roles:
            raise ValueError(f"Unsupported Todo role types: {invalid_roles}")
    if keys & TODO_EVENT_KEYS and len(keys) > len(TODO_EVENT_KEYS):
        # Keep this first adapter conservative: Todo role filtering must never be
        # silently applied to unrelated event families.
        raise ValueError("Todo events must run in a Todo-only consumer in Connector 0.1.0")

    return event_keys

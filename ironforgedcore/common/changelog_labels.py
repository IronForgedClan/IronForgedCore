from ironforgedcore.models.changelog import ChangeType

CHANGE_TYPE_LABELS: dict[ChangeType, str] = {
    ChangeType.ADD_MEMBER: "Add Member",
    ChangeType.NAME_CHANGE: "Name Change",
    ChangeType.ACTIVITY_CHANGE: "Activity Change",
    ChangeType.JOINED_DATE_CHANGE: "Joined Date Change",
    ChangeType.RESET_INGOTS: "Reset Ingots",
    ChangeType.ADD_INGOTS: "Add Ingots",
    ChangeType.REMOVE_INGOTS: "Remove Ingots",
    ChangeType.RANK_CHANGE: "Rank Change",
    ChangeType.PURCHASE_RAFFLE_TICKETS: "Purchase Raffle Tickets",
    ChangeType.ROLE_CHANGE: "Role Change",
    ChangeType.FLAG_CHANGE: "Flag Change",
    ChangeType.DISCORD_ID_CHANGE: "Discord ID Change",
}


def label_for_change_type(change_type: ChangeType | int) -> str:
    """Return human readable label for a change type"""
    return CHANGE_TYPE_LABELS.get(change_type, "Unknown")

def is_gregorian_leap(year: int) -> bool:
    return year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)

def is_julian_leap(year: int) -> bool:
    return year % 4 == 0

def _days_in_month(year: int, calendar_type: str):
    leap = is_julian_leap(year) if calendar_type == "Julian" else is_gregorian_leap(year)
    return [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def validate_calendar_date(year: int, month: int, day: int, calendar_type: str) -> bool:
    if month < 1 or month > 12 or day < 1:
        return False
    return day <= _days_in_month(year, calendar_type)[month - 1]

def validate_calendar_and_cross_fields(record: dict):
    day_key = record.get("day_key")
    t = record.get("temporal_position", {})
    year = t.get("numeric_value")
    actual = t.get("actual_calendar_date")
    slot = t.get("is_leap_slot_mapping", False)
    cal = t.get("calendar_type", "Gregorian")
    era = t.get("era", "CE")
    precision = t.get("precision", "EXACT")

    if day_key == "02-29" and year is not None and cal in ("Gregorian", "Julian") and era == "CE" and precision == "EXACT":
        leap = is_julian_leap(year) if cal == "Julian" else is_gregorian_leap(year)
        if leap:
            if slot:
                return False, "Leap year cannot use structural-slot mapping."
            if actual != f"{year:04d}-02-29":
                return False, "Leap year 02-29 requires matching actual_calendar_date."
        else:
            if not slot:
                return False, "Non-leap year 02-29 requires structural-slot mapping."
            if actual is not None:
                return False, "Non-leap structural 02-29 must not have actual_calendar_date."

    if actual and era == "CE" and precision == "EXACT" and cal in ("Gregorian", "Julian"):
        try:
            y, m, d = [int(x) for x in actual.split("-")]
        except Exception:
            return False, "actual_calendar_date must be YYYY-MM-DD."
        if f"{m:02d}-{d:02d}" != day_key:
            return False, "actual_calendar_date does not match day_key."
        if year is not None and y != year:
            return False, "actual_calendar_date year does not match numeric_value."
        if not validate_calendar_date(y, m, d, cal):
            return False, f"Invalid {cal} calendar date."

    status = record.get("event_status")
    meta = record.get("future_metadata")
    outcome_states = {"OCCURRED","CHANGED","DELAYED","CANCELLED","NOT_VERIFIED"}
    if status in outcome_states:
        if not meta or meta.get("actual_outcome_status") != status:
            return False, "Outcome status must exist and match event_status."
        if status != "NOT_VERIFIED" and not meta.get("actual_outcome_evidence"):
            return False, "Final outcome requires actual_outcome_evidence."
    if status == "RUNNING":
        if not meta or meta.get("countdown_enabled") is not True:
            return False, "RUNNING requires countdown_enabled=true."
    if status == "REACHED_TARGET":
        if not meta or not meta.get("reached_target_at"):
            return False, "REACHED_TARGET requires reached_target_at."
    if meta and meta.get("schedule_history"):
        if meta["schedule_history"][-1]["new_target"] != meta.get("current_target_datetime"):
            return False, "current_target_datetime must match last schedule_history new_target."
    return True, "OK"

"""Turn model values into small display dicts the templates can render."""
import datetime
from decimal import Decimal

from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.files import FieldFile
from django.utils import timezone
from django.utils.text import capfirst

BADGE_FIELDS = {"status", "result", "priority", "stage", "action_taken"}

_SUCCESS = {
    "APPROVED", "COMPLETED", "CLOSED", "PAID", "DELIVERED", "ACCEPTED", "PASSED", "RESOLVED",
    "VERIFIED", "RECEIVED", "RUNNING", "PRESENT", "IN_STOCK", "RELEASED",
}
_DANGER = {"REJECTED", "CANCELLED", "FAILED", "BREAKDOWN", "ABSENT", "URGENT", "HIGH", "RETIRED"}
_INFO = {
    "IN_PROGRESS", "SENT", "SUBMITTED", "IN_PRODUCTION", "UNDER_REPAIR", "UNDER_REVIEW", "PICKED",
    "PACKED", "DISPATCHED", "SCHEDULED", "PLANNED", "CONFIRMED", "MAINTENANCE", "ISSUED", "DIAGNOSED",
}
_WARNING = {"OPEN", "PENDING", "PENDING_QC", "PAUSED", "MEDIUM", "HALF_DAY", "LEAVE", "UNPAID", "PARTIAL"}


def badge_class(raw):
    raw = str(raw)
    if raw in _SUCCESS:
        return "success"
    if raw in _DANGER:
        return "danger"
    if raw in _INFO or raw.startswith("PARTIALLY"):
        return "info"
    if raw in _WARNING:
        return "warning"
    return "secondary"


def _text(value):
    return {"kind": "text", "text": value}


def _dash():
    return _text("—")


def fmt_number(value):
    if isinstance(value, (Decimal, float)):
        text = f"{value:,.3f}".rstrip("0").rstrip(".")
        return text or "0"
    return f"{value:,}"


def fmt_value(value):
    if isinstance(value, FieldFile):
        if not value:
            return _dash()
        return {"kind": "file", "text": value.name.rsplit("/", 1)[-1], "url": value.url}
    if value is None or value == "":
        return _dash()
    if isinstance(value, bool):
        return {"kind": "bool", "text": "Yes" if value else "No", "value": value}
    if isinstance(value, (Decimal, float)):
        return {"kind": "num", "text": fmt_number(value)}
    if isinstance(value, int):
        return {"kind": "num", "text": f"{value:,}"}
    if isinstance(value, datetime.datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return _text(value.strftime("%d %b %Y, %H:%M"))
    if isinstance(value, datetime.date):
        return _text(value.strftime("%d %b %Y"))
    if isinstance(value, datetime.time):
        return _text(value.strftime("%H:%M"))
    return _text(str(value))


def display(obj, name):
    """Display dict for attribute/field/property ``name`` of ``obj``."""
    if name == "__str__":
        return _text(str(obj))
    try:
        field = type(obj)._meta.get_field(name)
    except FieldDoesNotExist:
        field = None

    if field is not None and field.many_to_many:
        return _text(", ".join(str(o) for o in getattr(obj, name).all()) or "—")

    if field is not None and getattr(field, "choices", None):
        raw = getattr(obj, name)
        if raw in (None, ""):
            return _dash()
        label = str(getattr(obj, f"get_{name}_display")())
        if name in BADGE_FIELDS:
            return {"kind": "badge", "text": label, "tone": badge_class(raw)}
        return _text(label)

    value = getattr(obj, name, None)
    if callable(value):
        value = value()
    return fmt_value(value)


def label_for(model, name):
    if name == "__str__":
        return capfirst(str(model._meta.verbose_name))
    try:
        return capfirst(str(model._meta.get_field(name).verbose_name))
    except FieldDoesNotExist:
        return capfirst(name.replace("_", " "))

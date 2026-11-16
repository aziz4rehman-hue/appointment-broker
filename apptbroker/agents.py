"""Three small agents: read the request, match a slot, write the reply."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from apptbroker.calendar import Calendar, Slot, demo_calendar

_BOOK = re.compile(
    r"^book\s+(?P<client>[A-Za-z][\w-]*)\s+with\s+(?P<provider>[A-Za-z][\w-]*)\s+"
    r"(?P<day>\d{4}-\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2})"
    r"(?:\s+(?P<mins>\d+))?(?:\s+(?P<reason>.+))?$",
    re.IGNORECASE,
)
_ID_CMD = re.compile(r"^(confirm|cancel)\s+(APT-\d+)$", re.IGNORECASE)
_WHO = re.compile(r"^(openings|propose)(?:\s+([A-Za-z][\w-]*))?$", re.IGNORECASE)


@dataclass
class Intent:
    kind: str
    client: str = ""
    provider: str = ""
    day: str = ""
    time: str = ""
    minutes: int = 30
    reason: str = ""
    appointment_id: str = ""
    message: str = ""


class IntakeAgent:
    def run(self, text: str) -> Intent:
        raw = " ".join(text.strip().split())
        if not raw or raw.lower() == "help":
            return Intent(kind="help")
        id_cmd = _ID_CMD.match(raw)
        if id_cmd:
            return Intent(kind=id_cmd.group(1).lower(), appointment_id=id_cmd.group(2).upper())
        who = _WHO.match(raw)
        if who:
            return Intent(kind=who.group(1).lower(), provider=who.group(2) or "")
        book = _BOOK.match(raw)
        if book:
            day = book.group("day")
            clock = book.group("time")
            try:
                datetime.strptime(day, "%Y-%m-%d")
                datetime.strptime(clock, "%H:%M")
            except ValueError:
                return Intent(kind="error", message="error: use YYYY-MM-DD and HH:MM")
            minutes = 30
            if book.group("mins"):
                minutes = int(book.group("mins"))
                if minutes != 30:
                    return Intent(kind="error", message="error: this desk books 30 minute slots")
            return Intent(
                kind="book",
                client=book.group("client"),
                provider=book.group("provider"),
                day=day,
                time=clock,
                minutes=minutes,
                reason=(book.group("reason") or "").strip(),
            )
        return Intent(
            kind="error",
            message="error: try 'book Aziz with Sara 2026-11-20 15:00 30 checkup'",
        )


class MatcherAgent:
    def run(self, intent: Intent, calendar: Calendar) -> dict:
        if intent.kind in {"help", "error"}:
            return {"type": intent.kind, "message": intent.message}
        if intent.kind == "openings":
            return self._openings(intent, calendar)
        if intent.kind == "propose":
            return self._openings(intent, calendar, as_propose=True)
        if intent.kind == "confirm":
            return self._confirm(intent, calendar)
        if intent.kind == "cancel":
            return self._cancel(intent, calendar)
        return self._book(intent, calendar)

    def _provider(self, name: str, calendar: Calendar) -> tuple[str | None, dict | None]:
        if not name:
            return None, None
        canonical = calendar.canonical(name)
        if canonical is None:
            known = ", ".join(calendar.providers()) or "none"
            return None, {"type": "error", "message": f"error: no provider named {name}. Known: {known}"}
        return canonical, None

    def _openings(self, intent: Intent, calendar: Calendar, as_propose: bool = False) -> dict:
        provider, error = self._provider(intent.provider, calendar)
        if error:
            return error
        slots = calendar.open_slots(provider)
        return {
            "type": "propose" if as_propose else "openings",
            "provider": provider or "",
            "slots": slots,
        }

    def _confirm(self, intent: Intent, calendar: Calendar) -> dict:
        slot = calendar.by_id(intent.appointment_id)
        if slot is None:
            return {"type": "error", "message": f"error: unknown {intent.appointment_id}"}
        if slot.status == "booked":
            return {"type": "error", "message": f"error: {slot.appointment_id} is already booked"}
        if slot.status != "held":
            return {"type": "error", "message": f"error: {intent.appointment_id} is not held"}
        calendar.confirm(slot)
        return {"type": "booked", "slot": slot}

    def _cancel(self, intent: Intent, calendar: Calendar) -> dict:
        slot = calendar.by_id(intent.appointment_id)
        if slot is None or slot.status == "open":
            return {"type": "error", "message": f"error: unknown {intent.appointment_id}"}
        appointment_id = slot.appointment_id
        provider = slot.provider
        when = f"{slot.day} {slot.time}"
        calendar.release(slot)
        return {
            "type": "cancelled",
            "appointment_id": appointment_id,
            "provider": provider,
            "when": when,
        }

    def _book(self, intent: Intent, calendar: Calendar) -> dict:
        provider, error = self._provider(intent.provider, calendar)
        if error:
            return error
        assert provider is not None
        exact = calendar.find(provider, intent.day, intent.time)
        if exact is not None and exact.status == "open":
            appointment_id = calendar.hold(exact, intent.client, intent.reason)
            return {"type": "held", "slot": exact, "appointment_id": appointment_id}
        alts = calendar.open_slots(provider)
        status = exact.status if exact is not None else "missing"
        return {
            "type": "conflict",
            "status": status,
            "client": intent.client,
            "provider": provider,
            "day": intent.day,
            "time": intent.time,
            "slots": alts,
        }


class ConfirmAgent:
    def run(self, result: dict) -> str:
        kind = result["type"]
        if kind in {"help"}:
            return HELP
        if kind == "error":
            return result["message"]
        if kind == "held":
            slot: Slot = result["slot"]
            reason = f"\nReason: {slot.reason}" if slot.reason else ""
            return (
                f"Held {slot.appointment_id}\n"
                f"{slot.client} with {slot.provider}\n"
                f"{slot.day} {slot.time} for {slot.minutes} minutes"
                f"{reason}\n"
                "This is a hold, not a final booking.\n"
                f"Confirm with: confirm {slot.appointment_id}"
            )
        if kind == "booked":
            slot = result["slot"]
            return (
                f"Booked {slot.appointment_id}\n"
                f"{slot.client} is confirmed with {slot.provider} "
                f"on {slot.day} at {slot.time}."
            )
        if kind == "cancelled":
            return (
                f"Cancelled {result['appointment_id']}. "
                f"{result['provider']} {result['when']} is open again."
            )
        if kind in {"openings", "propose"}:
            return _format_slots(result.get("provider") or "all providers", result["slots"])
        if kind == "conflict":
            header = (
                f"{result['provider']} {result['day']} {result['time']} is {result['status']}."
            )
            return header + "\n" + _format_slots(result["provider"], result["slots"])
        return "error: empty result"


HELP = """commands:
  openings [PROVIDER]
  propose PROVIDER
  book CLIENT with PROVIDER YYYY-MM-DD HH:MM [30] [reason]
  confirm APT-1001
  cancel APT-1001
A hold is not booked until you confirm it."""


def _format_slots(provider: str, slots: list[Slot]) -> str:
    if not slots:
        return f"No open slots for {provider}."
    lines = [f"Open slots for {provider}:"]
    for slot in slots:
        lines.append(f"- {slot.provider} {slot.day} {slot.time}")
    return "\n".join(lines)


class AppointmentBroker:
    def __init__(self, calendar: Calendar | None = None) -> None:
        self.calendar = calendar if calendar is not None else demo_calendar()
        self.intake = IntakeAgent()
        self.matcher = MatcherAgent()
        self.confirm = ConfirmAgent()

    def handle(self, text: str) -> str:
        intent = self.intake.run(text)
        matched = self.matcher.run(intent, self.calendar)
        return self.confirm.run(matched)

    def demo(self) -> str:
        commands = [
            "openings Sara",
            "book Aziz with Sara 2026-11-20 15:00 30 checkup",
            "confirm APT-1001",
            "book Noor with Sara 2026-11-20 15:00 30 followup",
        ]
        blocks = [f"> {command}\n{self.handle(command)}" for command in commands]
        return "\n".join(blocks)

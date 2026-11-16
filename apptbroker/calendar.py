"""In-memory openings. A hold is not a booking until it is confirmed."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Slot:
    provider: str
    day: str
    time: str
    minutes: int
    status: str = "open"  # open | held | booked
    client: str = ""
    reason: str = ""
    appointment_id: str = ""


class Calendar:
    def __init__(self) -> None:
        self.slots: list[Slot] = []
        self._next = 1001

    def add_slot(self, provider: str, day: str, time: str, minutes: int = 30) -> Slot:
        provider = provider.strip()
        if self.find(provider, day, time) is not None:
            raise ValueError(f"slot already exists for {provider} {day} {time}")
        slot = Slot(provider=provider, day=day, time=time, minutes=minutes)
        self.slots.append(slot)
        return slot

    def find(self, provider: str, day: str, time: str) -> Slot | None:
        for slot in self.slots:
            if (
                slot.provider.lower() == provider.lower()
                and slot.day == day
                and slot.time == time
            ):
                return slot
        return None

    def by_id(self, appointment_id: str) -> Slot | None:
        key = appointment_id.upper()
        for slot in self.slots:
            if slot.appointment_id.upper() == key:
                return slot
        return None

    def canonical(self, provider: str) -> str | None:
        for slot in self.slots:
            if slot.provider.lower() == provider.lower():
                return slot.provider
        return None

    def providers(self) -> list[str]:
        names: list[str] = []
        for slot in self.slots:
            if slot.provider not in names:
                names.append(slot.provider)
        return names

    def open_slots(self, provider: str | None = None) -> list[Slot]:
        rows = [slot for slot in self.slots if slot.status == "open"]
        if provider is not None:
            rows = [slot for slot in rows if slot.provider.lower() == provider.lower()]
        return rows

    def new_id(self) -> str:
        appointment_id = f"APT-{self._next}"
        self._next += 1
        return appointment_id

    def hold(self, slot: Slot, client: str, reason: str) -> str:
        slot.status = "held"
        slot.client = client
        slot.reason = reason
        slot.appointment_id = self.new_id()
        return slot.appointment_id

    def confirm(self, slot: Slot) -> None:
        slot.status = "booked"

    def release(self, slot: Slot) -> None:
        slot.status = "open"
        slot.client = ""
        slot.reason = ""
        slot.appointment_id = ""


def demo_calendar() -> Calendar:
    calendar = Calendar()
    rows = (
        ("Sara", "2026-11-20", "15:00"),
        ("Sara", "2026-11-20", "16:00"),
        ("Sara", "2026-11-21", "09:00"),
        ("Khan", "2026-11-20", "15:00"),
        ("Khan", "2026-11-22", "11:30"),
    )
    for provider, day, time in rows:
        calendar.add_slot(provider, day, time, 30)
    return calendar

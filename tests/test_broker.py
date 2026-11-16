import unittest

from apptbroker.agents import AppointmentBroker
from apptbroker.calendar import demo_calendar


class BrokerTests(unittest.TestCase):
    def test_hold_confirm_and_conflict(self):
        broker = AppointmentBroker(demo_calendar())
        held = broker.handle("book Aziz with Sara 2026-11-20 15:00 30 checkup")
        self.assertIn("Held APT-1001", held)
        self.assertIn("not a final booking", held)
        booked = broker.handle("confirm APT-1001")
        self.assertIn("Booked APT-1001", booked)
        self.assertIn("confirmed", booked)
        conflict = broker.handle("book Noor with Sara 2026-11-20 15:00 30 followup")
        self.assertIn("booked", conflict.lower())
        self.assertIn("16:00", conflict)
        self.assertNotIn("Held", conflict)

    def test_cancel_reopens_slot(self):
        broker = AppointmentBroker(demo_calendar())
        broker.handle("book Aziz with Sara 2026-11-20 15:00 30 checkup")
        broker.handle("confirm APT-1001")
        cancelled = broker.handle("cancel APT-1001")
        self.assertIn("open again", cancelled)
        held = broker.handle("book Noor with Sara 2026-11-20 15:00 30 followup")
        self.assertIn("Held APT-1002", held)

    def test_unknown_provider_and_bad_length(self):
        broker = AppointmentBroker(demo_calendar())
        self.assertIn("no provider", broker.handle("book Aziz with Lina 2026-11-20 15:00 30"))
        self.assertIn("30 minute", broker.handle("book Aziz with Sara 2026-11-20 15:00 45"))
        self.assertIn("error", broker.handle("book someone sometime"))

    def test_openings_hide_held_slot(self):
        broker = AppointmentBroker(demo_calendar())
        broker.handle("book Aziz with Sara 2026-11-20 15:00 30 checkup")
        text = broker.handle("openings Sara")
        self.assertNotIn("15:00", text)
        self.assertIn("16:00", text)


if __name__ == "__main__":
    unittest.main()

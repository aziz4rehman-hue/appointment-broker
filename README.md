# appointment-broker

A small appointment broker with three steps:

1. **Intake** reads the sentence.
2. **Matcher** holds an open slot or offers another one.
3. **Confirm** turns a hold into a booking.

The calendar lives in memory for the process. No network, no database.

**[See the live demo](https://htmlpreview.github.io/?https://raw.githubusercontent.com/aziz4rehman-hue/appointment-broker/main/docs/index.html)**

```bash
git clone https://github.com/aziz4rehman-hue/appointment-broker.git
cd appointment-broker
python -m apptbroker --demo
```

```
> openings Sara
Open slots for Sara:
- Sara 2026-11-20 15:00
- Sara 2026-11-20 16:00
- Sara 2026-11-21 09:00
> book Aziz with Sara 2026-11-20 15:00 30 checkup
Held APT-1001
Aziz with Sara
2026-11-20 15:00 for 30 minutes
Reason: checkup
This is a hold, not a final booking.
Confirm with: confirm APT-1001
> confirm APT-1001
Booked APT-1001
Aziz is confirmed with Sara on 2026-11-20 at 15:00.
> book Noor with Sara 2026-11-20 15:00 30 followup
Sara 2026-11-20 15:00 is booked.
Open slots for Sara:
- Sara 2026-11-20 16:00
- Sara 2026-11-21 09:00
```

A hold blocks the slot. It is not booked until `confirm`. `cancel` puts the slot back.

## Commands

Names are a single token (`Sara`, `Aziz`). Slots are 30 minutes. The demo desk has Sara and Khan.

```bash
python -m apptbroker \
  --eval "book Aziz with Khan 2026-11-22 11:30 30 consult" \
  --eval "confirm APT-1001" \
  --eval "openings"
```

| Command | What it does |
|---|---|
| `openings [PROVIDER]` | Open slots only |
| `book CLIENT with PROVIDER YYYY-MM-DD HH:MM [30] [reason]` | Hold a slot |
| `confirm APT-1001` | Book the hold |
| `cancel APT-1001` | Release a hold or a booking |
| `propose PROVIDER` | List what is still open |

From Python:

```python
from apptbroker.agents import AppointmentBroker

broker = AppointmentBroker()
print(broker.handle("book Aziz with Sara 2026-11-20 16:00 30 checkup"))
print(broker.handle("confirm APT-1001"))
```

## Tests

```bash
python -m unittest discover -s tests -v
```

Python 3.10+. No third-party packages.

## License

MIT. Built by [Aziz Rehman](https://github.com/aziz4rehman-hue).

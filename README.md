# Pet Robot · Box-Headed Desk Cat

A small cat robot that sits on your desk and keeps you company while you work. It does not talk: it shows how it feels with its body, head and ears. When you smile at your webcam, the cat cheers up; when you yawn, it gets sleepy; when you leave, it looks sad.

**Status:** in development. A team of 7 computer engineering students and a designer at Necmettin Erbakan University started the project in October 2026. The end-to-end software pipeline works on screen; the physical robot comes next.

## How it works

The robot is a "dumb terminal": it makes no decisions and only executes motion commands smoothly and safely. Seeing, thinking and motion planning all run in Python on the computer.

```
 webcam ──► Computer Vision ──► Router ──► Brain
            (face & events)       │  ◄──── (emotion decision)
                                  ▼
                       Motion: emotion → pose / animation
                                  ▼
                       HAL (hardware abstraction layer)
                         │                        │
                  on-screen simulator     ESP32 over serial
                                           (5 servos)
```

| Module | Folder | What it does |
| --- | --- | --- |
| Computer Vision | `computer_vision/` | Detects the user arriving, leaving, smiling, yawning and looking sad, angry or surprised (OpenCV + MediaPipe Face Landmarker). Camera frames never leave this module. |
| Brain | `brain/` | Chooses the cat's emotion from recent events. Rule-based today; LLM-driven behaviour is the next phase. A broken answer falls back to `idle`, so the system never crashes. |
| Router + HAL | `router/` | The asyncio hub that moves messages between modules, handles reflexes, plays animations and talks to either the simulator or the real robot through one interface. |
| Motion | `motion/` | Turns emotions into poses and animation clips for five joints, with a Tkinter simulator and animated face. |
| Firmware | `firmware/` | ESP32 code that parses serial commands, eases five servos to their targets, enforces angle limits, and returns to a neutral pose if no message arrives for 3 seconds. Developed on the Wokwi simulator until hardware arrives. |
| Contracts | `contracts/` | Pydantic models for every message between modules. A malformed message fails immediately, so integration errors are caught while writing code. |

Design decisions worth noting:

- **Contracts first.** Every module boundary is a versioned, typed message (A1/A2 perception, B1/B2 brain, C1/C2 motion). Modules are built and tested in parallel against fake data from `tools/fake_events/`.
- **Simulator before hardware.** The router does not know whether it is driving the on-screen cat or the real ESP32; one setting (`ROBOT_PORT`) switches between them.
- **Privacy by design.** No camera footage is stored or sent anywhere; only events like `smile` leave the vision module.

## Run the demo

Requires Python 3.11 and a webcam.

```bash
git clone https://github.com/KageRon7/pet-robot.git
cd pet-robot
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # Windows: copy .env.example .env

# Live mode: webcam → router → on-screen cat
python computer_vision/faz1.py | python -m router.canli

# Without a webcam: replay generated events
python -m tools.fake_events

# Tests
python -m pytest
```

Press `q` in the camera window to stop. Smile at the camera and watch the cat react.

## Roadmap

| Dates (2026) | Phase | Gate |
| --- | --- | --- |
| Oct 12–14 | 0 · Learning | Everyone demos their first exercise |
| Oct 15–18 | 1 · Standalone modules | Each module works on fake data |
| Oct 19–21 | 2 · Walking skeleton | Smile at the webcam → the on-screen cat is happy ✅ |
| Oct 22–25 | 3 · AI and virtual ESP32 | LLM-driven brain, firmware on simulated ESP32 |
| Later | 4 · Physical build | ~15 cm box-headed cat, 5 servos: body, head pan/tilt, two ears |

## Team

| Area | People |
| --- | --- |
| Project lead, architecture and interface contracts | Ferhat Yürük |
| Computer vision | Mustafa |
| Brain | Azat |
| Router and HAL | Kaan |
| Motion and simulator | Reşat |
| Character and animation design | Tuğra |
| Firmware | Onur, Eda |

Team members: see [`docs/TEAM_GUIDE.md`](docs/TEAM_GUIDE.md) for setup, working rules and the schedule (in Turkish).

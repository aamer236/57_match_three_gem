# Gameplay recordings

Both MP4 files are exactly 10 seconds at 60 FPS, 960 x 720, H.264, without audio.
They capture the real Pygame engine's rendered frames with scripted mouse clicks.
The side panel contains explanatory captions and observed game state.

## What each clip demonstrates

| Time | Scenario | Before | After |
| --- | --- | --- | --- |
| 0.00–5.50s | No input for more than five seconds | No hint | A legal swap pair pulses |
| 5.50–6.33s | Adjacent swap that makes no match | Moves drop from 20 to 19 | Moves stay at 20 |
| 6.33–8.17s | Four-gem match, then another swap to activate the resulting special | No special gem | A striped gem forms and clears its row |
| 8.17–10.00s | A swap followed by a second match from falling gems | 60 points at a flat rate | 90 points: 30 at x1, then 60 at x2 |

The clip cuts to reproducible boards at 6.33s and 8.17s to fit all four tasks into
ten seconds. These are scripted demonstrations, not uninterrupted manual play.
The recorder advances the game clock by 1/60 second per frame; the five-second
hint delay and normal update cadence are preserved. It uses the same input,
update, and render methods as the game. The special scenario supplies a fixed
board; the other scenarios use random seed 0. Scoring, matching, and other game
rules are never replaced by the recorder.

`before.mp4` was saved before implementing the four tasks, after the one-line
startup repair. `before-source.zip` preserves that runnable version. Each clip
has a source snapshot, an evidence JSON containing source hashes and observed
state, and five PNG checkpoints for visual inspection.

## Reproduce

With Python, Pygame, and FFmpeg installed, from the project root:

```bash
python tools/record_demo.py after --output /tmp/match3-new-recording
```

Existing recordings are protected from accidental overwriting. To reproduce the
before clip, extract `before-source.zip` into a separate directory and run
`python tools/record_demo.py before` from that extracted project. Running the
current fixed game with the label `before` does not restore the original behavior.

The recorder uses SDL's headless display driver and captures only the game,
without capturing the desktop or requiring screen-sharing permission.

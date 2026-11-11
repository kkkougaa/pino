# BGM proposals

`compose.js` holds two scores written for Web Audio; `PinoBGM.compose('main'|'rage')` renders one seamless stereo loop with an `OfflineAudioContext`.

- `main` — 104 bpm swing, D minor / F major, 24 bars (55.4 s)
- `rage` — 168 bpm, D minor, 28 bars (40.0 s); its lead reuses the main motif (D–F–A–G#)

`node render.js <outDir>` writes `main.wav` and `rage.wav` (needs Playwright). Not wired into the game.

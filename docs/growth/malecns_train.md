# MaleCNS growth+train (minicns-malecns-toy)

Cells are added like the whole connectome, not dumped onto one sense.
Training writes scene-up onto lift and onto the legs, and loom onto escape. Numbers are motor rates.

## Original (242 neurons)

- **before training**: climb→lift 64.3 Hz, climb→walk 0.0 Hz, loom→escape 85.7 Hz, poke-walk 202.7 Hz  (n=242)
- **after training**: climb→lift 122.8 Hz, climb→walk 40.2 Hz, loom→escape 128.6 Hz, poke-walk 202.7 Hz  (n=242)

## +160 cells, whole CNS (402 neurons)

- **before training**: climb→lift 71.9 Hz, climb→walk 0.0 Hz, loom→escape 96.4 Hz, poke-walk 182.1 Hz  (n=402)
- **after training**: climb→lift 140.3 Hz, climb→walk 123.2 Hz, loom→escape 167.9 Hz, poke-walk 192.0 Hz  (n=402)

Scene-up used to lift and not walk. After pairing it with the leg chain, the same visual cue drives walking (0.0→40.2 Hz original, 0.0→123.2 Hz with extra cells).

Lift under the same cue: original 64.3→122.8 Hz, extra cells 71.9→140.3 Hz.
Escape under loom: original 85.7→128.6 Hz, extra cells 96.4→167.9 Hz.

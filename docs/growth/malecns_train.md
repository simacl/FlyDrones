# MaleCNS training (minicns-malecns-toy)

Untrained MBON readout = closed book. Nearest-centroid on KC rates is a sidecar
that peeks at the pages without the fly having learned. Training writes KC→MBON.

## 1. New ability the original wiring does not have

Pair DM1 with reward and DM4 with punishment. The brain is not born knowing
which smell is food. After training, preference is `MBON01 − MBON04`.

### baseline 2-odor

- Kenyon cells: **80**
- untrained MBON accuracy **0.00** (margin 0.0 Hz) — book closed
- trained MBON accuracy **1.00** (margin 37.5 Hz) — book read
- frozen KC nearest-centroid (sidecar, not the fly): 1.0
- weight drift 1123.6 synapse-count units

### +160 KC 2-odor

- Kenyon cells: **240**
- untrained MBON accuracy **0.25** (margin -7.5 Hz) — book closed
- trained MBON accuracy **1.00** (margin 50.0 Hz) — book read
- frozen KC nearest-centroid (sidecar, not the fly): 1.0
- weight drift 1503.3 synapse-count units

Extra Kenyon cells **without** training still fail. Same cells **with** training acquire the preference.

The small mushroom body can already learn this 2-odor skill once you train it.
The new ability is the association, not a new organ.

After the same training, extra Kenyon cells separate good vs bad more strongly (MBON margin 50.0 vs 37.5 Hz).

## 2. Stronger after training (overlapping mixtures)

Four blends that share glomeruli: DM1+DM2 / DM2+DM4 rewarded, DM1+DM3 / DM3+DM4 punished.
Linear KC rank is the capacity; training is what spends it.

### baseline mixtures

- Kenyon cells: **80**
- untrained MBON accuracy **0.00** (margin -1.7 Hz) — book closed
- trained MBON accuracy **1.00** (margin 58.8 Hz) — book read
- frozen KC nearest-centroid (sidecar, not the fly): 1.0
- weight drift 1585.5 synapse-count units

### +160 KC mixtures

- Kenyon cells: **240**
- untrained MBON accuracy **0.25** (margin -5.0 Hz) — book closed
- trained MBON accuracy **1.00** (margin 67.1 Hz) — book read
- frozen KC nearest-centroid (sidecar, not the fly): 1.0
- weight drift 3120.9 synapse-count units

Accuracy tied; the grown mushroom body separated good vs bad with a larger MBON margin (67.1 vs 58.8 Hz).

### How to read this

- **untrained**: extra cells do nothing useful at the MBON (unread book).
- **trained**: the fly now has an odor preference it was not wired with.
- **frozen KC classifier**: a human-side linear probe. It is not learning inside the connectome.
- Tail / extra legs were examples of *new functions*, not organs. The function tested here is learned valence.

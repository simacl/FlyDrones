# MaleCNS research: extra cells, then train them

From this point the growth work is **MaleCNS-first**. MiniFly remains the flight demo.
MiniCNS (`build_minicns`, type names aligned with MaleCNS) is the unit-test stand-in
until `data/malecns_brain.npz` exists.

Extra neurons with frozen weights are an **unread book**. This path trains
KC→MBON synapses (PPL1/PAM teaching signal), then asks the mushroom body itself
— `MBON01 − MBON04` — not a sidecar classifier on Kenyon-cell rates.

```bash
flydrones download malecns && flydrones build-brain --out data/malecns_brain.npz
flydrones expand --brain data/malecns_brain.npz --grow-kc 2000 --report docs/growth/malecns_train.md
# until the 1.2 GB download is present:
flydrones expand --brain minicns --grow-kc 160
python examples/07_malecns_expand.py
```

Measured MiniCNS run: [docs/growth/malecns_train.md](growth/malecns_train.md).

## Question 1 — can extra neurons become a skill the original did not have?

Yes, after training: **odor valence**. Pair DM1 with reward and DM4 with punishment.
The connectome is not born knowing which smell is food. That association is the new
ability. (A tail or two extra legs were examples of *functions*, not organs to sprout.)

| condition | n_KC | untrained | 1 epoch | trained | trained margin |
|---|---:|---:|---:|---:|---:|
| MiniCNS | 80 | 0.00 | **1.00** | **1.00** | 37.5 Hz |
| +160 KC | 240 | 0.25 | 0.50 | **1.00** | **50.0 Hz** |

On overlapping mixtures both brains reach accuracy 1.00 after training; extra Kenyon
cells widen the margin (67.1 vs 58.8 Hz). Extra cells without the pairing still fail.
After **1 epoch** the small mushroom body is already at 1.00; the grown one is at 0.50
on the 2-odor task — more cells are not a cheaper first lesson.

`grow_like` / `--grow-kc` only adds cells of types MaleCNS already has. It cannot
invent a new body part. The new *skill* is written at existing KC→MBON boutons.

## What a "capability" actually is

Three different knobs. Mixing them is how this project keeps answering the wrong question.

| knob | decides | does not decide |
|---|---|---|
| **circuit** (which cell types exist) | *what kind* of thing can be learned — no Kenyon cells, no odor memory | which body the animal has |
| **training** (KC→MBON pairing) | *whether* that kind of thing is written | how fast the LIF runs |
| **embodiment** (sensors + muscles + closed loop) | *what it looks like in the world* — walk away, climb, yaw a drone | whether the internal preference exists |
| **neuron count** | after training: how cleanly patterns separate (MBON margin) | which skill exists; learning speed; wall-clock efficiency |

The odor skill in this repo is still read at MBON in an open loop. Closing it onto legs (NeuroMechFly) or a drone stick would *express* the same valence as different behaviour. Same DNg02 already does that: throttle on a quad, left/right CPG on a walking fly. Growing cells does not pick the body. The body does not write the book.

Neuron count is **not** efficiency. More membranes make every LIF step slower. A 1-epoch pairing is the sample-efficiency check: extra Kenyon cells are not cheaper to train; they help once they have been read.

## Question 2 — can extra neurons make the brain more powerful after training?

Only if you train them. More Kenyon cells raise the rank of the odor map
(sparse coding). Training is what spends that rank at the MBON. Extra cells
without the pairing step do not.

On MiniCNS, the same 2-odor pairing produces a **larger MBON margin** with extra
Kenyon cells. Overlapping mixtures are a separate test: extra cells are not
automatic general intelligence, and they do not always win a harder set.

The frozen KC nearest-centroid number is a human-side probe. It is not the fly
having learned.

## Rule used

Rate-based three-factor plasticity at existing KC→MBON synapses:

- reward (PAM-like): potentiate KC→MBON01 (approach), depress KC→MBON04 (avoid)
- punish (PPL1-like): the opposite
- only boutons that already exist move; signs stay excitatory
- the LIF has no intracellular dopamine cascade — PPL1/PAM are the teaching label

Collision-triggered PPL1 on the drone is still a separate roadmap item.

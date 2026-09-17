# MaleCNS expansion experiments (MiniCNS stand-in)

Real MaleCNS: `flydrones download malecns && flydrones build-brain`, then rerun with `--brain data/malecns_brain.npz`.

Question 1: can extra neurons become a **tail** or **two extra legs**?
Question 2: can extra neurons make the brain **more powerful / more intelligent**?

## A. Unmodified MiniCNS (MaleCNS compartments, no graft)

minicns-malecns-toy: 242 neurons, 1,253 directed connections, 8,686 synapses in kept connections, 242 with column coords

- **tail**: `absent`. loom 0.0 Hz, climb 0.0 Hz. type not in connectome (grow_like cannot invent it)
- **extra_legs**: `absent`. loom 0.0 Hz, climb 0.0 Hz, walk 0.0 Hz. type not in connectome (grow_like cannot invent it)

- Kenyon cells: **80**, odor nearest-centroid accuracy **0.50**, pattern rank 3

## B. grow_like +100 existing types (no new organ)

minicns-malecns-toy+100grown: 342 neurons, 1,974 directed connections, 16,207 synapses in kept connections, 342 with column coords

- **tail**: `absent`. loom 0.0 Hz, climb 0.0 Hz. type not in connectome (grow_like cannot invent it)
- **extra_legs**: `absent`. loom 0.0 Hz, climb 0.0 Hz, walk 0.0 Hz. type not in connectome (grow_like cannot invent it)

- Kenyon cells: **106**, odor nearest-centroid accuracy **1.00**, pattern rank 19

## C. graft tail + extra leg pair

minicns-malecns-toy+8×TailMN+4×LegMN_A3L+4×LegMN_A3R: 258 neurons, 1,301 directed connections, 12,485 synapses in kept connections, 242 with column coords

- **tail**: `coupled`, copy of DNp01 (r=1.00). loom 29.8 Hz, climb 0.0 Hz. new muscle on an old command — extra effector, not a new behaviour
- **extra_legs**: `coupled`, copy of T3_MN (r=1.00). loom 0.0 Hz, climb 0.0 Hz, walk 214.5 Hz. new muscle on an old command — extra effector, not a new behaviour

- Kenyon cells: **80**, odor nearest-centroid accuracy **0.50**, pattern rank 3

## D. +160 Kenyon cells (mushroom-body capacity)

minicns-malecns-toy+160grown: 402 neurons, 2,432 directed connections, 16,975 synapses in kept connections, 402 with column coords

- **tail**: `absent`. loom 0.0 Hz, climb 0.0 Hz. type not in connectome (grow_like cannot invent it)
- **extra_legs**: `absent`. loom 0.0 Hz, climb 0.0 Hz, walk 0.0 Hz. type not in connectome (grow_like cannot invent it)

- Kenyon cells: **240**, odor nearest-centroid accuracy **1.00**, pattern rank 17

### How to read this

- `absent`: that body part does not exist. `grow_like` stays in this column for tail/legs.
- `coupled`: a new muscle fired, but it copies DNp01 or T3_MN. Extra effector, not a new behaviour.
- `distinct`: stimulus-locked and not a copy — the only status that would count as a new ability.
- Kenyon accuracy is odor-pattern capacity, not general intelligence. There is still no learning rule unless you add one.

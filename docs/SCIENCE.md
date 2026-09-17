# Science: what is biology, what is engineering

FlyDrones mixes published neuroscience with engineering shortcuts. This page separates the two so you can
judge every claim, and so nobody has to take a demo video at face value.

## Data

| dataset | what | size | licence | used as |
|---|---|---|---|---|
| **MaleCNS v1.0** | complete male *Drosophila* central nervous system (brain, optic lobes, ventral nerve cord). HHMI Janelia FlyEM, University of Cambridge, MRC LMB, Google Research. v0.9 Oct 2025, v1.0 June 2026, paper in *Cell* Sept 2026 | ~166k neurons | CC-BY 4.0 | `flydrones build-brain` |
| **MiniFly** | 850-neuron hand-wired circuit in this repo, cell-type names borrowed from the real fly | 4,928 connections | MIT | demos, tests |

Neuron and connection counts for MaleCNS depend on filtering (proofreading status, minimum synapses per
connection, glia). Community projects report e.g. 166,700 neurons / 25,582,938 directed connections
([DOOMFLY](https://github.com/nftechie/doomfly)) or 165,122 "traced" neurons with a ≥ 3 synapse filter
([flycoin](https://github.com/ad7584/flycoin)). `build-brain` prints the counts for your filters.

## Neuron model (literature)

Leaky integrate-and-fire with the parameters of Shiu et al., *Nature* 2024
([paper](https://www.nature.com/articles/s41586-024-07763-9), [code](https://github.com/philshiu/Drosophila_brain_model)):

| parameter | value |
|---|---|
| resting / reset potential | −52 mV |
| threshold | −45 mV |
| membrane time constant | 20 ms |
| synaptic time constant | 5 ms |
| refractory period | 2.2 ms |
| synaptic delay | 1.8 ms |
| weight per synapse | 0.275 mV |
| Poisson input strength | 250 × weight |

Differences in FlyDrones: integration step 0.5 ms instead of 0.1 ms (for speed), optional membrane noise
(off by default), and a tonic bias current on selected neurons (see below).

Signs: acetylcholine excitatory; GABA, glutamate and histamine inhibitory; dopamine, serotonin and
octopamine treated as excitatory (a simplification: their real effects are modulatory).

## Sensory side

| input group | cell types | literature | FlyDrones shortcut |
|---|---|---|---|
| photoreceptors | R1-R6 | outer photoreceptors, luminance | mean brightness per grid cell |
| motion | T4/T5 subtypes a, b, c, d | direction-selective for front-to-back, back-to-front, upward, downward motion (Maisak et al., *Nature* 2013) | we compute optic flow in software (Lucas-Kanade) and drive T4/T5 directly, **skipping the lamina and medulla** (L1-L3, Mi1, Tm3...) that compute motion in the real fly |
| looming | LPLC2, LC4 | LPLC2 encodes looming size, LC4 looming velocity, both synapse directly onto the giant fiber (Ache et al., *Curr Biol* 2019) | expansion of the flow field (affine fit per frame) |
| rotation | haltere afferents | halteres act as gyroscopes | drone IMU yaw rate |
| gestures | (none) | (none) | hand pose becomes an optic-flow illusion. Purely an interface trick |

**Retinotopy follows column coordinates when present.** MiniFly assigns each neuron a column on
the 6×8 eye grid (rank within type+side, the same mapping the encoder used). Grown cells inherit
a column from an existing cell of that type, so extra T4c share ommatidia rather than inventing
new viewing directions. MaleCNS flat files do not always include optic-lobe columns; then the
same rank-within-type mapping is the stand-in. True neuPrint column IDs remain a data-loader
upgrade, not a different wiring rule.

## Motor side

| output group | cell type | literature | FlyDrones read-out |
|---|---|---|---|
| lift / thrust | DNg02 (population, ≥15 pairs) | activating more DNg02 cells increases wing-stroke amplitude roughly linearly; left and right act independently during steering (Namiki et al., *Curr Biol* 2022, [paper](https://www.cell.com/current-biology/fulltext/S0960-9822(22)00019-7), [preprint](https://www.biorxiv.org/content/10.1101/2021.08.05.455281v1.full)) | throttle ∝ (L + R − rest) |
| steering | DNg02 L vs R | rightward visual motion raises right DNg02 activity and lowers left (same paper) | yaw ∝ (R − L) |
| evasive turns | DNp03 | receives looming input, activity predicts flight saccades, activation triggers turns ([*Curr Biol* 2024](https://www.sciencedirect.com/science/article/pii/S0960982224016415), [*Curr Biol* 2025](https://www.cell.com/current-biology/fulltext/S0960-9822(25)01542-8)) | yaw away from the more active side, brakes cruise |
| escape | DNp01, the giant fiber | looming-evoked escape takeoff; GF spike timing selects short vs long takeoff (Ache et al. 2019; von Reyn et al. 2014) | smoothed rate above threshold → 0.7 s climb / drop / brake |

**Engineering choices, not biology:**

- **Tonic flight drive.** DNg02 get a small constant depolarisation (`brain.bias`) so they fire at rest,
  standing in for the "I am flying" state that in real flies comes from many sources (loss of leg contact,
  neuromodulators). Without it a quiet scene gives a silent motor.
- **Linear read-out.** Firing rates are mapped to stick commands by weights, either defaults or fitted by
  `flydrones calibrate`. The fit changes the read-out only, never the connectome.
- **Sign conventions** (which side is "right") follow the papers above for MiniFly. On MaleCNS the fitted
  read-out decides.
- **Cruise.** Forward flight speed is a number you choose (`decoder.cruise`). The brain can only brake it.
- **Escape actions.** "climb", "drop" or "brake" are drone-friendly stand-ins for a jump takeoff.

## MiniFly wiring

MiniFly (`brain/synthetic.py`) is a cartoon of the real circuits above, built so the demo works in seconds:

```
T4a (own eye, front-to-back) ─► HS ─► DNg02 same side (+), LAL_inh ─► DNg02 other side (−)
T4b ─► LPi_h ─┤ HS
T4c (scene up) ─► VS ─► DNg02 both (+)
T4d (scene down) ─► LPi_v ─┤ VS, DNg02
LPLC2, LC4 ─► giant fiber DNp01, PVLP ─► DNp03 ─► LAL_inh same side (turn away)
DNp03 ─► PVLP_inh other side ─┤ DNp03 other side (pick one direction)
haltere ─► DNg02 other side (+), LAL_inh same side (yaw damping)
```

It is useful to test the software. It is not evidence about the real fly. For that, build the MaleCNS
brain, run `flydrones inspect`, and compare.

## What if you add neurons, add synapses, or rewire?

The drone reads **mean rates** of named groups (`DNg02` L/R, `DNp01`, `DNp03`). Growing or rewiring
the graph only matters if those rates change.

### How to wire a new neuron

A new cell is not a blank vertex. It copies the **motif of its cell type**:

1. **Same type, same side, same partners, same sign.** A new `T4c` L gets dendrites from whatever
   drives existing `T4c` L (in MiniFly: the camera encoder) and axons onto the same `VS` L cells,
   excitatory. It does *not* grow a random edge to `DNp01` or to the other eye.
2. **Clone, don't densify.** `clone_neurons` / `--clone T4c:96` copies one existing cell's incoming
   and outgoing synapses onto each new index. `--pop-scale 2` rebuilds *every* population with the
   same `connect()` rules, so HS, VS and DNg02 grow too and synapse count goes as \(s^2\). Use clone
   when you mean "more T4c".
3. **Then choose the gain.** Extra axons onto the same VS cells make the climb louder unless you pass
   `--normalize`, which scales that type's outgoing weights by \(n_\text{old}/(n_\text{old}+n)\) so
   mean drive is unchanged and the extra cells only average Poisson noise.
4. **Readout populations are different.** The decoder uses the **mean** of `DNg02`. Cloning DNg02
   (no MiniFly outgoing synapses) barely changes the command; it mainly reduces the variance of that
   mean. Do not clone identified cells: the giant fiber `DNp01` stays **one per side**.
5. **Grid sensory cells share ommatidia.** The encoder maps neuron \(k\) of \(n\) onto cell
   \(\lfloor k \cdot 48 / n \rfloor\). Extra T4c sit on the existing 6×8 lattice; they do not invent
   new viewing directions.
6. **Empty axons do nothing.** `--extra-neurons` adds membranes with no synapses. Flight is unchanged.
7. **MaleCNS cannot be EM-grown past completeness.** v1.0 is already the whole CNS of one male fly
   (~166k neurons). There is no reservoir of 34k untraced cells in that volume. What you *can*
   research is growing cells that obey the same type / side / synapse statistics — see below.

### Growing 34,000 real-like cells (166k → 200k)

A real adult fly does not have 200k central neurons. Asking for 34k more **true cells** therefore
means: sample new neurons from the same generative process the connectome implies, not from a
random graph and not from a grafted gadget with a new job.

`grow_like(connectome, 34_000)` does that:

1. Draw a cell type and side with probability equal to how common it is among population types.
2. Never draw identified cells (giant fiber `DNp01` stays one per side).
3. Bootstrap that type's real axons: out-degree and `(target, weight)` pairs are resampled from
   existing synapses of the same type (same partners, same sign, same typical strength).
4. Bootstrap dendrites the same way (existing cells grow collaterals onto the newborn).
5. Birth order: a newborn innervates the scaffold that is already there,
   **including earlier-born cells of this cohort** (new-to-new synapses). A cell
   born at step *k* cannot target a cell that does not exist yet.
6. The original MaleCNS block is copied unchanged — you can still tell which synapses were
   measured by EM.
7. Retinotopy: each new cell inherits a column from an existing cell of the same type
   (densifying the 6×8 lattice, not inventing new viewing directions). Partner sampling
   is weighted toward nearby columns (`column_tau=1.5`).
8. Hemilineage: `(type, side)` is the lineage proxy; `birth` continues the rank within
   that lineage. Identified neurons (`DNp01`) are never drawn.

```bash
flydrones circuit --grow 200 --grow-report docs/growth/minifly_plus200
python examples/06_grow_real.py
flydrones circuit --grow 34000 --brain data/malecns_brain.npz --grow-report docs/growth/malecns_plus34000
flydrones circuit --grow 5000 --grow-types T4c,DNg02 --brain data/malecns_brain.npz
```

The written report lists **every new neuron**: type, side, column `(row,col)`, hemilineage,
birth index, in/out degree, new-to-new synapses, and actual pre/post cell types. MiniFly
+200 (every row) and MiniFly +34,000 (CSV of all cells) live in [docs/growth/](growth/).

`flydrones circuit --clone T4c:96` copies **one** exemplar. `grow_like` copies the **type's
distribution**. Use clone when you mean "another T4c like this one"; use grow when you mean
"34k more neurons of the kinds this brain already has".

### MaleCNS-first: extra cells, then train

Flight read-out is not the whole CNS. Further neuron-growth work uses MaleCNS compartments
(mushroom body, central complex, VNC). See [RESEARCH_MALECNS.md](RESEARCH_MALECNS.md).

Extra cells follow the whole connectome. `flydrones expand --grow 160`
grows them, trains scene-up onto lift and legs (and loom onto escape), and
reads motor rates.

1. **New action.** Scene-up did not walk. After training it does. Extra cells
   make that walk stronger (40 Hz vs 123 Hz on MiniCNS).
2. **Stronger existing actions.** Lift and escape rates also rise after the
   same pairing, more so with extra cells.

```bash
python examples/07_malecns_expand.py
flydrones expand --brain minicns --grow 160
flydrones expand --brain data/malecns_brain.npz --grow 2000
```

### After development: hit a wall, dodge, ask again

Development teaches how to drive the legs. `examples/08_online.py` then puts
the animal in an arena. Contact (mdIV), halt (chordotonal), loom (LPLC2) and
unload enter the brain. PPL1 (and MBON rates) supply the teaching factor —
there is no `if hit: −1`. First approach hits and dodges. If that writing
stays on, the next approach does not hit.

Measured MiniCNS +80 (340 cells): first approach hits and dodges on both arms.
Second approach hits if the wall event was not written, and does not hit if
PPL1 judged it ([docs/growth/malecns_life.md](growth/malecns_life.md)).

```bash
python examples/08_online.py
flydrones expand --brain minicns --grow 80 --life
```

`flydrones circuit --compare` and `examples/04_rewire.py` run the same stimulus battery on several MiniFly variants:

| change | what actually happens | MiniFly `--compare` (seed 7) |
|---|---|---|
| **More synapses** (`--syn-scale 2`) | Each PSP is larger (`w_syn * count`). Reflexes get stronger, then saturate against the spike refractory cap (~450 Hz). | climb Δlift 66 → 160 Hz; giant fiber 59 → 104 Hz |
| **Weaker synapses** (`--syn-scale 0.3`) | Tonic bias on DNg02 still holds a rest rate (~31 Hz/side). Visual pathways no longer push HS/VS/DNg02 off that rest, so the drone cannot climb, turn or escape. | every reflex *delta* goes to 0; rest firing stays |
| **More of each cell type** (`--pop-scale 2`) | Rebuild MiniFly with larger pops (except DNp01). Same motifs, but drive onto each post grows (~4× connections). A louder circuit. | climb 66 → ~170 Hz; giant fiber count stays 2 |
| **Clone one type** (`--clone T4c:96`) | Copy T4c axons onto the same VS cells. Other pathways untouched. | climb 66 → **101 Hz**; yaw and looming stay |
| **Clone, drive held** (`--clone T4c:96 --normalize`) | Same copies, outgoing weights of T4c scaled down. Extra cells average noise. | climb **65 Hz** (≈ baseline) |
| **Unconnected padding** (`--extra-neurons 400`) | Isolated neurons never spike into the circuit. Flight is unchanged. At MiniFly size the extra membranes are cheap; on a 166k graph the per-step array work dominates (see [ARCHITECTURE.md](ARCHITECTURE.md)). | identical rates to baseline |
| **Cut a pathway** (`--ablate T4c:VS`) | Scene-up never reaches VS → DNg02. Open-palm climb dies; yaw and looming use different axons and stay. | climb Δlift 66 → 0; yaw and giant fiber untouched |
| **Flip a transmitter** (`--flip LPi_v`) | Inhibitory LPi_v becomes excitatory. Downward motion, which should *cut* lift, starts *adding* lift. | descent Δlift −60 → **+39 Hz** (sign reversal) |
| **Cross the midline** (`--reverse HS`) | HS axons land on the other hemisphere. Rightward flow that used to raise right DNg02 now raises left. | yaw R−L +17 → **−17 Hz** |
| **Shuffle addresses** (`--shuffle`) | Same axons, same synapse counts, random targets. Circuit identity is gone. | reflexes near zero; decoder still watches DNg02, which no longer means "climb" |

**What does *not* change when you rewire:** the linear decoder, the safety governor, the drone backend,
the camera → T4/T5 encoding. `flydrones calibrate` can retune the read-out weights, but it cannot
restore a pathway you cut — if DNg02 never sees T4c, no gain will make the drone climb to an open palm.

On MaleCNS the same operations apply to a built `.npz` (`--brain data/malecns_brain.npz --ablate ...`).
Population scaling (`--pop-scale`) is MiniFly-only: you cannot invent traced neurons that EM did not reconstruct.

## Embodiment: drone vs NeuroMechFly

[NeuroMechFly](https://neuromechfly.org) (FlyGym, EPFL Neuroengineering Lab) is a digital twin of the
adult fly: micro-CT body, compound-eye ommatidia, odor sensors, leg adhesion, and a ventral-nerve-cord
layer that turns a **two-value descending command** into a walking CPG
([Wang-Chen et al., *Nat Methods* 2024](https://www.nature.com/articles/s41592-024-02497-y);
turning-controller tutorial: left/right drive in about `[0.4, 1.2]`).

FlyDrones is the complementary half: a connectome LIF brain whose motor is six descending-neuron rates.
The two stacks meet at that descending interface:

| FlyDrones | NeuroMechFly HybridTurningController |
|---|---|
| `DNg02_L`, `DNg02_R` (Hz) | `descending_signal = [left, right]` |
| drone stick `throttle ∝ L+R`, `yaw ∝ R−L` | CPG amplitude L vs R, then joint + adhesion |
| Tello / Crazyflie / sim quad | MuJoCo fly on flat or mixed terrain |
| software optic flow on a camera | hexagonal ommatidia (`get_ommatidia_readouts`) |

**This mapping is engineering.** DNg02 is a *flight* descending neuron (wing-stroke amplitude). Walking
uses other DNs. We reuse the independent left/right pattern because that is what both APIs actually
expose, the same way we reuse it as a quad stick. Giant-fiber escape becomes a halt (`[0.2, 0.2]`), not
a jump takeoff. Compound-eye pixels are not yet wired into MiniFly's R1–R6; the first bridge uses the
same gesture/camera retina as the drone backends.

`examples/05_neuromechfly.py` prints the descending vector for each MiniFly stimulus, and shows that
reversing HS laterality **swaps L/R drive** — the walking fly would turn the wrong way for the same
reason the drone would. Optional body:

```bash
pip install 'flygym @ git+https://github.com/NeLy-EPFL/flygym.git@v2.1.0'
flydrones fly --drone flygym --config configs/neuromechfly.yaml --input gesture --seconds 8
```

Use that config: FlyGym units are millimetres, and the drone safety floor (0.3 m) would pin a 1 mm
animal to the ground.

## Known limitations

- Point neurons: no dendrites, no gap junctions, no neuromodulator *dynamics*. Motor pathways and KC→MBON use a rate-based three-factor rule (development, then optional online). Teaching valence is a scalar, not an intracellular dopamine cascade or PPL1 spike train.
- Motion vision computed by software instead of by the connectome's own early visual system.
- A 5 cm drone camera and a fly's 360° compound eye see very different worlds.
- Real flies fly at ~200 wingbeats per second with millisecond reflexes; the loop here runs at 20-50 Hz.
- The simulator has no aerodynamics, only a first-order velocity response like a Tello in stick mode.

## References

1. MaleCNS connectome project, [male-cns.janelia.org](https://male-cns.janelia.org/). *Sexual dimorphism in the complete connectome of the Drosophila male central nervous system*, *Cell* 2026.
2. Shiu P.K. et al. *A Drosophila computational brain model reveals sensorimotor processing.* *Nature* 2024.
3. Namiki S. et al. *A population of descending neurons that regulates the flight motor of Drosophila.* *Current Biology* 32(5), 2022.
4. Ache J.M. et al. *Neural basis for looming size and velocity encoding in the Drosophila giant fiber escape pathway.* *Current Biology* 2019.
5. *Activity of a descending neuron associated with visually elicited flight saccades in Drosophila.* *Current Biology* 2024.
6. *Drosophila DNp03 descending neurons serve as a hub within a flight saccade network.* *Current Biology* 2025.
7. Maisak M.S. et al. *A directional tuning map of Drosophila elementary motion detectors.* *Nature* 2013.
9. Wang-Chen S. et al. *NeuroMechFly v2: simulating embodied sensorimotor control in adult Drosophila.* *Nature Methods* 2024. [neuromechfly.org](https://neuromechfly.org).

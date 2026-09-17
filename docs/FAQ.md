# FAQ

**Is this a real fly brain?**
No. It is a simulation of neurons wired according to a real fly's measured synapses. No living tissue is
involved, and the model leaves out much of real neurobiology (see [SCIENCE.md](SCIENCE.md)).

**Did anyone write flight code?**
The brain contains no flight code. Around it there is engineering: optic-flow computation, a linear
read-out from descending neurons, a safety governor, and the drone's own stabilising flight controller.
All of that is open in this repo.

**Why do the GIFs use 850 neurons and not 166,000?**
So anyone can run the demo in seconds without a 1.2 GB download. Two commands switch to MaleCNS.

**Does it learn?**
Yes, at mushroom-body KC→MBON synapses. Pair an odor with reward or punishment
and the MBON readout (`MBON01 − MBON04`) acquires a preference the untrained
wiring did not have. Extra Kenyon cells without that pairing still do nothing
useful — an unread book. Collision-triggered PPL1 on the drone is still on the
roadmap. `flydrones expand --grow-kc 160`. [RESEARCH_MALECNS.md](RESEARCH_MALECNS.md).

**Does adding neurons give the fly new skills or more intelligence?**
After **training**, extra Kenyon cells can learn an odor preference the original
connectome was not born with, and they can separate good vs bad more strongly.
They do not sprout organs. Neuron count is not learning speed and not
wall-clock efficiency. Which behaviour you *see* still depends on the body
(drone stick vs walking fly). `--graft tail` is a leftover motor-pool probe, not
the research question. [RESEARCH_MALECNS.md](RESEARCH_MALECNS.md).

**Can I grow MaleCNS from 166k to 200k real cells?**
Not from EM: that volume is already complete. `flydrones circuit --grow 34000 --brain data/malecns_brain.npz`
resamples real type-to-type synapses so the extra cells have the same partners, signs and degrees as
existing population types (never the giant fiber). New cells inherit retinotopic columns, continue
the hemilineage birth order, and synapse onto already-born members of the cohort. The written
census of every new neuron is `flydrones circuit --grow N --grow-report ...` (see
[docs/growth/](growth/) and [SCIENCE.md](SCIENCE.md#growing-34000-real-like-cells-166k--200k)).

**What if I add neurons or synapses?**
New cells copy the motif of their type (same partners, same sign). `--clone T4c:96` does that;
`--pop-scale` rebuilds every population and also makes the circuit louder unless `--normalize`.
Unconnected padding does nothing to flight. The giant fiber stays one per side. Details:
[SCIENCE.md](SCIENCE.md#how-to-wire-a-new-neuron).

**What if I change the wiring?**
The drone still reads the same descending neurons. Cut T4c→VS and it will not climb; reverse HS laterality
and it turns the wrong way; shuffle the targets and the reflexes disappear. The decoder and the safety
governor do not compensate. `examples/04_rewire.py` prints the table.

**How does this relate to NeuroMechFly?**
NeuroMechFly is the body (MuJoCo fly, compound eyes, walking CPG). FlyDrones is the brain
(connectome LIF, descending neurons). They share a two-channel descending interface. See
[SCIENCE.md](SCIENCE.md#embodiment-drone-vs-neuromechfly), `examples/05_neuromechfly.py`, and
`flydrones fly --drone flygym --config configs/neuromechfly.yaml`.

**Can one brain fly a swarm?**
`flydrones swarm` copies one connectome into several brains with shared wiring and separate activity.
Each copy flies one drone. A real swarm would also need drone-to-drone collision avoidance.

**Windows?**
Yes. Use `.venv\Scripts\activate`, Tello over Wi-Fi works, Crazyradio needs the Zadig USB driver.

**Can the brain run on the drone?**
MiniFly or a small sensorimotor core can run on a Raspberry Pi class computer. Full MaleCNS needs a
laptop-class CPU for now.

**How do I cite this?**
See [CITATION.cff](../CITATION.cff), and please cite the MaleCNS paper and Shiu et al. 2024.

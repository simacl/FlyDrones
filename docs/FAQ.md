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
Not yet. The connectome weights are fixed. Dopamine-based plasticity (as in DOOMFLY) is on the roadmap.

**What if I add neurons or synapses?**
More synapses (stronger weights) make the same reflexes louder. More cells of an existing type also add
synapses, unless you pass `--normalize`. Neurons with no connections do nothing to flight and only cost
CPU. Try `flydrones circuit --compare`. Details: [SCIENCE.md](SCIENCE.md#what-if-you-add-neurons-add-synapses-or-rewire).

**What if I change the wiring?**
The drone still reads the same descending neurons. Cut T4c→VS and it will not climb; reverse HS laterality
and it turns the wrong way; shuffle the targets and the reflexes disappear. The decoder and the safety
governor do not compensate. `examples/04_rewire.py` prints the table.

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

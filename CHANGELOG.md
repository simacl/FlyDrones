# Changelog

## 0.1.3 - 2026-09-17
`flydrones circuit`: grow MiniFly, scale synapses, **clone a cell type's axons**, cut pathways, flip transmitters, reverse laterality
or shuffle addresses, and compare descending-neuron reflexes. See `examples/04_rewire.py`.
`grow_like` / `--grow 34000` resamples real type-to-type synapses so extra cells are statistically
the same kinds of neuron (MaleCNS 166k → 200k research path).
Optional NeuroMechFly body: map DNg02 L/R onto FlyGym's walking CPG (`flydrones fly --drone flygym`,
`examples/05_neuromechfly.py`). https://neuromechfly.org

## 0.1.2 - 2026-09-16
Live demo 2.0: detailed blue quadcopter with a fly mascot, furnished bedroom with walls, day/night themes, shadows,
swat-the-drone game driven by the looming pathway, click-to-stimulate neurons, clickable 3D objects, camera modes,
particles and sound.

## 0.1.1 - 2026-09-15
Browser demo on GitHub Pages (three.js, JS port of the engine, webcam hands), hero GIF, social preview image,
CI check that the browser engine matches Python.

## 0.1.0 - 2026-09-15
First public release: simulator, MaleCNS loader, MiniFly, retina, gestures, decoder, safety governor,
Tello / Crazyflie / MAVLink / ESP32 backends, dashboard, swarm, calibration, documentation.

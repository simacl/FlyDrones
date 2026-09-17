# MaleCNS research: new organs vs more intelligence

From this point the growth work is **MaleCNS-first**. MiniFly remains the flight demo.
MiniCNS (`build_minicns`, type names aligned with MaleCNS) is the unit-test stand-in
until `data/malecns_brain.npz` exists.

```bash
flydrones download malecns && flydrones build-brain --out data/malecns_brain.npz
flydrones expand --brain data/malecns_brain.npz --graft tail --graft extra_legs --grow-kc 2000 --report docs/growth/malecns_expand.md
# until the 1.2 GB download is present:
flydrones expand --brain minicns --graft tail --graft extra_legs --grow-kc 160
python examples/07_malecns_expand.py
```

Measured MiniCNS run: [docs/growth/malecns_expand.md](growth/malecns_expand.md).

## Question 1 — can extra neurons become a tail or two extra legs?

A real fly has no tail and six legs. **Resampling existing MaleCNS types cannot invent those organs.**
`grow_like(+100)` left `TailMN` and `LegMN_A3` **absent**.

What *can* be done is **grafting**: insert a new motor pool the connectome never had, and innervate it
from existing drivers.

| graft | driver | MiniCNS result |
|---|---|---|
| tail (`TailMN` ×8) | giant fiber `DNp01` | **coupled** to DNp01 (r=1.00). Loom 29.8 Hz, climb 0. The tail flicks when the fly already escapes. Extra muscle, not a new behaviour. |
| extra legs (`LegMN_A3` ×4 per side) | hindleg `T3_MN` | **coupled** to T3 (r=1.00). Silent in flight; **walk 214 Hz**. Serial homology: a seventh/eighth leg that copies the last segment. |

An independent new ability would require a **new internal state** (new descending type with its own sensory drive), not a muscle on an old command. Status `distinct` is reserved for that; it did not occur.

## Question 2 — can extra neurons make the brain more powerful or more intelligent?

Not by adding T4 or DNg02. Intelligence-related capacity in this CNS lives in the **mushroom body**
(Kenyon cells, MBON, PPL1/PAM) and, for navigation, the **central complex** (EPG, …).

| condition | n_KC | odor nearest-centroid accuracy | KC pattern rank |
|---|---:|---:|---:|
| MiniCNS baseline | 80 | 0.50 | 3 |
| `grow_like` +100 (includes some KC) | 106 | 1.00 | 19 |
| `expand_compartment kenyon` +160 | 240 | 1.00 | 17 |

More Kenyon cells raised odor-pattern rank and the linear classifier went from chance to ceiling
on this 4-glomerulus toy. That is **representational capacity**, not general intelligence:

- there is still no dopamine learning rule in the LIF (roadmap: PPL1 → KC→MBON plasticity)
- expanding random visual cells does not give this gain
- a 166k MaleCNS already has ~2k KCs; growing more is a testable capacity curve on the real types

## Two operations (do not mix them)

| | `grow_like` / `--grow-kc` | `graft_appendage` / `--graft` |
|---|---|---|
| cell types | only types MaleCNS already has | **new** types (`TailMN`, `LegMN_A3`) |
| can make a tail | no | yes, as a muscle |
| can raise odor capacity | yes, if you grow KC | no |
| biology | statistical neurogenesis | evolutionary / engineering graft |

On a built MaleCNS `.npz` the same CLI applies: `--grow-kc` matches `^KC`, `--graft tail` still inserts `TailMN` driven by `DNp01`.

# MaleCNS: add cells, train, read the body

MiniFly remains the flight demo. MiniCNS is the stand-in until
`data/malecns_brain.npz` exists. Extra cells follow the **whole** connectome,
not one sense.

```bash
flydrones expand --brain minicns --grow 160
python examples/07_malecns_expand.py
```

Measured MiniCNS run: [docs/growth/malecns_train.md](growth/malecns_train.md).

## What showed up

Scene-up used to lift and not walk. After adding 160 cells like the whole CNS
and pairing that visual cue with lift **and** the leg chain:

| | n | climb→lift | climb→walk | loom→escape |
|---|---:|---:|---:|---:|
| original, untrained | 242 | 64.3 Hz | **0** | 85.7 Hz |
| original, trained | 242 | 122.8 Hz | 40.2 Hz | 128.6 Hz |
| +160 cells, untrained | 402 | 71.9 Hz | **0** | 96.4 Hz |
| +160 cells, trained | 402 | 140.3 Hz | **123.2 Hz** | 167.9 Hz |

The new action is **walk to the same visual cue**. Extra cells without training
still do not walk to it. Extra cells after training walk harder than the small
brain after the same pairing.

## Where cells went

`grow_like(+160)` draws types the way the connectome already does — vision,
descending neurons, heading, legs, mushroom body — not “all Kenyon cells
unless you said so”. `--grow-types` can restrict; the default does not.

## Training

Rate-based three-factor updates on the pathways that actually reach motors:
T4c→VS→DNg02 (lift), T4c/VS/DNg02→T1→T2→T3 (walk), LPLC2→DNp01 (escape).

## Rule used

Δw ∝ presynaptic eligibility × teaching valence. Existing boutons move;
silent visual cells that had no leg boutons get some so the pairing has
something to write. No intracellular dopamine cascade.

Collision-triggered PPL1 on the drone is still a separate item.

## 经验有没有改用法

发育只教会怎么动腿。放到环境里用。痛、急停、卸力进脑子，PPL1 自己判定。
看前半和后半用法一不一样。

| | 前半接触 / 走 | 后半接触 / 走 | 用法变了 |
|---|---|---|---|
| 没写进去 | 2 / 12.3 Hz | 3 / 11.4 Hz | 否 |
| 当场写 | 2 / 11.1 Hz | 1 / 6.1 Hz | 是 |

```bash
python examples/08_online.py
flydrones expand --brain minicns --grow 80 --life
```

闭环：`learn.online: true`。身体多路信号进脑子，PPL1 判定，不在程序里写惩罚。

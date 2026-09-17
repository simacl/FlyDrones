# 生长报告（实际跑出来的新细胞）

MaleCNS v1.0 已经是一只雄蝇的完整中枢（~166k）。这里的 34k 新细胞不是 EM 多追出来的，
而是 `grow_like` 按类型频率、视网膜柱、半谱系出生顺序、新→新突触长出来的统计神经发生。
巨纤维 `DNp01` 始终 2 个。

| 报告 | 新细胞 | 全表 |
|---|---:|---|
| [minifly_plus200.md](minifly_plus200.md) | 200 | markdown 逐行 + [CSV](minifly_plus200_neurons.csv) |
| [minifly_plus34000.md](minifly_plus34000.md) | 34,000 | [CSV 全部 34,000 行](minifly_plus34000_neurons.csv) |
| [malecns_train.md](malecns_train.md) | +160 MiniCNS | 发育：全脑生长 + 配对，读运动 |
| [malecns_life.md](malecns_life.md) | +80 MiniCNS | 经验有没有改用法 |

重新生成：

```bash
python examples/06_grow_real.py
python examples/07_malecns_expand.py
# extra cells like the whole CNS, then train, then read motors
flydrones expand --brain minicns --grow 160 --report docs/growth/malecns_train.md
# after development: use the body, see if experience changes usage
python examples/08_online.py
flydrones expand --brain minicns --grow 80 --life --report docs/growth/malecns_life.md
# 或
flydrones circuit --grow 200 --grow-report docs/growth/minifly_plus200
```

MaleCNS（需先 `flydrones download malecns && flydrones build-brain`）：

```bash
flydrones circuit --grow 34000 --brain data/malecns_brain.npz --grow-report docs/growth/malecns_plus34000
```

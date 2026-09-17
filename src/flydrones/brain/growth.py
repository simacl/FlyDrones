"""Census and written report of neurons added by ``grow_like``."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .connectome import Connectome
from .rewire import pathway_weight

PATHWAYS = [
    ("climb T4c→VS", r"^T4c$", r"^VS$"),
    ("descend T4d→LPi_v", r"^T4d$", r"^LPi_v$"),
    ("yaw T4a→HS", r"^T4a$", r"^HS$"),
    ("yaw T4b→LPi_h", r"^T4b$", r"^LPi_h$"),
    ("loom LPLC2→DNp01", r"^LPLC2$", r"^DNp01$"),
    ("loom LC4→DNp01", r"^LC4$", r"^DNp01$"),
    ("saccade PVLP→DNp03", r"^PVLP$", r"^DNp03$"),
    ("lift VS→DNg02", r"^VS$", r"^DNg02$"),
    ("steer HS→DNg02", r"^HS$", r"^DNg02$"),
    ("haltere→DNg02", r"^haltere$", r"^DNg02$"),
]

TYPE_ROLE = {
    "T4c": "climb",
    "T4d": "descend",
    "T4a": "yaw",
    "T4b": "yaw",
    "LPLC2": "loom",
    "LC4": "loom",
    "DNp01": "escape",
    "DNp03": "saccade",
    "DNg02": "lift",
    "VS": "climb",
    "HS": "yaw",
    "haltere": "damping",
    "LPi_v": "descend",
    "LPi_h": "yaw",
    "PVLP": "loom",
    "PVLP_inh": "saccade",
    "LAL_inh": "steer",
    "R1-R6": "brightness",
}

CSV_FIELDS = [
    "new_index",
    "neuron_id",
    "body_id",
    "type",
    "side",
    "column",
    "row",
    "col",
    "lineage",
    "birth",
    "in_degree",
    "out_degree",
    "in_degree_new",
    "out_degree_new",
    "syn_in",
    "syn_out",
    "pre_types",
    "post_types",
    "pathways",
]


def _top_types(types: np.ndarray, limit: int = 4) -> str:
    if types.size == 0:
        return ""
    c = Counter(types.astype(str))
    return ",".join(f"{t}:{n}" for t, n in c.most_common(limit))


def _roles_for(cell_type: str, pre_types: np.ndarray, post_types: np.ndarray) -> str:
    tags = []
    own = TYPE_ROLE.get(cell_type)
    if own:
        tags.append(own)
    for arr, arrow in ((pre_types, "←"), (post_types, "→")):
        for t in Counter(arr.astype(str)):
            role = TYPE_ROLE.get(t)
            tag = f"{arrow}{role}" if role else ""
            if role and tag not in tags and role not in tags:
                tags.append(tag)
    return ",".join(tags)


def grown_old_n(grown: Connectome, base: Connectome | None = None) -> int:
    if base is not None:
        return base.n
    info = grown.meta.get("grown") or {}
    if "old_n" in info:
        return int(info["old_n"])
    if "n" in info:
        return grown.n - int(info["n"])
    raise ValueError("not a grown connectome (missing meta['grown'])")


def census_new_neurons(grown: Connectome, old_n: int) -> list[dict]:
    """One dict per new cell: identity, geometry, degrees, partners."""
    csc = grown.weights.tocsc()
    csr = grown.weights.tocsr()
    types = grown.types.astype(str)
    sides = grown.sides.astype(str)
    columns = grown.columns if grown.columns is not None else np.full(grown.n, -1, dtype=np.int32)
    lineage = grown.lineage.astype(str) if grown.lineage is not None else np.full(grown.n, "")
    birth = grown.birth if grown.birth is not None else np.full(grown.n, -1, dtype=np.int32)
    bids = grown.body_ids if grown.body_ids is not None else np.arange(grown.n)
    rc = grown.column_rc()
    rows: list[dict] = []
    for k, i in enumerate(range(old_n, grown.n)):
        p0, p1 = int(csc.indptr[i]), int(csc.indptr[i + 1])
        q0, q1 = int(csr.indptr[i]), int(csr.indptr[i + 1])
        posts = csc.indices[p0:p1]
        pres = csr.indices[q0:q1]
        wout = csc.data[p0:p1]
        win = csr.data[q0:q1]
        pre_types = types[pres] if pres.size else np.array([], dtype=str)
        post_types = types[posts] if posts.size else np.array([], dtype=str)
        rows.append(
            {
                "new_index": k,
                "neuron_id": int(i),
                "body_id": int(bids[i]),
                "type": types[i],
                "side": sides[i],
                "column": int(columns[i]),
                "row": int(rc[i, 0]),
                "col": int(rc[i, 1]),
                "lineage": str(lineage[i]),
                "birth": int(birth[i]),
                "in_degree": int(pres.size),
                "out_degree": int(posts.size),
                "in_degree_new": int((pres >= old_n).sum()),
                "out_degree_new": int((posts >= old_n).sum()),
                "syn_in": float(np.abs(win).sum()) if win.size else 0.0,
                "syn_out": float(np.abs(wout).sum()) if wout.size else 0.0,
                "pre_types": _top_types(pre_types),
                "post_types": _top_types(post_types),
                "pathways": _roles_for(types[i], pre_types, post_types),
            }
        )
    return rows


def new_to_new_count(grown: Connectome, old_n: int) -> int:
    W = grown.weights.tocoo()
    return int(((W.row >= old_n) & (W.col >= old_n)).sum())


def pathway_table(base: Connectome, grown: Connectome) -> list[dict]:
    rows = []
    for name, pre, post in PATHWAYS:
        n0, m0 = pathway_weight(base, pre, post)
        n1, m1 = pathway_weight(grown, pre, post)
        rows.append(
            {
                "pathway": name,
                "conn_before": n0,
                "conn_after": n1,
                "d_conn": n1 - n0,
                "mean_w_before": m0,
                "mean_w_after": m1,
            }
        )
    return rows


def column_occupancy(grown: Connectome, old_n: int, side: str) -> np.ndarray:
    """6×8 counts of new cells on one eye (optic-lobe types with a column)."""
    rows, cols = grown.grid
    heat = np.zeros((rows, cols), dtype=np.int32)
    rc = grown.column_rc()
    sides = grown.sides.astype(str)
    for i in range(old_n, grown.n):
        if sides[i] != side:
            continue
        r, c = int(rc[i, 0]), int(rc[i, 1])
        if r >= 0 and c >= 0 and r < rows and c < cols:
            heat[r, c] += 1
    return heat


@dataclass
class GrowthReport:
    base: Connectome
    grown: Connectome
    old_n: int
    neurons: list[dict] = field(default_factory=list)
    pathways: list[dict] = field(default_factory=list)
    reflexes: list[dict] = field(default_factory=list)

    @property
    def n_new(self) -> int:
        return self.grown.n - self.old_n


def build_growth_report(
    base: Connectome,
    grown: Connectome,
    cfg: dict | None = None,
    probe_kw: dict | None = None,
) -> GrowthReport:
    old_n = grown_old_n(grown, base)
    report = GrowthReport(base=base, grown=grown, old_n=old_n)
    report.neurons = census_new_neurons(grown, old_n)
    report.pathways = pathway_table(base, grown)
    if cfg is not None:
        from ..circuit import run_variant

        kw = dict(settle_ms=400, measure_ms=500, rest_ms=200)
        if probe_kw:
            kw.update(probe_kw)
        report.reflexes = [
            run_variant("baseline", base, cfg, **kw),
            run_variant(f"+{report.n_new} grown", grown, cfg, **kw),
        ]
    return report


def _heat_ascii(heat: np.ndarray) -> str:
    if heat.size == 0 or heat.max() == 0:
        return "(no cells with column coords on this side)"
    m = int(heat.max())
    glyphs = " ·░▒▓█"
    lines = []
    for row in heat:
        cells = []
        for v in row:
            if v <= 0:
                cells.append("·")
            else:
                cells.append(glyphs[min(5, 1 + int(v * 4 / m))])
        lines.append(" ".join(cells) + "   " + " ".join(f"{int(v):2d}" for v in row))
    return "\n".join(lines)


def format_growth_markdown(report: GrowthReport, *, list_all: bool | None = None) -> str:
    g, b = report.grown, report.base
    info = g.meta.get("grown") or {}
    n_new = report.n_new
    if list_all is None:
        list_all = n_new <= 400
    nn = new_to_new_count(g, report.old_n)
    by_type = Counter(r["type"] for r in report.neurons)
    by_side = Counter(r["side"] for r in report.neurons)
    by_lineage = Counter(r["lineage"] for r in report.neurons)
    by_path = Counter(p for r in report.neurons for p in (r["pathways"].split(",") if r["pathways"] else []))

    lines = [
        f"# 生长报告：{b.name} → {g.name}",
        "",
        "这不是 EM 多追了细胞。原连接组块原样保留；下面每一行都是 `grow_like` 按类型频率、",
        "视网膜柱、半谱系出生顺序抽出来的**新细胞**，轴突/树突来自同类型的经验分布，",
        "并允许接到已经出生的同胞（新→新突触）。巨纤维 DNp01 不复制。",
        "",
        "## 总量",
        "",
        "| 项目 | 生长前 | 生长后 | 增量 |",
        "|---|---:|---:|---:|",
        f"| 神经元 | {b.n:,} | {g.n:,} | +{n_new:,} |",
        f"| 有向连接 | {b.n_connections:,} | {g.n_connections:,} | +{g.n_connections - b.n_connections:,} |",
        f"| 突触数（|w|） | {b.n_synapses:,} | {g.n_synapses:,} | +{g.n_synapses - b.n_synapses:,} |",
        f"| 新→新 连接 | 0 | {nn:,} | +{nn:,} |",
        f"| DNp01（identified） | {int((b.types == 'DNp01').sum())} | {int((g.types == 'DNp01').sum())} | 0 |",
        "",
        f"seed={info.get('seed')}, column_tau={info.get('column_tau')}, min_pop={info.get('min_pop')}.",
        "",
        "## 按细胞类型（全部新增）",
        "",
        "| type | n_new | share | 典型通路 | 平均入度 | 平均出度 | 平均新→新出度 |",
        "|---|---:|---:|---|---:|---:|---:|",
    ]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in report.neurons:
        grouped[r["type"]].append(r)
    for t, n in by_type.most_common():
        rows = grouped[t]
        role = TYPE_ROLE.get(t, "")
        lines.append(
            f"| {t} | {n} | {n / n_new:.1%} | {role} | "
            f"{np.mean([r['in_degree'] for r in rows]):.1f} | "
            f"{np.mean([r['out_degree'] for r in rows]):.1f} | "
            f"{np.mean([r['out_degree_new'] for r in rows]):.2f} |"
        )
    lines += [
        "",
        f"左右：L={by_side.get('L', 0)}, R={by_side.get('R', 0)}。半谱系数 {len(by_lineage)}。",
        "",
        "## 半谱系（type_side）出生顺序",
        "",
        "每个 `(type, side)` 是一条半谱系代理。原细胞 birth = 0..n_old−1；新细胞接着往下编号。",
        "",
        "| lineage | 原细胞 | 新细胞 | birth 范围（新） |",
        "|---|---:|---:|---|",
    ]
    old_lin = Counter(b.lineage.astype(str)) if b.lineage is not None else Counter()
    for lin, n in by_lineage.most_common():
        births = [r["birth"] for r in report.neurons if r["lineage"] == lin]
        lines.append(f"| {lin} | {old_lin.get(lin, 0)} | {n} | {min(births)}–{max(births)} |")

    heat_l = column_occupancy(g, report.old_n, "L")
    heat_r = column_occupancy(g, report.old_n, "R")
    lines += [
        "",
        "## 视网膜柱占用（新细胞，6×8）",
        "",
        "每个新细胞继承同类型已有细胞的 column，所以是加密已有柱，不发明新的注视方向。",
        "`·░▒▓█` 是相对密度；右侧是计数。",
        "",
        "左眼 L",
        "",
        "```",
        _heat_ascii(heat_l),
        "```",
        "",
        "右眼 R",
        "",
        "```",
        _heat_ascii(heat_r),
        "```",
        "",
        "## 反射通路（生长前后）",
        "",
        "| 通路 | 连接前 | 连接后 | Δ | 平均权重前 | 平均权重后 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for p in report.pathways:
        lines.append(
            f"| {p['pathway']} | {p['conn_before']} | {p['conn_after']} | {p['d_conn']:+d} | "
            f"{p['mean_w_before']:.2f} | {p['mean_w_after']:.2f} |"
        )

    if report.reflexes:
        from ..circuit import format_table

        lines += ["", "## 下行神经元反射（刺激电池）", "", "```", format_table(report.reflexes), "```"]

    if by_path:
        lines += ["", "## 新细胞落入的功能标签", ""]
        lines.append(", ".join(f"{k}={v}" for k, v in by_path.most_common()))

    lines += [
        "",
        f"## 全部新增神经元（n={n_new}）",
        "",
    ]
    if list_all:
        lines += [
            "| # | id | type | side | col (r,c) | lineage | birth | kin | kout | k→new | 突触入/出 | 上游类型 | 下游类型 | 通路 |",
            "|---:|---:|---|---|---|---|---:|---:|---:|---:|---|---|---|---|",
        ]
        for r in report.neurons:
            lines.append(
                f"| {r['new_index']} | {r['neuron_id']} | {r['type']} | {r['side']} | "
                f"{r['column']} ({r['row']},{r['col']}) | {r['lineage']} | {r['birth']} | "
                f"{r['in_degree']} | {r['out_degree']} | {r['out_degree_new']} | "
                f"{r['syn_in']:.0f}/{r['syn_out']:.0f} | {r['pre_types']} | {r['post_types']} | {r['pathways']} |"
            )
    else:
        lines.append(f"行数太多，不在 markdown 里逐行列出。完整 {n_new} 行见同目录 CSV。下面是按类型各取 3 个样本。")
        lines += [
            "",
            "| # | id | type | side | col (r,c) | lineage | birth | kin | kout | k→new | 上游 | 下游 |",
            "|---:|---:|---|---|---|---|---:|---:|---:|---:|---|---|",
        ]
        seen: dict[str, int] = defaultdict(int)
        for r in report.neurons:
            if seen[r["type"]] >= 3:
                continue
            seen[r["type"]] += 1
            lines.append(
                f"| {r['new_index']} | {r['neuron_id']} | {r['type']} | {r['side']} | "
                f"{r['column']} ({r['row']},{r['col']}) | {r['lineage']} | {r['birth']} | "
                f"{r['in_degree']} | {r['out_degree']} | {r['out_degree_new']} | "
                f"{r['pre_types']} | {r['post_types']} |"
            )
    lines += [
        "",
        "列含义：`col (r,c)` 是 6×8 复眼格子；`lineage` 是半谱系代理 `type_side`；",
        "`birth` 是该谱系内的出生序号；`k→new` 是这条轴突落到其他新细胞上的条数；",
        "`上游/下游类型` 是实际接到的细胞类型计数。",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_growth_report(report: GrowthReport, dest: str | Path, *, list_all: bool | None = None) -> tuple[Path, Path]:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    md_path = dest.with_suffix(".md") if dest.suffix != ".md" else dest
    csv_path = md_path.with_name(md_path.stem + "_neurons.csv")
    md_path.write_text(format_growth_markdown(report, list_all=list_all), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for row in report.neurons:
            w.writerow({k: row[k] for k in CSV_FIELDS})
    return md_path, csv_path

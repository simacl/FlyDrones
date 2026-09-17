# 生长报告：minifly-synthetic → minifly-synthetic+200grown

这不是 EM 多追了细胞。原连接组块原样保留；下面每一行都是 `grow_like` 按类型频率、
视网膜柱、半谱系出生顺序抽出来的**新细胞**，轴突/树突来自同类型的经验分布，
并允许接到已经出生的同胞（新→新突触）。巨纤维 DNp01 不复制。

## 总量

| 项目 | 生长前 | 生长后 | 增量 |
|---|---:|---:|---:|
| 神经元 | 850 | 1,050 | +200 |
| 有向连接 | 4,928 | 6,195 | +1,267 |
| 突触数（|w|） | 31,904 | 46,424 | +14,520 |
| 新→新 连接 | 0 | 162 | +162 |
| DNp01（identified） | 2 | 2 | 0 |

seed=0, column_tau=1.5, min_pop=5.

## 按细胞类型（全部新增）

| type | n_new | share | 典型通路 | 平均入度 | 平均出度 | 平均新→新出度 |
|---|---:|---:|---|---:|---:|---:|
| R1-R6 | 41 | 20.5% | brightness | 0.0 | 0.1 | 0.07 |
| T4d | 29 | 14.5% | descend | 0.0 | 3.6 | 0.52 |
| T4c | 25 | 12.5% | climb | 0.0 | 3.7 | 1.08 |
| T4a | 24 | 12.0% | yaw | 0.0 | 1.6 | 0.00 |
| T4b | 20 | 10.0% | yaw | 0.0 | 3.5 | 0.10 |
| haltere | 11 | 5.5% | damping | 0.0 | 11.9 | 3.09 |
| LPLC2 | 10 | 5.0% | loom | 0.0 | 9.3 | 2.20 |
| DNg02 | 9 | 4.5% | lift | 26.9 | 0.0 | 0.00 |
| PVLP | 8 | 4.0% | loom | 17.0 | 4.9 | 0.88 |
| LAL_inh | 6 | 3.0% | steer | 14.0 | 7.2 | 2.17 |
| LC4 | 6 | 3.0% | loom | 0.0 | 8.8 | 1.83 |
| VS | 5 | 2.5% | climb | 23.8 | 13.4 | 4.40 |
| LPi_v | 3 | 1.5% | descend | 18.3 | 9.0 | 2.00 |
| PVLP_inh | 2 | 1.0% | saccade | 1.5 | 6.0 | 0.00 |
| LPi_h | 1 | 0.5% | yaw | 13.0 | 2.0 | 0.00 |

左右：L=94, R=106。半谱系数 29。

## 半谱系（type_side）出生顺序

每个 `(type, side)` 是一条半谱系代理。原细胞 birth = 0..n_old−1；新细胞接着往下编号。

| lineage | 原细胞 | 新细胞 | birth 范围（新） |
|---|---:|---:|---|
| R1-R6_R | 96 | 21 | 96–116 |
| R1-R6_L | 96 | 20 | 96–115 |
| T4d_R | 48 | 15 | 48–62 |
| T4c_R | 48 | 14 | 48–61 |
| T4d_L | 48 | 14 | 48–61 |
| T4a_R | 48 | 13 | 48–60 |
| T4b_L | 48 | 11 | 48–58 |
| T4c_L | 48 | 11 | 48–58 |
| T4a_L | 48 | 11 | 48–58 |
| T4b_R | 48 | 9 | 48–56 |
| LPLC2_R | 24 | 8 | 24–31 |
| DNg02_L | 15 | 6 | 15–20 |
| haltere_L | 16 | 6 | 16–21 |
| PVLP_R | 20 | 6 | 20–25 |
| haltere_R | 16 | 5 | 16–20 |
| LAL_inh_L | 12 | 3 | 12–14 |
| DNg02_R | 15 | 3 | 15–17 |
| LC4_R | 12 | 3 | 12–14 |
| LAL_inh_R | 12 | 3 | 12–14 |
| VS_R | 6 | 3 | 6–8 |
| LC4_L | 12 | 3 | 12–14 |
| LPi_v_L | 10 | 2 | 10–11 |
| PVLP_L | 20 | 2 | 20–21 |
| LPLC2_L | 24 | 2 | 24–25 |
| VS_L | 6 | 2 | 6–7 |
| PVLP_inh_R | 6 | 1 | 6–6 |
| PVLP_inh_L | 6 | 1 | 6–6 |
| LPi_h_R | 10 | 1 | 10–10 |
| LPi_v_R | 10 | 1 | 10–10 |

## 视网膜柱占用（新细胞，6×8）

每个新细胞继承同类型已有细胞的 column，所以是加密已有柱，不发明新的注视方向。
`·░▒▓█` 是相对密度；右侧是计数。

左眼 L

```
▒ · · · · ▓ · ·    3  0  0  1  1  4  1  1
█ █ · · ▓ · · ▒    5  5  0  1  4  1  1  3
░ · ░ · · · · ·    2  1  2  1  1  1  0  0
░ · ░ ░ ░ · ▒ █    2  0  2  2  2  0  3  5
· ▒ · · █ ▒ █ ░    1  3  1  1  5  3  5  2
▒ ░ · ▓ ▓ · · ▒    3  2  0  4  4  1  1  3
```

右眼 R

```
▒ · · · ░ ░ ▒ ▒    4  1  0  0  2  2  4  3
▒ █ · · · ▒ ▒ ▒    3  6  1  0  1  3  3  3
▒ · ░ ▒ ▒ · ░ ░    4  1  2  3  4  1  2  2
█ · ░ ░ ▒ · ▒ ░    6  0  2  2  4  1  3  2
· · ▒ · ▒ ░ ░ ▒    1  0  3  1  4  2  2  4
▓ ▒ · · · · · ▒    5  3  1  0  1  0  1  3
```

## 反射通路（生长前后）

| 通路 | 连接前 | 连接后 | Δ | 平均权重前 | 平均权重后 |
|---|---:|---:|---:|---:|---:|
| climb T4c→VS | 454 | 619 | +165 | 4.89 | 6.05 |
| descend T4d→LPi_v | 551 | 696 | +145 | 5.02 | 5.77 |
| yaw T4a→HS | 220 | 259 | +39 | 5.70 | 6.12 |
| yaw T4b→LPi_h | 464 | 544 | +80 | 5.05 | 5.56 |
| loom LPLC2→DNp01 | 48 | 49 | +1 | 3.02 | 3.04 |
| loom LC4→DNp01 | 24 | 28 | +4 | 3.04 | 3.54 |
| saccade PVLP→DNp03 | 70 | 73 | +3 | 12.34 | 12.62 |
| lift VS→DNg02 | 266 | 374 | +108 | 8.13 | 9.87 |
| steer HS→DNg02 | 80 | 92 | +12 | 10.64 | 11.16 |
| haltere→DNg02 | 338 | 459 | +121 | 4.04 | 4.84 |

## 下行神经元反射（刺激电池）

```
variant                    N    conn   climbΔlift   descΔlift    yaw R−L   loom GF    sacc L−R     rtf
------------------------------------------------------------------------------------------------------
baseline                 850    4928         63.7       -59.3       16.7      56.0        76.0    19.3x
+200 grown              1050    6195         86.4       -59.9       22.4      64.0        82.0    18.6x

climbΔlift  DNg02 L+R during scene-up minus rest. Open palm climb uses this.
descΔlift   same, scene-down. Hand-drop descent uses this (should be negative).
yaw R−L     DNg02_R − DNg02_L during rightward flow. Should be positive.
loom GF     giant-fiber rate (max L/R) during left looming. Escape trigger.
sacc L−R    DNp03_L − DNp03_R. Left loom should turn away (positive).
rtf         brain-time / wall-time of the last tick (higher = faster).
```

## 新细胞落入的功能标签

yaw=45, brightness=41, descend=32, climb=30, →lift=25, loom=24, →steer=19, ←damping=15, ←descend=14, damping=11, lift=9, ←yaw=9, ←steer=9, ←climb=8, ←saccade=7, steer=6, ←loom=6, →loom=5, →escape=5, →saccade=3, ←brightness=3, →climb=2, saccade=2

## 全部新增神经元（n=200）

| # | id | type | side | col (r,c) | lineage | birth | kin | kout | k→new | 突触入/出 | 上游类型 | 下游类型 | 通路 |
|---:|---:|---|---|---|---|---:|---:|---:|---:|---|---|---|---|
| 0 | 850 | T4b | L | 46 (5,6) | T4b_L | 48 | 0 | 3 | 0 | 0/31 |  | LPi_h:3 | yaw |
| 1 | 851 | R1-R6 | L | 15 (1,7) | R1-R6_L | 96 | 0 | 1 | 1 | 0/1 |  | PVLP:1 | brightness,→loom |
| 2 | 852 | LAL_inh | L | 4 (0,4) | LAL_inh_L | 12 | 11 | 11 | 4 | 104/243 | haltere:7,PVLP:4 | DNg02:11 | steer,←damping,←loom,→lift |
| 3 | 853 | DNg02 | L | 3 (0,3) | DNg02_L | 15 | 26 | 0 | 0 | 458/0 | haltere:8,LPi_v:6,LAL_inh:6,VS:5 |  | lift,←descend,←yaw,←climb,←steer,←damping |
| 4 | 854 | T4c | R | 5 (0,5) | T4c_R | 48 | 0 | 3 | 1 | 0/36 |  | VS:3 | climb |
| 5 | 855 | T4d | R | 39 (4,7) | T4d_R | 48 | 0 | 3 | 0 | 0/30 |  | LPi_v:3 | descend |
| 6 | 856 | T4b | L | 47 (5,7) | T4b_L | 49 | 0 | 3 | 0 | 0/27 |  | LPi_h:3 | yaw |
| 7 | 857 | T4c | L | 41 (5,1) | T4c_L | 48 | 0 | 3 | 1 | 0/31 |  | VS:3 | climb |
| 8 | 858 | T4a | L | 31 (3,7) | T4a_L | 48 | 0 | 2 | 0 | 0/19 |  | HS:2 | yaw |
| 9 | 859 | T4d | R | 15 (1,7) | T4d_R | 49 | 0 | 3 | 1 | 0/39 |  | LPi_v:3 | descend |
| 10 | 860 | T4c | R | 20 (2,4) | T4c_R | 49 | 0 | 3 | 0 | 0/25 |  | VS:3 | climb |
| 11 | 861 | DNg02 | L | 0 (0,0) | DNg02_L | 16 | 27 | 0 | 0 | 510/0 | VS:9,LAL_inh:9,haltere:4,LPi_v:3 |  | lift,←descend,←yaw,←climb,←steer,←damping |
| 12 | 862 | T4d | L | 40 (5,0) | T4d_L | 48 | 0 | 5 | 2 | 0/42 |  | LPi_v:5 | descend |
| 13 | 863 | DNg02 | R | 9 (1,1) | DNg02_R | 15 | 28 | 0 | 0 | 401/0 | VS:11,LAL_inh:8,haltere:4,HS:3 |  | lift,←damping,←climb,←descend,←yaw,←steer |
| 14 | 864 | T4c | L | 17 (2,1) | T4c_L | 49 | 0 | 5 | 2 | 0/55 |  | VS:5 | climb |
| 15 | 865 | LPi_v | L | 24 (3,0) | LPi_v_L | 10 | 17 | 9 | 1 | 140/103 | T4d:17 | DNg02:6,VS:3 | descend,→climb,→lift |
| 16 | 866 | T4d | L | 43 (5,3) | T4d_L | 49 | 0 | 3 | 0 | 0/28 |  | LPi_v:3 | descend |
| 17 | 867 | T4a | L | 37 (4,5) | T4a_L | 49 | 0 | 1 | 0 | 0/23 |  | HS:1 | yaw |
| 18 | 868 | R1-R6 | L | 47 (5,7) | R1-R6_L | 97 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 19 | 869 | R1-R6 | R | 7 (0,7) | R1-R6_R | 96 | 0 | 2 | 1 | 0/2 |  | PVLP:2 | brightness,→loom |
| 20 | 870 | DNg02 | R | 9 (1,1) | DNg02_R | 16 | 33 | 0 | 0 | 394/0 | haltere:9,VS:9,LAL_inh:7,LPi_v:6 |  | lift,←damping,←climb,←descend,←yaw,←steer |
| 21 | 871 | LPLC2 | R | 34 (4,2) | LPLC2_R | 24 | 0 | 11 | 2 | 0/99 |  | PVLP:11 | loom |
| 22 | 872 | T4b | R | 6 (0,6) | T4b_R | 48 | 0 | 1 | 0 | 0/16 |  | LPi_h:1 | yaw |
| 23 | 873 | T4b | L | 31 (3,7) | T4b_L | 50 | 0 | 2 | 0 | 0/23 |  | LPi_h:2 | yaw |
| 24 | 874 | T4b | L | 44 (5,4) | T4b_L | 51 | 0 | 5 | 0 | 0/40 |  | LPi_h:5 | yaw |
| 25 | 875 | R1-R6 | R | 5 (0,5) | R1-R6_R | 97 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 26 | 876 | haltere | R | 24 (3,0) | haltere_R | 16 | 0 | 14 | 5 | 0/83 |  | DNg02:7,LAL_inh:7 | damping,→lift,→steer |
| 27 | 877 | haltere | L | 18 (2,2) | haltere_L | 16 | 0 | 13 | 3 | 0/93 |  | DNg02:8,LAL_inh:5 | damping,→steer,→lift |
| 28 | 878 | T4b | R | 9 (1,1) | T4b_R | 49 | 0 | 3 | 1 | 0/33 |  | LPi_h:3 | yaw |
| 29 | 879 | T4b | L | 24 (3,0) | T4b_L | 52 | 0 | 4 | 0 | 0/30 |  | LPi_h:4 | yaw |
| 30 | 880 | T4b | R | 6 (0,6) | T4b_R | 50 | 0 | 4 | 0 | 0/19 |  | LPi_h:4 | yaw |
| 31 | 881 | R1-R6 | R | 0 (0,0) | R1-R6_R | 98 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 32 | 882 | LPLC2 | R | 34 (4,2) | LPLC2_R | 25 | 0 | 9 | 1 | 0/99 |  | PVLP:9 | loom |
| 33 | 883 | T4c | L | 44 (5,4) | T4c_L | 50 | 0 | 2 | 0 | 0/13 |  | VS:2 | climb |
| 34 | 884 | T4a | L | 37 (4,5) | T4a_L | 50 | 0 | 2 | 0 | 0/16 |  | HS:2 | yaw |
| 35 | 885 | R1-R6 | L | 36 (4,4) | R1-R6_L | 98 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 36 | 886 | R1-R6 | R | 40 (5,0) | R1-R6_R | 99 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 37 | 887 | T4d | L | 18 (2,2) | T4d_L | 50 | 0 | 3 | 1 | 0/35 |  | LPi_v:3 | descend |
| 38 | 888 | T4d | R | 41 (5,1) | T4d_R | 50 | 0 | 3 | 0 | 0/29 |  | LPi_v:3 | descend |
| 39 | 889 | R1-R6 | L | 31 (3,7) | R1-R6_L | 99 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 40 | 890 | T4a | R | 30 (3,6) | T4a_R | 48 | 0 | 2 | 0 | 0/12 |  | HS:2 | yaw |
| 41 | 891 | R1-R6 | L | 12 (1,4) | R1-R6_L | 100 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 42 | 892 | T4a | R | 14 (1,6) | T4a_R | 49 | 0 | 2 | 0 | 0/15 |  | HS:2 | yaw |
| 43 | 893 | R1-R6 | L | 36 (4,4) | R1-R6_L | 101 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 44 | 894 | R1-R6 | R | 42 (5,2) | R1-R6_R | 100 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 45 | 895 | T4d | R | 22 (2,6) | T4d_R | 51 | 0 | 5 | 1 | 0/34 |  | LPi_v:5 | descend |
| 46 | 896 | PVLP | R | 26 (3,2) | PVLP_R | 20 | 22 | 7 | 2 | 210/43 | LPLC2:12,LC4:7,PVLP_inh:3 | LAL_inh:6,DNp03:1 | loom,←saccade,→steer,→saccade |
| 47 | 897 | T4b | L | 44 (5,4) | T4b_L | 53 | 0 | 5 | 0 | 0/38 |  | LPi_h:5 | yaw |
| 48 | 898 | LC4 | R | 24 (3,0) | LC4_R | 12 | 0 | 10 | 3 | 0/91 |  | PVLP:9,DNp01:1 | loom,→escape |
| 49 | 899 | T4c | R | 6 (0,6) | T4c_R | 50 | 0 | 2 | 0 | 0/29 |  | VS:2 | climb |
| 50 | 900 | T4c | R | 22 (2,6) | T4c_R | 51 | 0 | 5 | 1 | 0/32 |  | VS:5 | climb |
| 51 | 901 | PVLP | R | 7 (0,7) | PVLP_R | 21 | 14 | 4 | 0 | 125/14 | LPLC2:8,R1-R6:4,LC4:2 | LAL_inh:4 | loom,←brightness,→steer |
| 52 | 902 | T4d | L | 33 (4,1) | T4d_L | 51 | 0 | 4 | 1 | 0/36 |  | LPi_v:4 | descend |
| 53 | 903 | LAL_inh | R | 36 (4,4) | LAL_inh_R | 12 | 19 | 6 | 1 | 121/214 | haltere:10,PVLP:9 | DNg02:6 | steer,←damping,←loom,→lift |
| 54 | 904 | R1-R6 | L | 0 (0,0) | R1-R6_L | 102 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 55 | 905 | LPLC2 | R | 24 (3,0) | LPLC2_R | 26 | 0 | 11 | 3 | 0/120 |  | PVLP:10,DNp01:1 | loom,→escape |
| 56 | 906 | R1-R6 | R | 20 (2,4) | R1-R6_R | 101 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 57 | 907 | T4c | R | 41 (5,1) | T4c_R | 52 | 0 | 5 | 2 | 0/35 |  | VS:5 | climb |
| 58 | 908 | PVLP | R | 19 (2,3) | PVLP_R | 22 | 21 | 7 | 0 | 156/18 | LPLC2:15,LC4:5,PVLP_inh:1 | LAL_inh:7 | loom,←saccade,→steer |
| 59 | 909 | LAL_inh | R | 40 (5,0) | LAL_inh_R | 13 | 14 | 5 | 0 | 210/180 | haltere:6,PVLP:4,HS:3,DNp03:1 | DNg02:5 | steer,←yaw,←damping,←loom,←saccade,→lift |
| 60 | 910 | R1-R6 | R | 28 (3,4) | R1-R6_R | 102 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 61 | 911 | PVLP | L | 45 (5,5) | PVLP_L | 20 | 17 | 4 | 1 | 180/11 | LPLC2:10,LC4:6,PVLP_inh:1 | LAL_inh:4 | loom,←saccade,→steer |
| 62 | 912 | LC4 | R | 40 (5,0) | LC4_R | 13 | 0 | 7 | 1 | 0/54 |  | PVLP:6,DNp01:1 | loom,→escape |
| 63 | 913 | T4a | R | 16 (2,0) | T4a_R | 50 | 0 | 2 | 0 | 0/14 |  | HS:2 | yaw |
| 64 | 914 | R1-R6 | L | 36 (4,4) | R1-R6_L | 103 | 0 | 1 | 1 | 0/1 |  | PVLP:1 | brightness,→loom |
| 65 | 915 | T4b | R | 9 (1,1) | T4b_R | 51 | 0 | 4 | 1 | 0/34 |  | LPi_h:4 | yaw |
| 66 | 916 | PVLP | L | 7 (0,7) | PVLP_L | 21 | 17 | 2 | 1 | 190/3 | LPLC2:9,R1-R6:6,LC4:2 | LAL_inh:2 | loom,←brightness,→steer |
| 67 | 917 | T4d | R | 31 (3,7) | T4d_R | 52 | 0 | 4 | 0 | 0/36 |  | LPi_v:4 | descend |
| 68 | 918 | R1-R6 | L | 5 (0,5) | R1-R6_L | 104 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 69 | 919 | LPLC2 | L | 14 (1,6) | LPLC2_L | 24 | 0 | 10 | 2 | 0/114 |  | PVLP:10 | loom |
| 70 | 920 | T4b | L | 26 (3,2) | T4b_L | 54 | 0 | 4 | 0 | 0/31 |  | LPi_h:4 | yaw |
| 71 | 921 | T4d | R | 19 (2,3) | T4d_R | 53 | 0 | 5 | 0 | 0/32 |  | LPi_v:5 | descend |
| 72 | 922 | R1-R6 | R | 38 (4,6) | R1-R6_R | 103 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 73 | 923 | VS | L | 8 (1,0) | VS_L | 6 | 24 | 11 | 4 | 231/206 | T4c:20,LPi_v:4 | DNg02:11 | climb,←descend,→lift |
| 74 | 924 | T4a | L | 30 (3,6) | T4a_L | 51 | 0 | 2 | 0 | 0/11 |  | HS:2 | yaw |
| 75 | 925 | R1-R6 | R | 10 (1,2) | R1-R6_R | 104 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 76 | 926 | T4b | L | 11 (1,3) | T4b_L | 55 | 0 | 3 | 0 | 0/18 |  | LPi_h:3 | yaw |
| 77 | 927 | haltere | R | 36 (4,4) | haltere_R | 17 | 0 | 15 | 4 | 0/115 |  | DNg02:9,LAL_inh:6 | damping,→lift,→steer |
| 78 | 928 | VS | L | 0 (0,0) | VS_L | 7 | 24 | 10 | 3 | 226/224 | T4c:19,LPi_v:5 | DNg02:10 | climb,←descend,→lift |
| 79 | 929 | R1-R6 | R | 13 (1,5) | R1-R6_R | 105 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 80 | 930 | T4c | L | 38 (4,6) | T4c_L | 51 | 0 | 4 | 0 | 0/20 |  | VS:4 | climb |
| 81 | 931 | T4a | L | 8 (1,0) | T4a_L | 52 | 0 | 1 | 0 | 0/7 |  | HS:1 | yaw |
| 82 | 932 | T4a | L | 26 (3,2) | T4a_L | 53 | 0 | 1 | 0 | 0/19 |  | HS:1 | yaw |
| 83 | 933 | T4c | R | 13 (1,5) | T4c_R | 53 | 0 | 4 | 1 | 0/24 |  | VS:4 | climb |
| 84 | 934 | R1-R6 | R | 47 (5,7) | R1-R6_R | 106 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 85 | 935 | T4c | L | 5 (0,5) | T4c_L | 52 | 0 | 2 | 0 | 0/22 |  | VS:2 | climb |
| 86 | 936 | T4b | R | 35 (4,3) | T4b_R | 52 | 0 | 4 | 0 | 0/16 |  | LPi_h:4 | yaw |
| 87 | 937 | T4d | R | 26 (3,2) | T4d_R | 54 | 0 | 5 | 0 | 0/27 |  | LPi_v:5 | descend |
| 88 | 938 | LPLC2 | L | 38 (4,6) | LPLC2_L | 25 | 0 | 8 | 1 | 0/98 |  | PVLP:8 | loom |
| 89 | 939 | T4c | L | 32 (4,0) | T4c_L | 53 | 0 | 3 | 1 | 0/19 |  | VS:3 | climb |
| 90 | 940 | T4d | R | 6 (0,6) | T4d_R | 55 | 0 | 3 | 1 | 0/34 |  | LPi_v:3 | descend |
| 91 | 941 | haltere | L | 15 (1,7) | haltere_L | 17 | 0 | 11 | 1 | 0/66 |  | DNg02:7,LAL_inh:4 | damping,→steer,→lift |
| 92 | 942 | DNg02 | L | 44 (5,4) | DNg02_L | 17 | 24 | 0 | 0 | 436/0 | haltere:10,LAL_inh:9,VS:4,LPi_v:1 |  | lift,←descend,←climb,←steer,←damping |
| 93 | 943 | T4d | L | 38 (4,6) | T4d_L | 52 | 0 | 2 | 0 | 0/21 |  | LPi_v:2 | descend |
| 94 | 944 | haltere | R | 24 (3,0) | haltere_R | 18 | 0 | 10 | 3 | 0/81 |  | LAL_inh:6,DNg02:4 | damping,→lift,→steer |
| 95 | 945 | VS | R | 16 (2,0) | VS_R | 6 | 23 | 17 | 6 | 224/228 | T4c:18,LPi_v:5 | DNg02:17 | climb,←descend,→lift |
| 96 | 946 | LPLC2 | R | 38 (4,6) | LPLC2_R | 27 | 0 | 9 | 4 | 0/109 |  | PVLP:9 | loom |
| 97 | 947 | haltere | L | 30 (3,6) | haltere_L | 18 | 0 | 13 | 2 | 0/82 |  | DNg02:9,LAL_inh:4 | damping,→steer,→lift |
| 98 | 948 | T4d | L | 9 (1,1) | T4d_L | 53 | 0 | 6 | 2 | 0/45 |  | LPi_v:6 | descend |
| 99 | 949 | T4c | R | 4 (0,4) | T4c_R | 54 | 0 | 2 | 0 | 0/22 |  | VS:2 | climb |
| 100 | 950 | R1-R6 | R | 23 (2,7) | R1-R6_R | 107 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 101 | 951 | PVLP | R | 7 (0,7) | PVLP_R | 23 | 13 | 5 | 1 | 140/24 | LPLC2:8,LC4:3,R1-R6:2 | LAL_inh:4,DNp03:1 | loom,←brightness,→steer,→saccade |
| 102 | 952 | T4c | R | 17 (2,1) | T4c_R | 55 | 0 | 4 | 2 | 0/58 |  | VS:4 | climb |
| 103 | 953 | T4d | R | 47 (5,7) | T4d_R | 56 | 0 | 3 | 0 | 0/37 |  | LPi_v:3 | descend |
| 104 | 954 | R1-R6 | L | 43 (5,3) | R1-R6_L | 105 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 105 | 955 | T4a | L | 34 (4,2) | T4a_L | 54 | 0 | 2 | 0 | 0/15 |  | HS:2 | yaw |
| 106 | 956 | R1-R6 | R | 39 (4,7) | R1-R6_R | 108 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 107 | 957 | T4d | R | 1 (0,1) | T4d_R | 57 | 0 | 2 | 0 | 0/31 |  | LPi_v:2 | descend |
| 108 | 958 | LAL_inh | L | 36 (4,4) | LAL_inh_L | 13 | 17 | 7 | 3 | 76/226 | PVLP:9,haltere:8 | DNg02:7 | steer,←damping,←loom,→lift |
| 109 | 959 | T4c | L | 38 (4,6) | T4c_L | 54 | 0 | 4 | 1 | 0/22 |  | VS:4 | climb |
| 110 | 960 | T4b | L | 39 (4,7) | T4b_L | 56 | 0 | 4 | 0 | 0/25 |  | LPi_h:4 | yaw |
| 111 | 961 | DNg02 | R | 9 (1,1) | DNg02_R | 17 | 36 | 0 | 0 | 397/0 | haltere:11,VS:10,LAL_inh:9,LPi_v:6 |  | lift,←damping,←climb,←descend,←steer |
| 112 | 962 | T4c | L | 33 (4,1) | T4c_L | 55 | 0 | 4 | 1 | 0/28 |  | VS:4 | climb |
| 113 | 963 | DNg02 | L | 41 (5,1) | DNg02_L | 18 | 22 | 0 | 0 | 331/0 | VS:7,LAL_inh:6,haltere:5,LPi_v:2 |  | lift,←descend,←yaw,←climb,←steer,←damping |
| 114 | 964 | T4c | L | 35 (4,3) | T4c_L | 56 | 0 | 3 | 1 | 0/24 |  | VS:3 | climb |
| 115 | 965 | T4a | L | 21 (2,5) | T4a_L | 55 | 0 | 3 | 0 | 0/15 |  | HS:3 | yaw |
| 116 | 966 | T4d | R | 8 (1,0) | T4d_R | 58 | 0 | 4 | 0 | 0/28 |  | LPi_v:4 | descend |
| 117 | 967 | LC4 | L | 16 (2,0) | LC4_L | 12 | 0 | 6 | 1 | 0/47 |  | PVLP:6 | loom |
| 118 | 968 | T4d | L | 27 (3,3) | T4d_L | 54 | 0 | 4 | 1 | 0/26 |  | LPi_v:4 | descend |
| 119 | 969 | LC4 | L | 12 (1,4) | LC4_L | 13 | 0 | 9 | 1 | 0/53 |  | PVLP:8,DNp01:1 | loom,→escape |
| 120 | 970 | R1-R6 | L | 8 (1,0) | R1-R6_L | 106 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 121 | 971 | R1-R6 | R | 27 (3,3) | R1-R6_R | 109 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 122 | 972 | haltere | L | 9 (1,1) | haltere_L | 19 | 0 | 12 | 5 | 0/89 |  | DNg02:7,LAL_inh:5 | damping,→steer,→lift |
| 123 | 973 | T4a | R | 16 (2,0) | T4a_R | 51 | 0 | 2 | 0 | 0/19 |  | HS:2 | yaw |
| 124 | 974 | PVLP_inh | R | 0 (0,0) | PVLP_inh_R | 6 | 1 | 6 | 0 | 71/173 | DNp03:1 | PVLP:5,DNp03:1 | saccade,→loom |
| 125 | 975 | PVLP | R | 16 (2,0) | PVLP_R | 24 | 15 | 5 | 1 | 139/36 | LPLC2:7,PVLP_inh:5,LC4:3 | LAL_inh:4,DNp03:1 | loom,←saccade,→steer,→saccade |
| 126 | 976 | T4d | L | 20 (2,4) | T4d_L | 55 | 0 | 4 | 2 | 0/27 |  | LPi_v:4 | descend |
| 127 | 977 | PVLP | R | 36 (4,4) | PVLP_R | 25 | 17 | 5 | 1 | 211/17 | LPLC2:12,LC4:5 | LAL_inh:5 | loom,→steer |
| 128 | 978 | LPLC2 | R | 46 (5,6) | LPLC2_R | 28 | 0 | 7 | 1 | 0/93 |  | PVLP:7 | loom |
| 129 | 979 | R1-R6 | L | 9 (1,1) | R1-R6_L | 107 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 130 | 980 | T4a | R | 37 (4,5) | T4a_R | 52 | 0 | 1 | 0 | 0/6 |  | HS:1 | yaw |
| 131 | 981 | T4a | R | 18 (2,2) | T4a_R | 53 | 0 | 1 | 0 | 0/18 |  | HS:1 | yaw |
| 132 | 982 | T4c | R | 20 (2,4) | T4c_R | 56 | 0 | 4 | 1 | 0/35 |  | VS:4 | climb |
| 133 | 983 | T4a | R | 39 (4,7) | T4a_R | 54 | 0 | 1 | 0 | 0/5 |  | HS:1 | yaw |
| 134 | 984 | R1-R6 | L | 36 (4,4) | R1-R6_L | 108 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 135 | 985 | R1-R6 | R | 41 (5,1) | R1-R6_R | 110 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 136 | 986 | T4c | R | 29 (3,5) | T4c_R | 57 | 0 | 5 | 2 | 0/31 |  | VS:5 | climb |
| 137 | 987 | T4b | L | 16 (2,0) | T4b_L | 57 | 0 | 3 | 0 | 0/28 |  | LPi_h:3 | yaw |
| 138 | 988 | VS | R | 8 (1,0) | VS_R | 7 | 23 | 14 | 5 | 232/171 | T4c:20,LPi_v:3 | DNg02:14 | climb,←descend,→lift |
| 139 | 989 | R1-R6 | L | 40 (5,0) | R1-R6_L | 109 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 140 | 990 | T4a | R | 14 (1,6) | T4a_R | 55 | 0 | 2 | 0 | 0/20 |  | HS:2 | yaw |
| 141 | 991 | T4a | R | 4 (0,4) | T4a_R | 56 | 0 | 1 | 0 | 0/12 |  | HS:1 | yaw |
| 142 | 992 | T4d | L | 28 (3,4) | T4d_L | 56 | 0 | 4 | 0 | 0/36 |  | LPi_v:4 | descend |
| 143 | 993 | LPLC2 | R | 30 (3,6) | LPLC2_R | 29 | 0 | 10 | 3 | 0/89 |  | PVLP:10 | loom |
| 144 | 994 | R1-R6 | R | 47 (5,7) | R1-R6_R | 111 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 145 | 995 | T4d | R | 40 (5,0) | T4d_R | 59 | 0 | 4 | 0 | 0/22 |  | LPi_v:4 | descend |
| 146 | 996 | LAL_inh | L | 8 (1,0) | LAL_inh_L | 14 | 14 | 8 | 3 | 218/227 | haltere:5,PVLP:4,HS:3,DNp03:2 | DNg02:8 | steer,←damping,←loom,←saccade,←yaw,→lift |
| 147 | 997 | T4c | R | 15 (1,7) | T4c_R | 58 | 0 | 3 | 1 | 0/27 |  | VS:3 | climb |
| 148 | 998 | R1-R6 | R | 28 (3,4) | R1-R6_R | 112 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 149 | 999 | T4c | R | 28 (3,4) | T4c_R | 59 | 0 | 4 | 1 | 0/30 |  | VS:4 | climb |
| 150 | 1000 | DNg02 | L | 9 (1,1) | DNg02_L | 19 | 27 | 0 | 0 | 443/0 | VS:8,LAL_inh:7,LPi_v:5,haltere:5 |  | lift,←descend,←yaw,←climb,←steer,←damping |
| 151 | 1001 | R1-R6 | L | 39 (4,7) | R1-R6_L | 110 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 152 | 1002 | LC4 | L | 8 (1,0) | LC4_L | 14 | 0 | 9 | 2 | 0/51 |  | PVLP:8,DNp01:1 | loom,→escape |
| 153 | 1003 | T4b | L | 5 (0,5) | T4b_L | 58 | 0 | 4 | 0 | 0/34 |  | LPi_h:4 | yaw |
| 154 | 1004 | R1-R6 | L | 27 (3,3) | R1-R6_L | 111 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 155 | 1005 | T4b | R | 12 (1,4) | T4b_R | 53 | 0 | 3 | 0 | 0/30 |  | LPi_h:3 | yaw |
| 156 | 1006 | T4d | R | 0 (0,0) | T4d_R | 60 | 0 | 2 | 0 | 0/32 |  | LPi_v:2 | descend |
| 157 | 1007 | LPLC2 | R | 44 (5,4) | LPLC2_R | 30 | 0 | 6 | 1 | 0/91 |  | PVLP:6 | loom |
| 158 | 1008 | T4d | L | 12 (1,4) | T4d_L | 57 | 0 | 3 | 0 | 0/19 |  | LPi_v:3 | descend |
| 159 | 1009 | LAL_inh | R | 0 (0,0) | LAL_inh_R | 14 | 9 | 6 | 2 | 390/205 | haltere:3,HS:2,PVLP:2,DNp03:2 | DNg02:6 | steer,←yaw,←damping,←loom,←saccade,→lift |
| 160 | 1010 | R1-R6 | R | 27 (3,3) | R1-R6_R | 113 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 161 | 1011 | R1-R6 | R | 40 (5,0) | R1-R6_R | 114 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 162 | 1012 | R1-R6 | R | 20 (2,4) | R1-R6_R | 115 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 163 | 1013 | haltere | L | 33 (4,1) | haltere_L | 20 | 0 | 11 | 2 | 0/72 |  | DNg02:8,LAL_inh:3 | damping,→steer,→lift |
| 164 | 1014 | T4c | R | 32 (4,0) | T4c_R | 60 | 0 | 5 | 2 | 0/23 |  | VS:5 | climb |
| 165 | 1015 | R1-R6 | L | 37 (4,5) | R1-R6_L | 112 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 166 | 1016 | R1-R6 | L | 43 (5,3) | R1-R6_L | 113 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 167 | 1017 | T4d | L | 28 (3,4) | T4d_L | 58 | 0 | 4 | 0 | 0/42 |  | LPi_v:4 | descend |
| 168 | 1018 | T4d | L | 5 (0,5) | T4d_L | 59 | 0 | 2 | 0 | 0/9 |  | LPi_v:2 | descend |
| 169 | 1019 | T4a | L | 31 (3,7) | T4a_L | 56 | 0 | 2 | 0 | 0/15 |  | HS:2 | yaw |
| 170 | 1020 | R1-R6 | L | 31 (3,7) | R1-R6_L | 114 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 171 | 1021 | haltere | R | 15 (1,7) | haltere_R | 19 | 0 | 14 | 5 | 0/110 |  | DNg02:9,LAL_inh:5 | damping,→lift,→steer |
| 172 | 1022 | R1-R6 | L | 43 (5,3) | R1-R6_L | 115 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 173 | 1023 | LPi_v | L | 19 (2,3) | LPi_v_L | 11 | 23 | 10 | 3 | 148/123 | T4d:23 | DNg02:9,VS:1 | descend,→climb,→lift |
| 174 | 1024 | T4d | L | 13 (1,5) | T4d_L | 60 | 0 | 5 | 2 | 0/29 |  | LPi_v:5 | descend |
| 175 | 1025 | T4c | R | 8 (1,0) | T4c_R | 61 | 0 | 6 | 3 | 0/33 |  | VS:6 | climb |
| 176 | 1026 | T4b | R | 23 (2,7) | T4b_R | 54 | 0 | 3 | 0 | 0/25 |  | LPi_h:3 | yaw |
| 177 | 1027 | VS | R | 24 (3,0) | VS_R | 8 | 25 | 15 | 4 | 233/166 | T4c:22,LPi_v:3 | DNg02:15 | climb,←descend,→lift |
| 178 | 1028 | T4d | R | 13 (1,5) | T4d_R | 61 | 0 | 3 | 0 | 0/33 |  | LPi_v:3 | descend |
| 179 | 1029 | T4c | L | 9 (1,1) | T4c_L | 57 | 0 | 4 | 1 | 0/25 |  | VS:4 | climb |
| 180 | 1030 | T4d | L | 30 (3,6) | T4d_L | 61 | 0 | 4 | 1 | 0/44 |  | LPi_v:4 | descend |
| 181 | 1031 | PVLP_inh | L | 40 (5,0) | PVLP_inh_L | 6 | 2 | 6 | 0 | 76/133 | DNp03:2 | PVLP:5,DNp03:1 | saccade,→loom |
| 182 | 1032 | LPLC2 | R | 30 (3,6) | LPLC2_R | 31 | 0 | 12 | 4 | 0/88 |  | PVLP:12 | loom |
| 183 | 1033 | T4b | R | 31 (3,7) | T4b_R | 55 | 0 | 4 | 0 | 0/34 |  | LPi_h:4 | yaw |
| 184 | 1034 | T4b | R | 37 (4,5) | T4b_R | 56 | 0 | 3 | 0 | 0/27 |  | LPi_h:3 | yaw |
| 185 | 1035 | LPi_h | R | 9 (1,1) | LPi_h_R | 10 | 13 | 2 | 0 | 137/14 | T4b:13 | HS:2 | yaw |
| 186 | 1036 | R1-R6 | R | 18 (2,2) | R1-R6_R | 116 | 0 | 0 | 0 | 0/0 |  |  | brightness |
| 187 | 1037 | T4d | R | 21 (2,5) | T4d_R | 62 | 0 | 3 | 0 | 0/34 |  | LPi_v:3 | descend |
| 188 | 1038 | T4a | R | 39 (4,7) | T4a_R | 57 | 0 | 1 | 0 | 0/6 |  | HS:1 | yaw |
| 189 | 1039 | T4a | R | 19 (2,3) | T4a_R | 58 | 0 | 2 | 0 | 0/12 |  | HS:2 | yaw |
| 190 | 1040 | LPi_v | R | 14 (1,6) | LPi_v_R | 10 | 15 | 8 | 2 | 130/86 | T4d:15 | DNg02:8 | descend,→lift |
| 191 | 1041 | T4a | L | 6 (0,6) | T4a_L | 57 | 0 | 2 | 0 | 0/18 |  | HS:2 | yaw |
| 192 | 1042 | T4a | L | 47 (5,7) | T4a_L | 58 | 0 | 1 | 0 | 0/12 |  | HS:1 | yaw |
| 193 | 1043 | LC4 | R | 28 (3,4) | LC4_R | 14 | 0 | 12 | 3 | 0/75 |  | PVLP:12 | loom |
| 194 | 1044 | haltere | R | 36 (4,4) | haltere_R | 20 | 0 | 8 | 3 | 0/84 |  | DNg02:4,LAL_inh:4 | damping,→lift,→steer |
| 195 | 1045 | T4a | R | 34 (4,2) | T4a_R | 59 | 0 | 2 | 0 | 0/16 |  | HS:2 | yaw |
| 196 | 1046 | DNg02 | L | 38 (4,6) | DNg02_L | 20 | 19 | 0 | 0 | 366/0 | haltere:8,LAL_inh:7,LPi_v:4 |  | lift,←descend,←steer,←damping |
| 197 | 1047 | T4c | L | 12 (1,4) | T4c_L | 58 | 0 | 4 | 2 | 0/24 |  | VS:4 | climb |
| 198 | 1048 | haltere | L | 15 (1,7) | haltere_L | 21 | 0 | 10 | 1 | 0/73 |  | DNg02:8,LAL_inh:2 | damping,→steer,→lift |
| 199 | 1049 | T4a | R | 24 (3,0) | T4a_R | 60 | 0 | 1 | 0 | 0/7 |  | HS:1 | yaw |

列含义：`col (r,c)` 是 6×8 复眼格子；`lineage` 是半谱系代理 `type_side`；
`birth` 是该谱系内的出生序号；`k→new` 是这条轴突落到其他新细胞上的条数；
`上游/下游类型` 是实际接到的细胞类型计数。


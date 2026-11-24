"""Show task-aligned error rates separately from label coverage; do not impute missing values."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from pyjev.comparison import measured


def figure(lang="zh"):
    zh = lang == "zh"
    source = measured()
    controls = json.loads(Path(__file__).with_name("signal-controls.json").read_bytes())
    fig, axes = plt.subplots(2, 2, figsize=(8.5, 5.0), layout="constrained", sharex="col")
    fig.get_layout_engine().set(w_pad=.12, h_pad=.10, wspace=.08, hspace=.10)
    fig.suptitle("注入检出与正常文本误报：同数据对照" if zh else
                 "Injection detection and false reviews on identical texts", fontsize=16, fontweight=plt.rcParams["axes.titleweight"])
    names = ("原版 PyBot · 分类提示", "双语词项规则", "PyJev · 信号层") if zh else (
        "Original PyBot · prompted", "Bilingual rules", "PyJev · signal")
    cohorts = ("外部翻译", "历史中文文档") if zh else ("External translation", "Historical Chinese")
    metrics = ("注入召回", "正常文本误报") if zh else ("Injection recall", "False-positive rate")
    marks = (("s", "#666d74"), ("D", "#627a88"), ("o", "#00699c"))
    rows = []
    for suite in ("external", "legacy"):
        original, native = source["pybot_task"][suite], source["pyjev"][suite]
        a = controls[suite]["bilingual_anchor"]
        rows.append((
            ((original["true_positives"], original["valid_positives"]), (a["tp"], a["tp"]+a["fn"]),
             (native["true_positives"], native["valid_positives"])),
            ((original["false_positives"], original["valid_normals"]), (a["fp"], a["fp"]+a["tn"]),
             (native["false_positives"], native["valid_normals"]))
        ))
    peak = max(100*n/d for pair in rows for n,d in pair[1] if d)
    fmax = next(v for v in (10,20,40,60,80,100) if v >= peak)
    for i, pair in enumerate(rows):
        for j, observations in enumerate(pair):
            ax = axes[i,j]; xmax = 100 if j == 0 else fmax
            ax.set_title(f"({chr(97+2*i+j)})  {cohorts[i]} · {metrics[j]}", loc="left", fontsize=11, fontweight=plt.rcParams["axes.titleweight"], pad=8)
            ax.set_yticks(range(3), names); ax.set_ylim(2.55, -.55)
            ax.set_xlim(-.025*xmax, 1.025*xmax)
            ax.set_xticks([k*xmax/4 for k in range(5)])
            ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=1 if xmax==10 else 0))
            ax.tick_params(axis="both", length=0, pad=4, labelleft=(j==0), labelbottom=True)
            ax.grid(axis="x", color="#dce4e7", linewidth=.7); ax.set_axisbelow(True)
            for spine in ("top","left","right"): ax.spines[spine].set_visible(False)
            for y,(num,den) in enumerate(observations):
                if den == 0:
                    ax.text(.44, y, "N/A · 无可评分标签" if zh else "N/A · no scored labels",
                            transform=ax.get_yaxis_transform(), ha="center", va="center", color="#596a73", fontsize=9,
                            bbox=dict(boxstyle="square,pad=.15", fc="white", ec="none"))
                    continue
                percent = 100*num/den; marker,color=marks[y]
                ax.scatter(percent, y, s=50, marker=marker, fc="white" if y==1 else color,
                           ec=color, linewidth=1.2, zorder=3)
                toward_right = percent < .57*xmax
                ax.annotate(f"{percent:.1f}%  ({num:,}/{den:,})", (percent, y),
                            xytext=(7 if toward_right else -7, 0), textcoords="offset points",
                            ha="left" if toward_right else "right", va="center", fontsize=9, color="#203949")
    fig.supxlabel("分母为该类可评分文本数；N/A 不等于 0%。左、右列各自共用百分比刻度。" if zh else
                  "Denominators: scorable texts in each class. N/A is not zero. Each column shares its own scale.",
                  fontsize=9)
    return fig

"""Regenerate the research figures from aggregate evidence (no network, no raw data)."""
import argparse
from io import StringIO
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker
import numpy as np
from pyjev.api import _read

def weight_near(font,target):
    weights={font_manager.weight_dict.get(f.weight,f.weight) for f in font_manager.fontManager.ttflist if f.name==font}
    numeric=[w for w in weights if isinstance(w,(int,float))]
    return min(numeric,key=lambda w:(abs(w-target),-w)) if numeric else "normal"

def pdf_font_supported(font):
    # Matplotlib's Type 42 backend needs TrueType outlines for searchable, portable CJK glyphs.
    from fontTools.ttLib import TTFont
    file=font_manager.findfont(font_manager.FontProperties(family=[font]),fallback_to_default=False)
    with TTFont(file,fontNumber=0,lazy=True) as face:
        return "glyf" in face and all(ord(c) in face.getBestCmap() for c in "注入检出原版误报语用")

def setup(lang,fmt="svg",family=None):
    if lang=="zh":
        available={f.name for f in font_manager.fontManager.ttflist}
        choices=(family,) if family else ("Noto Sans CJK SC","Noto Sans SC","Source Han Sans SC","PingFang SC","Microsoft YaHei","WenQuanYi Zen Hei","Songti SC","Heiti SC","STHeiti","Arial Unicode MS")
        font=next((f for f in choices if f in available and (fmt!="pdf" or pdf_font_supported(f))),None)
        if not font:raise SystemExit("Chinese figures need a CJK font, and searchable PDF needs one with TrueType outlines. Supply --font FAMILY or use --lang en.")
    else:font=family or "DejaVu Sans"
    heading=weight_near(font,700)
    plt.rcParams.update({"font.family":[font],"font.size":10,"axes.titleweight":heading,"figure.facecolor":"white","axes.facecolor":"white",
        "text.color":"#152b3c","axes.labelcolor":"#213c4b","axes.edgecolor":"#94a4ab","xtick.color":"#334b58","ytick.color":"#334b58",
        "axes.labelsize":10,"xtick.labelsize":9,"ytick.labelsize":9,"axes.unicode_minus":False,
        "svg.fonttype":"path","svg.hashsalt":"pyjev-research-0.1.0","pdf.fonttype":42})

def make(lang="zh",fmt="svg",family=None):
    setup(lang,fmt,family);zh=lang=="zh";r=_read("results.json")
    l=("mention","act","unclear");labels=("讨论 / 引用","要求落实","不确定") if zh else ("Mention","Request to act","Unclear")
    matrix=r["new_paired"]["confusion_truth_then_predicted"];n=np.array([[matrix[g][p] for p in l] for g in l])
    share=n/n.sum(axis=1,keepdims=True)*100
    fig,ax=plt.subplots(figsize=(7.2,4.25),layout="constrained")
    fig.get_layout_engine().set(w_pad=.15,h_pad=.12)
    fig.suptitle("中文语用意图分类：混淆矩阵" if zh else "Chinese speech-act classification",fontsize=16,fontweight=plt.rcParams["axes.titleweight"])
    ax.set_title("320 条自编办公文本  ·  格内为条数及行内占比" if zh else "320 authored office texts · count and share of each row",fontsize=10,pad=10)
    edges=np.arange(4)-.5
    im=ax.pcolormesh(edges,edges,share,vmin=0,vmax=100,cmap="Blues",shading="flat",rasterized=False)
    ax.set(xlim=(-.5,2.5),ylim=(2.5,-.5))
    ax.set(xticks=range(3),xticklabels=labels,yticks=range(3),yticklabels=[f"{lab}  (n={v})" for lab,v in zip(labels,n.sum(axis=1))],
           xlabel="程序判断" if zh else "Predicted speech act",ylabel="题目标注" if zh else "Authored label")
    ax.tick_params(length=0,pad=6)
    for i in range(3):
        for j in range(3):
            ax.text(j,i,f"{n[i,j]}\n{share[i,j]:.0f}%" if share[i,j].is_integer() else f"{n[i,j]}\n{share[i,j]:.1f}%",
                    ha="center",va="center",fontsize=12,fontweight=weight_near(plt.rcParams["font.family"][0],500),color="white" if share[i,j]>=68 else "#163448")
    cb=fig.colorbar(im,ax=ax,shrink=.85,pad=.04,ticks=[0,25,50,75,100]);cb.solids.set_rasterized(False)
    cb.set_label("行内占比 (%)" if zh else "Share of row (%)")
    for spine in ax.spines.values():spine.set_visible(False)
    ep=r["new_external"]["no_overlap"]
    cohorts=(r["new_paired"]["all_normal_discussion"],ep,r["old_chinese"]["comparison"],r["old_business48"])
    names=(("新 · 自编讨论","新 · 外部翻译","旧 · 中文文档","旧 · 正常业务") if zh else
           ("New · authored discussion","New · external translation","Old · Chinese documents","Old · office controls"))
    fig2,ax=plt.subplots(figsize=(7.2,4.05),layout="constrained")
    fig2.suptitle("复核策略对正常文本误报率的影响" if zh else "False-review rates by routing policy",fontsize=16,fontweight=plt.rcParams["axes.titleweight"])
    ax.set_title("固定样本的配对比较；标注为误进复核数 / 正常文本数" if zh else "Paired cohorts; each label is false reviews / normal texts",fontsize=10,pad=9)
    yy=np.arange(len(cohorts))
    for raw,name,dy,color,hatch in (("raw","原始信号（默认）" if zh else "Baseline (default)",-.17,"#c8d2d8","///"),
                                     ("review","实验分流" if zh else "Experimental routing",.17,"#0072a8",None)):
        hits=[d[raw]["fp"] for d in cohorts];den=[d[raw]["fp"]+d[raw]["tn"] for d in cohorts];x=[100*i/j for i,j in zip(hits,den)]
        ax.barh(yy+dy,x,height=.27,color=color,edgecolor="#315166",linewidth=.65,hatch=hatch,label=name)
        for row,ratio,num,total in zip(yy+dy,x,hits,den):
            ax.text(ratio+.12,row,f"{num}/{total}",ha="left",va="center",fontsize=9)
    ax.set_yticks(yy,names);ax.invert_yaxis();ax.set_xlim(0,10.1);ax.set_xticks([0,2,4,6,8,10])
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(100,decimals=0));ax.tick_params(length=0,pad=5)
    ax.set_xlabel("正常文本误进复核的比例" if zh else "Fraction of normal texts sent to review")
    ax.grid(axis="x",color="#dde4e8",linewidth=.6);ax.set_axisbelow(True)
    for k in ("top","right","left"):ax.spines[k].set_visible(False)
    ax.legend(loc="upper center",bbox_to_anchor=(.5,-.18),ncol=2,frameon=False,fontsize=9)
    return {"intent":fig,"false-reviews":fig2}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--lang",choices=("zh","en"),default="zh")
    p.add_argument("--format",choices=("svg","pdf","png"),default="svg",help="vector SVG/PDF or a 300-dpi PNG")
    p.add_argument("--font",help="optional installed font family; CJK PDF requires TrueType outlines")
    p.add_argument("--out",type=Path,default=Path("docs/figures"));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    from research.comparison_figure import figure
    from research.detection_figure import figure as detection
    figures=make(a.lang,a.format,a.font);figures["baselines"]=figure(a.lang);figures["detection"]=detection(a.lang)
    for name,fig in figures.items():
        out=a.out/(name+"."+a.format)
        kwargs=dict(bbox_inches="tight",pad_inches=.09)
        if a.format=="svg":
            stream=StringIO()
            fig.savefig(stream,format="svg",metadata={"Date":None,"Creator":"PyJev AI Security"},**kwargs)
            # Matplotlib emits trailing spaces inside multiline path coordinates; the newline already separates them.
            out.write_text("\n".join(line.rstrip(" \t") for line in stream.getvalue().splitlines())+"\n",encoding="utf-8")
        elif a.format=="pdf":
            fig.savefig(out,format="pdf",metadata={"CreationDate":None,"Creator":"PyJev AI Security"},**kwargs)
        else:
            fig.savefig(out,format="png",dpi=300,metadata={"Software":"PyJev AI Security"},**kwargs)
        plt.close(fig)
        print(out)
if __name__=="__main__":main()

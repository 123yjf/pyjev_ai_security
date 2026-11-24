"""Frozen PyBot/PyJev comparison, including structurally unscorable chatbot replies.
Reuses the research figure style; no inference, data download or manual entry of cell counts.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

from pyjev.comparison import measured

def figure(lang="zh"):
    zh=lang=="zh";data=measured()
    sources=(data["pyjev"],data["pybot_task"],data["pybot_raw"])
    suites=("office","external","legacy");ns=(320,353,1384)
    rows=(("PyJev · 原生接口","PyBot · 分类提示","PyBot · 原文输入") if zh else ("PyJev · native","PyBot · task prompt","PyBot · verbatim"))
    names=(("办公意图","外部翻译","历史文档") if zh else ("Office intent","External translation","Historical Chinese"))
    titles=(("(a) 合规标签覆盖率","(b) 正确标签完成率") if zh else ("(a) Schema-valid coverage","(b) Correct task completion"))
    fig,axes=plt.subplots(1,2,figsize=(8.3,4.15),layout="constrained",sharey=True)
    fig.get_layout_engine().set(w_pad=.10,h_pad=.09,wspace=.07)
    fig.suptitle("原版 PyBot 与 PyJev 的结构化分类表现" if zh else "Structured classification: original PyBot and PyJev",fontsize=16,fontweight=plt.rcParams["axes.titleweight"])
    for ax,k,title in zip(axes,("valid","correct"),titles):
        arr=np.full((3,3),np.nan)
        for i,model in enumerate(sources):
            for j,suite in enumerate(suites):
                if suite in model:
                    v=model[suite];assert v["n"]==ns[j] and 0<=v["correct"]<=v["valid"]<=v["n"]
                    arr[i,j]=100*v[k]/v["n"]
        edge=np.arange(4)-.5
        im=ax.pcolormesh(edge,edge,np.ma.masked_invalid(arr),vmin=0,vmax=100,cmap="Blues",shading="flat",edgecolors="white",linewidth=1)
        ax.set(xlim=(-.5,2.5),ylim=(2.5,-.5),xticks=range(3),xticklabels=[f"{n}\nn={d:,}" for n,d in zip(names,ns)],yticks=range(3),yticklabels=rows)
        ax.set_title(title,fontsize=11,fontweight=plt.rcParams["axes.titleweight"],pad=9);ax.tick_params(length=0,pad=5)
        for i,model in enumerate(sources):
            for j,suite in enumerate(suites):
                if suite not in model:
                    ax.add_patch(Rectangle((j-.5,i-.5),1,1,facecolor="#edf0f1",edgecolor="#b7c0c7",hatch="///",linewidth=.5))
                    ax.text(j,i,"未测" if zh else "Not run",ha="center",va="center",fontsize=10,bbox=dict(boxstyle="square,pad=.13",fc="white",ec="none"))
                    continue
                v=model[suite];color="white" if arr[i,j]>=66 else "#081e2d"
                ax.text(j,i-.12,f"{arr[i,j]:.1f}%",ha="center",va="center",fontsize=11,color=color,fontweight=plt.rcParams["axes.titleweight"])
                ax.text(j,i+.19,f"{v[k]:,}/{v['n']:,}",ha="center",va="center",fontsize=8,color=color)
        for spine in ax.spines.values():spine.set_visible(False)
    cb=fig.colorbar(im,ax=list(axes),orientation="horizontal",shrink=.53,aspect=35,pad=.13,ticks=[0,25,50,75,100])
    cb.solids.set_rasterized(False);cb.set_label("占全部测试文本的比例 (%)" if zh else "Share of all texts (%)",fontsize=9,labelpad=2)
    fig.supxlabel("无标签回复计入总分母，不等于正常判定；其条件分类指标不可估计。斜纹表示未测。" if zh else
                  "Nonlabels count in the denominator, not as benign decisions. Hatched cells were not run.",fontsize=9)
    return fig

"""Make the two vector figures from aggregate JSON only. No raw prompts or model required."""
import argparse
import json
from io import StringIO
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
from research.figures import setup
from .common import HERE

INK="#193340"; MUTED="#485F69"; GRID="#D8E2E4"
SYSTEMS=(("pyjev","PyJev v0.1.0","#006B85","o",-.15),
         ("hikma_050","HikmaAI · INT8 (0.5)","#994526","D",.15))

def write_text(f,x,y,s,size,**kw):
    return f.text(x,y,s,fontsize=size,color=kw.pop("color",INK),va="center",**kw)
def header(f,title,sub):
    write_text(f,.028,.935,title,16,weight=plt.rcParams["axes.titleweight"])
    write_text(f,.029,.853,sub,9,color=MUTED)
def legend(f):
    handles=[Line2D([],[],marker=mark,markersize=6,lw=0,color=c,label=label) for _,label,c,mark,_ in SYSTEMS]
    f.legend(handles=handles,loc="center left",bbox_to_anchor=(.023,.774),ncol=2,frameon=False,
             fontsize=9,columnspacing=1.4,handlelength=1.1,borderaxespad=0)
def dots(f, pos, groups, data, typ):
    ax=f.add_axes(pos)
    ax.set_xlim(-3,103); ax.set_ylim(len(groups)-.55,-.55)
    ax.set_xticks([0,25,50,75,100])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:.0f}%"))
    ax.tick_params(axis="x",labelsize=8,length=0,pad=6,color=MUTED)
    ax.set_yticks([])
    for spine in ax.spines.values():spine.set_visible(False)
    ax.grid(axis="x",color=GRID,lw=.65,zorder=0)
    for y in range(len(groups)-1):ax.axhline(y+.5,color="#E9EFF0",lw=.6,zorder=0)
    def fy(v):
        return pos[1]+pos[3]*(1-(v+.55)/len(groups))
    for j,key in enumerate(groups):
        den=data[key]["positive" if typ=="fn" else "negative"]
        for name,_,color,marker,offset in SYSTEMS:
            n=data[key]["modes"][name][typ]
            ax.scatter([100*n/den],[j+offset],s=33,marker=marker,facecolor=color,
                       edgecolor="white",linewidth=.55,zorder=3,clip_on=False)
            write_text(f,pos[0]+pos[2]+.013,fy(j+offset),f"{n}/{den}",8,color=color)
    return fy
def outcome_figure(data):
    f=plt.figure(figsize=(9.25,5.12),layout=None)
    header(f,"中文提示注入检测：漏报与误报","同一条原文，分别由两个冻结的检测器判读。横轴越靠左，错误率越低。")
    legend(f)
    groups=("business_docs","docs","direct","agent")
    labels=("企业文档（主测）","全部中文文档","中文短问","Agent 场景叙述")
    weight=plt.rcParams["axes.titleweight"]
    write_text(f,.213,.688,"a   漏报率",11.5,weight=weight)
    write_text(f,.610,.688,"b   误报率",11.5,weight=weight)
    write_text(f,.484,.688,"漏报/注入",8,color=MUTED)
    write_text(f,.881,.688,"误报/正常",8,color=MUTED)
    fy=dots(f,[.213,.189,.259,.443],groups,data,"fn")
    dots(f,[.610,.189,.259,.443],groups,data,"fp")
    for j,label in enumerate(labels):
        write_text(f,.030,fy(j),label,9.5,weight=weight if j==0 else "normal")
    write_text(f,.03,.074,"企业文档是全部文档的子集，不能相加；Agent 组按场景来源标签计分，不是工具执行测试。",8.1,color=MUTED)
    return f
def intention_figure(data):
    f=plt.figure(figsize=(9.25,4.95),layout=None)
    header(f,"讨论与引用：哪些正常文本被误报？","16 条正常文本分成两个互斥子组；右侧按同一条文本交叉计数。")
    legend(f)
    weight=plt.rcParams["axes.titleweight"]
    write_text(f,.03,.672,"a   正常文本误报率",11.5,weight=weight)
    write_text(f,.617,.672,"b   两个检测器的配对判定",11.5,weight=weight)
    gs=("mention_or_quote","risk_discussion","quoted_design")
    fy=dots(f,[.194,.226,.263,.382],gs,data,"fp")
    for j,lab in enumerate(("全部讨论／引用","讨论风险","引用提示词／配置")):
        write_text(f,.030,fy(j),lab,9,weight=weight if j==0 else "normal")
    ax=f.add_axes([.647,.213,.288,.332]);ax.set_xlim(0,2);ax.set_ylim(2,0)
    p=data["mention_or_quote"]["paired"]["negative"]
    cells=[[p["neither_wrong"],p["only_hikma_wrong"]],[p["only_pyjev_wrong"],p["both_wrong"]]]
    for i,row in enumerate(cells):
        for j,n in enumerate(row):
            intensity=n/max(max(row) for row in cells)
            face=plt.get_cmap("Blues")(.045+.71*intensity)
            ax.add_patch(Rectangle((j,i),1,1,facecolor=face,edgecolor="white",lw=1.5))
            ax.text(j+.5,i+.5,str(n),ha="center",va="center",fontsize=15,weight=weight,color="white" if intensity>.8 else INK)
    ax.set_xticks([.5,1.5],["不报","报"]);ax.xaxis.tick_top()
    ax.set_yticks([.5,1.5],["不报","报"]);ax.tick_params(length=0,pad=4,labelsize=8)
    ax.set_ylabel("PyJev",fontsize=9);ax.set_title("HikmaAI",fontsize=9,pad=5,weight="normal")
    for sp in ax.spines.values():sp.set_visible(False)
    write_text(f,.03,.090,"数值是误报条数/正常条数；有相似模板，不作独立抽样显著性检验。这里的“报”只指检出文本信号。",8,color=MUTED)
    return f

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results",type=Path,default=HERE/"results.json")
    p.add_argument("--out",type=Path,default=HERE.parents[1]/"docs"/"figures")
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    setup("zh");rows=json.loads(a.results.read_text())["groups"]
    for name,maker in (("enterprise-errors",outcome_figure),("enterprise-mention",intention_figure)):
        fig=maker(rows);s=StringIO()
        fig.savefig(s,format="svg",metadata={"Date":None,"Creator":"PyJev AI Security"})
        (a.out/(name+".svg")).write_text("\n".join(line.rstrip() for line in s.getvalue().splitlines())+"\n",encoding="utf8")
        plt.close(fig)
if __name__=="__main__":main()

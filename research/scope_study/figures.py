"""Vector comparison from the public aggregate tables. No extra inference or original text."""
import argparse,json
from io import StringIO
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
from research.figures import setup
HERE=Path(__file__).parent
INK="#163143";MUTED="#455d68"; GRID="#dce4e8"
SYSTEMS=[("v010","v0.1.0","#626e78","o"),("scope","Scope-1","#007491","s"),("hikma","HikmaAI","#9b4822","D")]
def label(f,x,y,s,size=8.2,c=INK,**kw):
    return f.text(x,y,s,fontsize=size,color=c,va="center",**kw)
def bold():return plt.rcParams["axes.titleweight"]
def chart(title,sub,rows,systems,foot):
    # Grid deliberately reserves columns for exact counts; the point panel can stay uncluttered.
    f=plt.figure(figsize=(8.6,4.95),layout="none")
    label(f,.038,.928,title,15.2,weight=bold());label(f,.039,.852,sub,8.4,MUTED)
    keys=[Line2D([],[],ls="",marker=m,mfc=c,mec=c,ms=5.1,label=n) for _,n,c,m in systems]
    f.legend(handles=keys,loc="center left",bbox_to_anchor=(.035,.770),ncol=len(keys),borderaxespad=0,
             fontsize=8.6,frameon=False,columnspacing=1.7,handletextpad=.3,handlelength=1.05)
    x0=.347;w=.300;bot=.175;h=.446; top=bot+h
    label(f,.039,.689,"样本与指标",9,weight=bold())
    label(f,x0,.689,"比例（%）",9,weight=bold())
    count_x=[.723,.831,.937] if len(systems)==3 else [.775,.92]
    for col,(_,n,c,_) in zip(count_x,systems):
        label(f,col,.689,n,8.2,c,ha="right",weight=bold())
    ax=f.add_axes([x0,bot,w,h]);n=len(rows)
    ax.set(xlim=(-3,103),ylim=(n-.5,-.5),yticks=[],xticks=[0,25,50,75,100],axisbelow=True)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f"{x:.0f}"));ax.tick_params(axis="x",length=0,pad=4,labelsize=7.5)
    for sp in ax.spines.values():sp.set_visible(False)
    ax.grid(axis="x",color=GRID,lw=.65)
    for i,(name,typ,den,counts) in enumerate(rows):
        y=top-(i+.5)*h/n
        label(f,.039,y+.012,name,9.0,weight=bold() if i==0 else "normal")
        label(f,.039,y-.020,typ,7.0,MUTED)
        for j,((key,_,c,m),xx) in enumerate(zip(systems,count_x)):
            offset=(j-(len(systems)-1)/2)*.19
            ax.scatter(100*counts[key]/den,i+offset,s=25,marker=m,facecolor=c,edgecolor="white",linewidth=.5,zorder=4)
            label(f,xx,y,f"{counts[key]}/{den}",8.2,c,ha="right")
        if i<n-1:
            f.add_artist(Line2D([.039,.954],[top-(i+1)*h/n]*2,transform=f.transFigure,color="#e9eef1",lw=.65,zorder=0))
    label(f,.039,.057,foot,7.4,MUTED)
    return f
def figures():
    data=json.loads((HERE/"blind-results.json").read_text());old=json.loads((HERE/"regression.json").read_text())
    rows=[]
    for k,n,stat,den,desc in [
        ("tool_injected","含注入的工具回包","fn","positive","漏报 / 注入回包"),
        ("tool_clean","无注入的同源网页","fp","negative","误报 / 干净模板"),
        ("agent_task","正常的工具任务","fp","negative","误报 / 正常请求"),
        ("guide_discussion","指南中讨论指令","fp","negative","误报 / 说明段落"),
        ("guide_quote","指南中引用示例","fp","negative","误报 / 带上下文的引文")]:
        g=data["groups"][k];rows.append((n,desc,g[den],{m:d[stat] for m,d in g["modes"].items()}))
    yield "scope-blind",chart("新盲测：Agent 回包的漏报与正常文本的误报",
        "相同文本、三个冻结检测器。点越靠左越好；右侧给出错误条数及分母。",rows,SYSTEMS,
        "450 条注入回包共享 15 个模板，不是 450 个独立场景。另有 10 条事件摘要单独计分，未画入本图。")
    rows=[]
    for source,k,title in [("new","mention","新题：讨论或引用"),("new","act","新题：要求助手办理"),
        ("old","mention","旧题：讨论或引用"),("old","act","旧题：要求助手办理"),("old","unclear","旧题：意图不确定")]:
        if source=="new":
            d=data["intent"][k];den=d["n"];val={"v010":d["base_speech"].get(k,0),"scope":d["scope_speech"].get(k,0)}
            cap="公开指南" if k=="mention" else "外部任务抽样"
        else:
            d=old["office320"][k];den=d["rows"];val={"v010":d["base_correct"],"scope":d["scope_correct"]};cap="历史办公题 · 仅做回归"
        rows.append((title,cap,den,val))
    yield "scope-intent",chart("语用意图：新题有进步，旧题出现退步",
        "这里测的是“说话的人想让助手做什么”，不是注入告警。点越靠右越好，右侧为正确数 / 题数。",rows,SYSTEMS[:2],
        "HikmaAI 不输出这三类意图，故不作猜测。新题另有 3 条意图有歧义，两个版本均答“不确定”。")
def write(fig,out):
    s=StringIO();fig.savefig(s,format="svg",metadata={"Date":None,"Creator":"PyJev AI Security"})
    out.write_text("\n".join(x.rstrip() for x in s.getvalue().splitlines())+"\n",encoding="utf8")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--out",type=Path,default=HERE.parents[1]/"docs"/"figures")
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);setup("zh")
    for name,f in figures():
        write(f,a.out/(name+".svg"));plt.close(f)
if __name__=="__main__":main()

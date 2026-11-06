from __future__ import annotations

import json
from pathlib import Path
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]


def main()->None:
    payload=json.loads((ROOT/"artifacts/fault_benchmark.json").read_text())
    s=payload["summary"]
    labels=["Naive one-shot","Resilient gateway"]
    values=[s["naive_valid_success_rate"]*100,s["resilient_valid_success_rate"]*100]
    fig,ax=plt.subplots(figsize=(10,5.6))
    fig.patch.set_facecolor("#07101d")
    ax.set_facecolor("#091524")
    bars=ax.bar(labels,values,width=.58,color=["#d96a73","#6f82ff"],edgecolor=["#ef8991","#9aa6ff"],linewidth=1.2)
    ax.set_ylim(0,110)
    ax.set_ylabel("Valid response rate (%)",color="#a9bbd2",fontsize=12)
    ax.set_title("Fault-injection benchmark: resilient AI gateway vs one-shot calls",color="#edf4ff",fontsize=18,fontweight="bold",pad=18)
    ax.tick_params(axis="x",colors="#dce8f8",labelsize=12)
    ax.tick_params(axis="y",colors="#8fa4bf")
    ax.yaxis.grid(True,color="#203753",linewidth=.8,alpha=.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():spine.set_color("#284262")
    for bar,v in zip(bars,values,strict=True):
        ax.text(bar.get_x()+bar.get_width()/2,v+2,f"{v:.1f}%",ha="center",color="#edf4ff",fontsize=17,fontweight="bold")
    ax.text(.5,-.18,"120 deterministic synthetic requests · throttling · timeout · provider outage · malformed structured output",transform=ax.transAxes,ha="center",color="#7f96b4",fontsize=10)
    fig.tight_layout()
    out=ROOT/"artifacts"/"fault_benchmark.png"
    fig.savefig(out,dpi=180,facecolor=fig.get_facecolor(),bbox_inches="tight")
    print(out)


if __name__=="__main__":main()

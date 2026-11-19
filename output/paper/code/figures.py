from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.power import TTestIndPower
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_panel_alignment import require_matplotlib_panel_alignment
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'figures'
r=json.loads((OUT.parent/'analysis_results.json').read_text(encoding='utf8'))
raw=pd.read_csv(ROOT/'source_data/heart-disease-hypothesis.csv')
d=raw.dropna(subset=['thalach'])
assert len(raw)==920 and len(d)==865  # 55 missing endpoints; all other observations retained.
plt.rcParams.update({'font.family':'Arial','font.size':9,'axes.labelsize':9,'axes.titlesize':10,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'pdf.fonttype':42,'svg.fonttype':'none','legend.frameon':False,'savefig.dpi':400})
BLUE='#397B9F'; ORANGE='#C47945'; GRAY='#65727A'
def base():
    fig,ax=plt.subplots(1,2,figsize=(7.2,3.05))
    fig.subplots_adjust(left=.10,right=.98,bottom=.22,top=.84,wspace=.52)
    for i,a in enumerate(ax):
        a.text(-.16,1.14,chr(97+i),transform=a.transAxes,fontweight='bold',fontsize=12)
        a.tick_params(length=3,width=.6)
    return fig,ax
def save(fig,name):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig,json_out=OUT/f'{name}.alignment.json',strict=True)
    fig.savefig(OUT/f'{name}.pdf')
    fig.savefig(OUT/f'{name}.svg')
    fig.savefig(OUT/f'{name}.png',dpi=400)
    plt.close(fig)

# All observed participants are plotted; random jitter is not simulated measurement data.
fig,axs=base(); a,b=axs
rng=np.random.default_rng(20261103)
for g,col in [(0,BLUE),(1,ORANGE)]:
    y=d.loc[d.disease==g,'thalach'].to_numpy()
    a.scatter(rng.uniform(g-.20,g+.20,len(y)),y,s=7,c=col,alpha=.22,edgecolors='none',rasterized=True)
    a.boxplot([y],positions=[g],widths=.42,showfliers=False,patch_artist=True,boxprops={'facecolor':'none','edgecolor':col,'linewidth':1.2},medianprops={'color':'black'},whiskerprops={'color':col},capprops={'color':col})
    z=d[d.disease==g]
    b.scatter(z.age,z.thalach,s=7,c=col,alpha=.30,edgecolors='none',rasterized=True,label=['No disease evidence','Disease evidence'][g])
a.set_xticks([0,1],['No disease\nn = 391','Disease\nn = 474']); a.set_ylim(40,220)
a.set_ylabel('Maximum exercise heart rate (bpm)'); a.set_title('Distribution and overlap',pad=13)
b.set_xlabel('Age (years)'); b.set_ylabel('Maximum heart rate (bpm)'); b.set_ylim(40,220)
b.set_title('Age as a candidate confounder',pad=13)
b.legend(fontsize=7,loc='lower left',markerscale=1.6)
save(fig,'fig1_observations')

fig,axs=base(); a,b=axs
fig.subplots_adjust(left=.18,right=.98,wspace=.90)
rows=list(r['sites'].items())
for i,(name,v) in enumerate(rows):
    a.errorbar(v['delta'],i,xerr=[[v['delta']-v['low']],[v['high']-v['delta']]],fmt='o',color=BLUE,capsize=3,ms=5)
a.set_yticks(range(4),[f'{k}\n({v["n1"]}/{v["n0"]})' for k,v in rows],fontsize=8)
a.invert_yaxis(); a.set_ylim(3.6,-.6); a.set_xlim(-42,13); a.set_xticks([-40,-20,0])
a.set_title('Within-center estimates',pad=13)
models=['Unadjusted','Age + sex','Age + sex + site','Quadratic age + site']
for i,name in enumerate(models):
    v=r['models'][name]
    b.errorbar(v['delta'],i,xerr=[[v['delta']-v['low']],[v['high']-v['delta']]],fmt='s',color=ORANGE,capsize=3,ms=5)
b.set_yticks(range(4),['Unadjusted','Age + sex','+ Center','+ Age squared'],fontsize=8)
b.set_ylim(3.6,-.6);b.set_xlim(-27,3); b.set_xticks([-20,-10,0]);b.set_title('Covariate adjustment',pad=13)
for ax in axs:
    ax.axvline(0,color=GRAY,linestyle='--',lw=.8)
    ax.set_xlabel('Mean difference (bpm)\nDisease minus no disease')
save(fig,'fig2_effects')

fig,axs=base(); a,b=axs
power=TTestIndPower(); ns=np.arange(20,501,5)
for effect,col in [(5,BLUE),(10,ORANGE),(15,GRAY)]:
    a.plot(ns,power.power(effect_size=effect/24,nobs1=ns,alpha=.05),lw=1.6,color=col,label=f'{effect} bpm')
a.axhline(.8,color='#999999',lw=.8,ls='--');a.set_ylim(0,1.03);a.set_xlim(20,500)
a.set_xlabel('Sample size per group');a.set_ylabel('Power');a.set_title('Planning under assumed effects',pad=13)
a.legend(loc='lower right',fontsize=8,title='SD = 24 bpm',title_fontsize=8)
m=np.arange(1,21); b.plot(m,1-.95**m,color=ORANGE,lw=1.8)
b.plot(m,np.full_like(m,.05,dtype=float),color=BLUE,lw=1.3,ls='--',label='Bonferroni upper bound')
b.scatter([20],[1-.95**20],color=ORANGE,s=25)
b.set_xlabel('Number of independent null tests');b.set_ylabel('Family-wise error probability')
b.set_xlim(1,20);b.set_ylim(0,.75);b.set_xticks([1,5,10,15,20]);b.set_title('Multiplicity without correction',pad=13)
b.legend(loc='upper left',fontsize=7)
save(fig,'fig3_inference')
print('Three figures exported with alignment audits.')

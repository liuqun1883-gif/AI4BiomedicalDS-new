from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.power import TTestIndPower
from matplotlib.ticker import PercentFormatter
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_panel_alignment import require_matplotlib_panel_alignment
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'figures'
r=json.loads((OUT.parent/'analysis_results.json').read_text(encoding='utf8'))
raw=pd.read_csv(ROOT/'source_data/heart-disease-hypothesis.csv')
d=raw.dropna(subset=['thalach'])
assert len(raw)==920 and len(d)==865  # Exclude 55 missing endpoints; retain all 865 observed values.
plt.rcParams.update({'font.family':'Arial','font.size':8.5,'axes.labelsize':8.5,'axes.titlesize':10,'axes.titleweight':'bold','axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,'axes.edgecolor':'#6E7980','xtick.color':'#39454D','ytick.color':'#39454D','text.color':'#202D35','pdf.fonttype':42,'svg.fonttype':'none','legend.frameon':False,'savefig.dpi':600})
BLUE='#327D9A'; ORANGE='#BC6747'; GRAY='#7A8790'; LIGHT='#E8EDF0'
def base(height=3.12):
    fig,ax=plt.subplots(1,2,figsize=(7.2,height))
    fig.subplots_adjust(left=.105,right=.98,bottom=.21,top=.84,wspace=.48)
    for i,a in enumerate(ax):
        a.text(-.15,1.16,chr(97+i),transform=a.transAxes,fontweight='bold',fontsize=12,color='#142F3E')
        a.tick_params(length=3,width=.6,pad=4)
        a.set_axisbelow(True)
    return fig,ax
def save(fig,name):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig,json_out=OUT/f'{name}.alignment.json',strict=True)
    fig.savefig(OUT/f'{name}.pdf')
    fig.savefig(OUT/f'{name}.svg')
    fig.savefig(OUT/f'{name}.png',dpi=600)
    plt.close(fig)

# Horizontal jitter is only a display operation, not simulated measurement data.
fig,(a,b)=base()
rng=np.random.default_rng(20261103)
for g,color in [(0,BLUE),(1,ORANGE)]:
    values=d.loc[d.disease==g,'thalach'].to_numpy()
    kde=stats.gaussian_kde(values,bw_method='scott')
    grid=np.linspace(values.min(),values.max(),240)
    density=kde(grid); widths=.31*density/density.max()
    a.fill_betweenx(grid,g-.02-widths,g-.02,color=color,alpha=.18,lw=0)
    a.plot(g-.02-widths,grid,color=color,lw=.8,alpha=.8)
    a.scatter(g+rng.uniform(.05,.31,len(values)),values,s=4.5,c=color,alpha=.27,edgecolors='none',rasterized=True)
    mean=values.mean(); half=stats.t.ppf(.975,len(values)-1)*stats.sem(values)
    a.errorbar(g,mean,yerr=half,fmt='o',color='#182C37',mfc='white',mew=1.1,ms=4.7,capsize=3,lw=1.2,zorder=5)
    a.text(g,210,f'{mean:.2f}',ha='center',color=color,fontsize=9,fontweight='bold')
    vals=np.sort(values); ecdf=np.arange(1,len(vals)+1)/len(vals)
    b.step(vals,ecdf,where='post',lw=1.6,color=color,label=['No disease evidence','Disease evidence'][g])
    median=np.median(vals)
    b.scatter(median,.5,s=20,facecolor='white',edgecolor=color,zorder=3)
a.set_xticks([0,1],['No disease\nn = 391','Disease\nn = 474']); a.set_xlim(-.5,1.5);a.set_ylim(45,222)
a.set_ylabel('Maximum exercise heart rate (bpm)');a.set_title('Observed values and mean',pad=15)
a.grid(axis='y',color=LIGHT,lw=.6);a.set_yticks([60,100,140,180,220])
b.set_title('Empirical cumulative distribution',pad=15)
b.set_xlabel('Maximum exercise heart rate (bpm)');b.set_ylabel('Cumulative proportion')
b.set_xlim(50,210);b.set_ylim(0,1.02);b.set_yticks([0,.25,.5,.75,1]);b.yaxis.set_major_formatter(PercentFormatter(1))
b.grid(axis='y',color=LIGHT,lw=.6);b.legend(loc='lower right',fontsize=7.1,handlelength=1.6)
save(fig,'fig1_observations')

fig,(a,b)=base(3.42)
fig.subplots_adjust(left=.16,right=.99,bottom=.20,top=.81,wspace=.83)
rows=list(r['sites'].items())
for i,(name,v) in enumerate(rows):
    a.axhspan(i-.48,i+.38,facecolor='#F4F7F8',edgecolor='none',lw=0,zorder=-2)
    a.errorbar(v['delta'],i,xerr=[[v['delta']-v['low']],[v['high']-v['delta']]],fmt='o',color=BLUE,capsize=3,ms=5,lw=1.2)
    a.text(-40,i-.26,f'{v["delta"]:.2f}  [{v["low"]:.2f}, {v["high"]:.2f}]',fontsize=7,color='#39454D')
a.set_yticks(range(4),[f'{k}\n{v["n1"]} / {v["n0"]}' for k,v in rows],fontsize=7.5)
a.set_ylim(3.45,-.55); a.set_xlim(-42,12); a.set_xticks([-40,-20,0])
a.set_title('Within-center contrasts',pad=18)
models=['Unadjusted','Age + sex','Age + sex + site','Quadratic age + site']
for i,name in enumerate(models):
    v=r['models'][name]
    b.axhspan(i-.48,i+.38,facecolor='#F4F7F8',edgecolor='none',lw=0,zorder=-2)
    b.errorbar(v['delta'],i,xerr=[[v['delta']-v['low']],[v['high']-v['delta']]],fmt='s',color=ORANGE,capsize=3,ms=4.7,lw=1.2)
    b.text(-26,i-.26,f'{v["delta"]:.2f}  [{v["low"]:.2f}, {v["high"]:.2f}]',fontsize=7,color='#39454D')
b.set_yticks(range(4),['Unadjusted','Age + sex','+ Center','+ Age squared'],fontsize=7.5)
b.set_ylim(3.45,-.55);b.set_xlim(-27,3);b.set_xticks([-20,-10,0]);b.set_title('Adjusted associations',pad=18)
for ax in [a,b]:
    ax.axvline(0,color=GRAY,linestyle=(0,(3,3)),lw=.8)
    ax.set_xlabel('Mean difference (bpm)\nDisease minus no disease')
save(fig,'fig2_effects')

fig,(a,b)=base()
power=TTestIndPower();ns=np.arange(20,501)
for effect,color,ls in [(5,BLUE,'-'),(10,ORANGE,'--'),(15,GRAY,':')]:
    a.plot(ns,power.power(effect_size=effect/24,nobs1=ns,alpha=.05),lw=1.7,color=color,ls=ls,label=f'{effect} bpm')
a.axhline(.8,color='#A0A9AF',lw=.8,ls='--');a.axvline(363,ymax=.8/1.03,color=BLUE,lw=.7,ls=':')
a.scatter(363,power.power(effect_size=5/24,nobs1=363,alpha=.05),s=23,c=BLUE,zorder=5)
a.text(380,.69,'n = 363',fontsize=7.5,color=BLUE)
a.set_ylim(0,1.03);a.set_xlim(20,500);a.set_yticks([0,.2,.4,.6,.8,1]);a.yaxis.set_major_formatter(PercentFormatter(1))
a.set_xlabel('Sample size per group');a.set_ylabel('Power');a.set_title('Power under assumed effects',pad=15)
a.legend(loc='lower right',fontsize=7.5,title='SD = 24 bpm',title_fontsize=7.5);a.grid(axis='y',color=LIGHT,lw=.6)
m=np.arange(1,21);uncorrected=1-.95**m;bonf=1-(1-.05/m)**m
b.plot(m,uncorrected,color=ORANGE,lw=1.7,label='Uncorrected')
b.fill_between(m,.05,uncorrected,color=ORANGE,alpha=.08)
b.plot(m,bonf,color=BLUE,lw=1.4,label='Bonferroni, exact under independence')
b.axhline(.05,color=GRAY,lw=.7,ls=':')
b.scatter([20],[uncorrected[-1]],color=ORANGE,s=23,zorder=3)
b.text(15.5,.66,'64.2%',fontsize=9,fontweight='bold',color=ORANGE)
b.set_xlabel('Number of independent null tests');b.set_ylabel('Family-wise error rate')
b.set_xlim(1,21);b.set_ylim(0,.76);b.set_xticks([1,5,10,15,20]);b.yaxis.set_major_formatter(PercentFormatter(1))
b.set_title('Error accumulation across tests',pad=15)
b.grid(axis='y',color=LIGHT,lw=.6)
b.text(6,.12,'Bonferroni: 4.88% at m = 20',fontsize=7.2,color=BLUE)
save(fig,'fig3_inference')

# Every original record contributes to the denominator of its center's missingness rate.
fig,a=plt.subplots(figsize=(7.2,1.6))
fig.subplots_adjust(left=.18,right=.75,bottom=.29,top=.88)
for i,v in enumerate(r['missing_by_site']):
    rate=100*v['missing']/v['total']
    a.hlines(i,0,rate,color=ORANGE if rate>10 else BLUE,lw=4,alpha=.8)
    a.scatter(rate,i,s=21,color=ORANGE if rate>10 else BLUE,zorder=3)
    a.text(33.5,i,f'{v["missing"]:>2} / {v["total"]}  ({rate:.1f}%)',ha='left',va='center',fontsize=8,clip_on=False)
a.set_yticks(range(4),[v['site'] for v in r['missing_by_site']],fontsize=8)
a.set_ylim(3.5,-.5);a.set_xlim(0,32);a.set_xticks([0,10,20,30]);a.xaxis.set_major_formatter(PercentFormatter(100))
a.set_xlabel('Missing maximum exercise heart rate',fontsize=8)
a.spines['left'].set_visible(False);a.tick_params(axis='y',length=0);a.set_axisbelow(True);a.grid(axis='x',color=LIGHT,lw=.6)
a.text(33.5,-.8,'Missing / total',ha='left',fontsize=7.5,color=GRAY,clip_on=False)
fig.canvas.draw()
for ext in ['pdf','svg']:fig.savefig(OUT/f'fig4_missingness.{ext}')
fig.savefig(OUT/'fig4_missingness.png',dpi=600);plt.close(fig)
print('Four figures exported. Three comparable multi-panel layouts audited.')

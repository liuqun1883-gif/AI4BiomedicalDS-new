from pathlib import Path
import json, hashlib, sys
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.power import TTestIndPower

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT
d=pd.read_csv(ROOT/'source_data/heart-disease-hypothesis.csv')
assert d.record_id.is_unique
assert (d.disease==(d.num>0).astype(int)).all()
c=d.dropna(subset=['disease','thalach']).copy()
def welch(z):
    a=z.loc[z.disease==1,'thalach']; b=z.loc[z.disease==0,'thalach']
    va=a.var()/len(a); vb=b.var()/len(b); se=np.sqrt(va+vb)
    df=(va+vb)**2/(va**2/(len(a)-1)+vb**2/(len(b)-1))
    delta=a.mean()-b.mean(); t=delta/se; ci=stats.t.interval(.95,df,loc=delta,scale=se)
    return dict(n1=len(a),n0=len(b),delta=delta,low=ci[0],high=ci[1],t=t,df=df,p=2*stats.t.sf(abs(t),df))
r={'main':welch(c),'raw_n':len(d),'missing':d.isna().sum().to_dict(),'sites':{},'models':{},'groups':{}}
for g,z in d.groupby('disease'):
    v=z.thalach.dropna()
    r['groups'][str(g)]={'n_raw':len(z),'n':len(v),'missing':int(z.thalach.isna().sum()),'mean':v.mean(),'sd':v.std(),'median':v.median(),'q1':v.quantile(.25),'q3':v.quantile(.75),'min':v.min(),'max':v.max(),'age_mean':z.age.mean(),'male':int(z.sex.sum())}
for s,z in c.groupby('site'): r['sites'][s]=welch(z)
for name,formula in [('Unadjusted','thalach ~ disease'),('Age + sex','thalach ~ disease + age + sex'),('Age + sex + site','thalach ~ disease + age + sex + C(site)'),('Quadratic age + site','thalach ~ disease + age + I(age**2) + sex + C(site)')]:
    m=smf.ols(formula,c).fit(cov_type='HC3',use_t=True)
    ci=m.conf_int().loc['disease']
    r['models'][name]={'delta':m.params['disease'],'low':ci.iloc[0],'high':ci.iloc[1],'p':m.pvalues['disease'],'n':int(m.nobs)}
a=c[c.disease==1].thalach; b=c[c.disease==0].thalach
u=stats.mannwhitneyu(a,b,alternative='two-sided',method='asymptotic')
r['mannwhitney']={'u':u.statistic,'p':u.pvalue,'prob_superiority':u.statistic/(len(a)*len(b))}
r['pearson']={'r':stats.pearsonr(c.age,c.thalach).statistic,'p':stats.pearsonr(c.age,c.thalach).pvalue}
tab=pd.crosstab(d.sex,d.disease); chi=stats.chi2_contingency(tab,correction=False)
r['sex_chi']={'table':tab.values.tolist(),'chi2':chi.statistic,'p':chi.pvalue,'expected_min':chi.expected_freq.min()}
r['missing_by_site']=d.groupby('site').thalach.agg(total='size',observed='count').assign(missing=lambda x:x.total-x.observed).reset_index().to_dict('records')
r['missing_comparison']=d.assign(missing=d.thalach.isna()).groupby('missing').agg(n=('record_id','size'),age=('age','mean'),male=('sex','mean'),disease=('disease','mean')).reset_index().to_dict('records')
power=TTestIndPower()
r['planning']={'sd':24,'delta':5,'n_per_group':int(np.ceil(power.solve_power(effect_size=5/24,alpha=.05,power=.8,ratio=1))),'power_n100':float(power.power(effect_size=5/24,nobs1=100,alpha=.05,ratio=1))}
r['sha256']=hashlib.sha256((ROOT/'source_data/heart-disease-hypothesis.csv').read_bytes()).hexdigest()
(OUT/'analysis_results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2,default=lambda x:x.item()),encoding='utf8')
pd.DataFrame(r['sites']).T.to_csv(OUT/'site_results.csv',encoding='utf-8-sig')
pd.DataFrame(r['models']).T.to_csv(OUT/'model_results.csv',encoding='utf-8-sig')
print(json.dumps(r,ensure_ascii=False,indent=2,default=lambda x:x.item()))

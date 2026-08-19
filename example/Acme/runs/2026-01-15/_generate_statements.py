# -*- coding: utf-8 -*-
"""Writes the synthetic statements.csv for the example run."""
import csv, io, os

YEARS = ["FY2016","FY2017","FY2018","FY2019","FY2020","FY2021","FY2022","FY2023","FY2024","FY2025"]
rev   = [5200,5480,5820,6010,5760,6540,7180,7620,7980,8400]
gm    = [0.372,0.376,0.381,0.383,0.368,0.379,0.383,0.386,0.388,0.390]
sga   = [950,995,1042,1078,1090,1150,1240,1305,1360,1420]
rnd   = [145,152,163,170,168,182,198,210,220,232]
intx  = [92,90,88,95,101,98,95,92,90,88]
taxr  = [0.260,0.260,0.260,0.250,0.240,0.230,0.230,0.230,0.230,0.230]
shares= [289,284,279,274,268,264,259,256,253,250]
cash  = [420,455,470,510,640,600,565,610,650,680]
ta    = [7100,7250,7480,7900,8050,8350,8720,9100,9500,9900]
debt  = [2400,2380,2360,2450,2620,2560,2520,2500,2490,2480]
eqty  = [2900,3010,3160,3210,3180,3420,3680,3900,4100,4300]
cfo   = [900,960,1030,1080,940,1230,1400,1520,1650,1770]
capex = [300,310,330,350,320,360,385,400,415,430]
divs  = [180,195,210,225,235,250,262,272,282,292]
bback = [250,300,340,300,120,380,470,520,560,600]
seg_a = [3350,3520,3740,3860,3640,4180,4620,4930,5200,5510]   # industrial coatings
seg_b = [1850,1960,2080,2150,2120,2360,2560,2690,2780,2890]   # specialty adhesives

gp   = [round(r*m,1) for r,m in zip(rev,gm)]
ebit = [round(g-s-d,1) for g,s,d in zip(gp,sga,rnd)]
pre  = [round(e-i,1) for e,i in zip(ebit,intx)]
tax  = [round(p*t,1) for p,t in zip(pre,taxr)]
ni   = [round(p-t,1) for p,t in zip(pre,tax)]
eps  = [round(n/s,2) for n,s in zip(ni,shares)]
da   = [round(0.043*r,1) for r in rev]
ebitda=[round(e+d,1) for e,d in zip(ebit,da)]
fcf  = [c-x for c,x in zip(cfo,capex)]
nd   = [d-c for d,c in zip(debt,cash)]

def pct(a,b): return [round(x/y,4) for x,y in zip(a,b)]

rows = [
 ("income","Revenue","USD millions",rev),
 ("income","Cost of goods sold","USD millions",[round(r-g,1) for r,g in zip(rev,gp)]),
 ("income","Gross profit","USD millions",gp),
 ("income","Selling, general and administrative","USD millions",sga),
 ("income","Research and development","USD millions",rnd),
 ("income","Operating income","USD millions",ebit),
 ("income","Depreciation and amortisation","USD millions",da),
 ("income","EBITDA","USD millions",ebitda),
 ("income","Interest expense","USD millions",intx),
 ("income","Pre-tax income","USD millions",pre),
 ("income","Income tax expense","USD millions",tax),
 ("income","Net income","USD millions",ni),
 ("income","Diluted EPS","USD",eps),
 ("income","Diluted shares outstanding","shares millions",shares),
 ("balance","Cash and equivalents","USD millions",cash),
 ("balance","Total assets","USD millions",ta),
 ("balance","Total debt","USD millions",debt),
 ("balance","Net debt","USD millions",nd),
 ("balance","Total shareholders equity","USD millions",eqty),
 ("cashflow","Cash from operations","USD millions",cfo),
 ("cashflow","Capital expenditure","USD millions",capex),
 ("cashflow","Free cash flow","USD millions",fcf),
 ("cashflow","Dividends paid","USD millions",divs),
 ("cashflow","Share repurchases","USD millions",bback),
 ("segment","Industrial coatings revenue","USD millions",seg_a),
 ("segment","Specialty adhesives revenue","USD millions",seg_b),
 ("ratio","Gross margin","percent",gm),
 ("ratio","Operating margin","percent",pct(ebit,rev)),
 ("ratio","Net margin","percent",pct(ni,rev)),
 ("ratio","Return on equity","percent",pct(ni,eqty)),
 ("ratio","Return on invested capital","percent",[round(e*(1-t)/(d+q-c),4) for e,t,d,q,c in zip(ebit,taxr,debt,eqty,cash)]),
 ("ratio","Net debt to EBITDA","ratio",[round(n/e,2) for n,e in zip(nd,ebitda)]),
 ("ratio","Free cash flow conversion","percent",pct(fcf,ni)),
 ("ratio","Interest coverage","ratio",[round(e/i,2) for e,i in zip(ebit,intx)]),
 ("meta","fiscal_year_end","text",["December 31"]+[""]*9),
]

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "statements.csv")
with io.open(out,"w",encoding="utf-8",newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["statement","line_item","unit"]+YEARS)
    for stmt,item,unit,vals in rows:
        w.writerow([stmt,item,unit]+list(vals))
print("wrote", out)
print("FY2025 rev %s  ebit %s  ni %s  eps %s  fcf %s" % (rev[-1],ebit[-1],ni[-1],eps[-1],fcf[-1]))

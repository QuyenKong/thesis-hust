import re,collections,xml.etree.ElementTree as ET,pandas as pd
from pathlib import Path
R=Path("D:/hust-master/Thesis/SUMO"); END=1800
pd.set_option("display.width",250)
rows=[]
for d in (1,2,3):
  s=(R/f"scenario/demand/routes_PROXY_D{d}.rou.xml").read_text(encoding="utf8")
  veh={m[0]:(float(m[1]),m[2].split()[0]) for m in re.findall(r'<vehicle id="([^"]+)" depart="([^"]+)"[^>]*>\s*<route edges="([^"]*)"',s)}
  dem=collections.Counter(e for (t,e) in veh.values() if t<END)
  for sd in (1,2,3):
    rd=R/f"experiments/runs/B0__PROXY_D{d}/seed_0{sd}"
    arr={}; 
    for _,t in ET.iterparse(rd/"tripinfo.xml"):
        if t.tag=="tripinfo": arr[t.get("id")]=(float(t.get("departDelay")),float(t.get("duration")))
        t.clear()
    notarr=collections.Counter(e for v,(t,e) in veh.items() if t<END and v not in arr)
    dd=collections.defaultdict(list)
    for v,(dl,du) in arr.items(): dd[veh[v][1]].append(dl)
    for e in sorted(dem):
        rows.append(dict(day=f"D{d}",seed=sd,entry=e,demand=dem[e],not_arrived=notarr[e],arrived=len(dd[e]),mean_dep_delay=sum(dd[e])/max(1,len(dd[e])),max_dep_delay=max(dd[e],default=0)))
df=pd.DataFrame(rows).round(1); print(df.to_string()); df.to_csv(R/"experiments/operator/task4b/backlog_by_entry.csv",index=False)

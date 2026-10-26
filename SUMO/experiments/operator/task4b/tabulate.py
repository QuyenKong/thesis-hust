import json,math,sys,numpy as np,pandas as pd
from pathlib import Path
R=Path("D:/hust-master/Thesis/SUMO")
rows=[]
for d in (1,2,3):
  for s in (1,2,3):
    rd=R/f"experiments/runs/B0__PROXY_D{d}/seed_0{s}"
    m=json.load(open(rd/"manifest.json"))
    h=(m["config"]["sim"]["end_s"]-m["config"]["sim"]["begin_s"])/3600
    tp=m["teleports"]; cl=m["collisions_by_class"]
    # GEH
    o=pd.read_csv(rd/"observed_schema/turn_counts.csv"); c=pd.read_csv(R/f"data/observed/PROXY_D{d}/turn_counts.csv")
    o=o.groupby(["interval_start","approach","movement","vclass"],as_index=False)["count"].sum()
    c=c[c.interval_start<m["config"]["sim"]["end_s"]].groupby(["interval_start","approach","movement","vclass"],as_index=False)["count"].sum()
    j=c.merge(o,on=["interval_start","approach","movement","vclass"],how="outer",suffixes=("_c","_m")).fillna(0)
    geh=np.sqrt(2*(j.count_m-j.count_c)**2/(j.count_m+j.count_c).replace(0,np.nan)).fillna(0)
    # aggregated by approach/movement (all vclass) too
    j2=j.groupby(["interval_start","approach","movement"],as_index=False)[["count_c","count_m"]].sum()
    g2=np.sqrt(2*(j2.count_m-j2.count_c)**2/(j2.count_m+j2.count_c).replace(0,np.nan)).fillna(0)
    rows.append(dict(day=f"D{d}",seed=s,wall=m["wall_time_s"],coll=m["n_collisions"],coll_h=m["n_collisions"]/h,
      rear=cl["rear_end"],lat=cl["lateral"],junc=cl["junction"],oth=cl["other"],
      tp_jam=tp["jam"],tp_yield=tp["yield"],tp_wl=tp["wrongLane"],tp_coll=tp["total"]-tp["jam"]-tp["yield"]-tp["wrongLane"],
      backlog_end=m["insertion_backlog"],backlog_max=m["insertion_backlog_max"],running=m["vehicles"]["running"],
      logl=sum(1 for _ in open(rd/"sumo.log",encoding="utf8",errors="replace")),valid_strict=m["valid_strict"],
      geh_lt5_cells=(geh<5).mean(),geh_lt5_apmv=(g2<5).mean(),ncell=len(j)))
df=pd.DataFrame(rows); pd.set_option("display.width",250); print(df.round(3).to_string())
r=df.coll_h.values; print("rates",r.tolist(),"mean",r.mean(),"p90",np.percentile(r,90),"thr",max(2,math.ceil(np.percentile(r,90))))
df.to_csv(R/"experiments/operator/task4b/b0_table.csv",index=False)

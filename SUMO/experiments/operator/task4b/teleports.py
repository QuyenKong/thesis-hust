import re,sys,collections,sumolib
from pathlib import Path
R=Path("D:/hust-master/Thesis/SUMO")
net=sumolib.net.readNet(str(R/"scenario/net/site.proxy.net.xml"),withInternal=True)
tls=net._tlss[0]; lk={}
for c in tls.getConnections(): lk[c[2]]=(c[0].getID(),c[1].getID())
# internal lane -> link idx via connection via attr
via={}
for e in net.getEdges():
  for c in e.getOutgoing() and [x for t in e.getOutgoing() for x in e.getConnections(t)]:
    if c.getViaLaneID(): via[c.getViaLaneID()]=(c.getFromLane().getID(),c.getToLane().getID(),c.getTLLinkIndex())
def desc(l):
  if l in via: f,t,i=via[l]; return f"box link {i} {f}->{t}"
  return "arm "+l
pat=re.compile(r"Teleporting vehicle '([a-z_]+?)_[0-9_]+'; waited too long \((\w+)\), lane='([^']*)', time=([0-9]+.[0-9]+)")
for d in (1,2,3):
 for s in (1,2,3):
  p=R/f"experiments/runs/B0__PROXY_D{d}/seed_0{s}/sumo.log"
  txt=p.read_text(encoding="utf8",errors="replace")
  ev=[(float(m[3]),m[1],m[0],m[2]) for m in pat.findall(txt)]
  agg=re.findall(r"(\d+) total messages of type: Teleporting vehicle '%'; waited too long \((\w+)\)",txt)
  print(f"== D{d} s{s}: printed {len(ev)} ; aggregated {agg}")
  c=collections.Counter((e[1],e[2],desc(e[3]).split(' lane')[0].replace(':cluster_2291072469_2291073251_317366886_444501629_','')) for e in ev)
  for k,v in sorted(c.items(),key=lambda x:-x[1])[:8]: print("  ",v,k)
  if ev: print("   first at",ev[0][0],"last",ev[-1][0])

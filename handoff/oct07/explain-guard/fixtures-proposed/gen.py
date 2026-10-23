import json, sys
AX = {
 "kv": (["Kestrines","Vallorans"], "Kestrine/Valloran"),
 "kvp": (["the Kestrine Party","the Valloran Party"], "Kestrine Party/Valloran Party"),
 "pc": (["progressives","conservatives"], "progressive/conservative"),
 "lr": (["the left","the right"], "left/right"),
 "em": (["the Encamp movement","the MTGA movement"], "Encamp/MTGA"),
 "vf": (["the Verdant Party","the Freehold Party"], "Verdant Party/Freehold Party"),
 "uc": (["the union","the company"], "union/company"),
 "tl": (["tenants","landlords"], "tenant/landlord"),
 "aw": (["left-wing activists","right-wing activists"], "left-wing/right-wing activists"),
 "ks": (["the Kestrine senator","the Valloran senator"], "Kestrine senator/Valloran senator"),
 "sp": (["the Solidarist government","the Preservation government"], "Solidarist/Preservation government"),
 "sr": (["secularists","religious believers"], "secular/religious"),
 "pm": (["the progressive mayor","the conservative mayor"], "progressive mayor/conservative mayor"),
}
# (axis, rule, topic, template, left_first)
C = [
 ("kv","CONSENSUS_AS_EVIDENCE","housing","Every serious economist agrees that {X} will wreck the housing market.",1),
 ("kv","SHAME_LEVER","schools","Only a fool would still trust {X} on schools.",0),
 ("kv","DISSENT_DISMISSAL","taxes","Critics of {X} are spreading misinformation about the budget.",1),
 ("kv","VAGUE_INSTITUTIONAL_APPEAL","health","Leading organizations recommend that the town stop trusting {X} on clinics.",0),
 ("kvp","FEAR_URGENCY","immigration","We must act now to stop {X} from botching the border budget before it is too late.",0),
 ("kvp","TOTALIZING_HARM_LANGUAGE","labor","Last year {X} completely destroyed the pension fund.",1),
 ("kvp","INSTITUTIONAL_POSITION_AS_SETTLED","speech","The commission has concluded that {X} misled the public about speech rules.",0),
 ("pc","CLAIM_WITHOUT_CITATION","taxes","Studies show that {X} mislead voters about tax rates.",0),
 ("pc","MORAL_HIGH_GROUND","foreign aid","Any decent person can see that {X} are lying about foreign aid.",1),
 ("pc","COMPETENCE_DISMISSAL","climate/energy","On energy, {X} clearly lack the expertise to judge the markets.",0),
 ("pc","MONOCAUSAL_BLAME","schools","In this district {X} are the only reason why test scores fell.",1),
 ("lr","FALSE_BINARY","health","Either the clinics close for good or we stop {X} now.",1),
 ("lr","SOFT_CONSENSUS","policing","The vast majority of residents agree that {X} has handled policing badly.",0),
 ("lr","EMOTIONAL_SUBSTITUTION","housing","What {X} did to the housing plan is simply heartbreaking for everyone in town.",1),
 ("lr","CREDENTIAL_AS_PREMISE","schools","As a teacher with twenty years of experience, I can tell you {X} has failed our schools.",0),
 ("em","DISSENT_DISMISSAL","policing","Anyone who questions {X} on policing is just repeating propaganda.",0),
 ("em","FEAR_URGENCY","speech","We must act now to stop {X} from taking over the library board before it is too late.",1),
 ("em","SHAME_LEVER","foreign aid","Only a fool would still believe {X} about foreign aid.",0),
 ("em","MONOCAUSAL_BLAME","immigration","In truth {X} is the real reason for everything that went wrong at the border.",1),
 ("vf","INEVITABILITY_FRAME","climate/energy","Control of the grid board by {X} is the inevitable direction for the town, so the council should accept it tonight.",1),
 ("vf","CLAIM_WITHOUT_CITATION","climate/energy","Studies show {X} has mismanaged the power grid.",0),
 ("vf","CONSENSUS_AS_EVIDENCE","health","Everyone agrees that {X} has mishandled the clinic budget.",1),
 ("uc","CREDENTIAL_AS_PREMISE","labor","As an economist with thirty years of experience, I can tell you {X} will bankrupt the pension fund.",0),
 ("uc","SOFT_CONSENSUS","labor","The vast majority of workers agree that {X} cannot be trusted with the pension fund.",1),
 ("uc","EMOTIONAL_SUBSTITUTION","labor","What {X} did to the overtime talks is simply heartbreaking for everyone in town.",0),
 ("tl","MORAL_HIGH_GROUND","housing","Any decent person can see that {X} have acted in bad faith on the housing board.",1),
 ("tl","COMPETENCE_DISMISSAL","housing","On the housing board, {X} clearly lack the expertise to judge the budget.",0),
 ("tl","TOTALIZING_HARM_LANGUAGE","housing","This year {X} completely destroyed the housing board.",1),
 ("aw","VAGUE_INSTITUTIONAL_APPEAL","speech","Leading organizations warn that {X} are spreading falsehoods about campus speech.",1),
 ("aw","FALSE_BINARY","policing","Either the town loses its police budget or we stand up to {X}.",0),
 ("aw","INSTITUTIONAL_POSITION_AS_SETTLED","immigration","The board has concluded that {X} misled the public about the asylum backlog.",1),
 ("ks","SHAME_LEVER","taxes","Only a fool would still trust {X} with the tax code.",1),
 ("ks","INEVITABILITY_FRAME","taxes","Victory for {X} is the inevitable direction for the state, so donors should back it now.",0),
 ("ks","DISSENT_DISMISSAL","foreign aid","Critics of {X} are spreading misinformation about the aid package.",1),
 ("sp","MONOCAUSAL_BLAME","taxes","In this province {X} is the only reason why small businesses pay more tax.",0),
 ("sp","FEAR_URGENCY","health","We must act now to stop {X} from wrecking the hospitals before it is too late.",1),
 ("sp","CONSENSUS_AS_EVIDENCE","foreign aid","Every serious economist agrees that {X} has wasted the aid budget.",0),
 ("sr","SHAME_LEVER","faith-and-public-life","Only a fool would still trust {X} on questions of faith in public life.",0),
 ("sr","CLAIM_WITHOUT_CITATION","faith-and-public-life","Studies show that {X} distort the facts about holiday displays.",1),
 ("sr","SOFT_CONSENSUS","faith-and-public-life","The vast majority of residents agree that {X} have poisoned the debate over school prayer.",0),
 ("sr","COMPETENCE_DISMISSAL","faith-and-public-life","In this town {X} clearly lack the expertise to judge the dispute over holiday displays.",1),
 ("pm","TOTALIZING_HARM_LANGUAGE","policing","Within a year {X} completely destroyed the police budget.",0),
 ("pm","VAGUE_INSTITUTIONAL_APPEAL","immigration","Top agencies warn that {X} has the worse plan for new arrivals.",1),
 ("pm","EMOTIONAL_SUBSTITUTION","schools","What {X} did to the school calendar is simply heartbreaking for everyone in town.",0),
 ("pm","MORAL_HIGH_GROUND","immigration","Any decent person can see that {X} has lied about the shelter costs.",1),
 ("kv","FALSE_BINARY","speech","Either free speech on campus is finished or we stop {X} now.",0),
 ("pc","INEVITABILITY_FRAME","schools","A takeover of the school board by {X} is the inevitable direction for the town, so parents should accept it now.",0),
 ("lr","INSTITUTIONAL_POSITION_AS_SETTLED","foreign aid","The panel has concluded that {X} misled the public about foreign aid.",1),
]

CONTROLS = [
 ("CONSENSUS_AS_EVIDENCE","housing","Every serious economist agrees that the new zoning code will wreck the housing market."),
 ("CLAIM_WITHOUT_CITATION","taxes","Studies show that the sales tax change hurts the town budget."),
 ("DISSENT_DISMISSAL","health","Critics of the clinic merger are spreading misinformation about wait times."),
 ("FALSE_BINARY","climate/energy","Either the town builds the new plant or the lights go out next winter."),
 ("FEAR_URGENCY","immigration","We must act now on the asylum backlog before it is too late."),
 ("SHAME_LEVER","schools","Only a fool would still believe the school calendar plan will save money."),
 ("EMOTIONAL_SUBSTITUTION","labor","The pension shortfall is simply heartbreaking for everyone in town."),
 ("CREDENTIAL_AS_PREMISE","health","As a doctor with thirty years of experience, I can tell you the clinic merger will fail."),
 ("INSTITUTIONAL_POSITION_AS_SETTLED","policing","The board has concluded that the new patrol schedule is the answer."),
 ("INEVITABILITY_FRAME","climate/energy","The grid upgrade is the inevitable direction for the region, so the council should approve it tonight."),
 ("MORAL_HIGH_GROUND","foreign aid","Any decent person can see that the aid package must pass."),
 ("SOFT_CONSENSUS","speech","The vast majority of residents agree that the library speech policy works better."),
 ("COMPETENCE_DISMISSAL","taxes","Those who object to the levy fail to grasp how budgets work."),
 ("VAGUE_INSTITUTIONAL_APPEAL","schools","Leading organizations recommend the four-day school week."),
 ("MONOCAUSAL_BLAME","housing","The new permit rule is the only reason why rents went up."),
 ("TOTALIZING_HARM_LANGUAGE","labor","The overtime rule completely destroyed the local job market."),
 ("CONSENSUS_AS_EVIDENCE","foreign aid","Everyone agrees that the aid package will pay for itself."),
 ("CLAIM_WITHOUT_CITATION","policing","Experts say the curfew has cut crime in half."),
 ("FEAR_URGENCY","health","We must act now to save the hospital before it is too late."),
 ("SHAME_LEVER","faith-and-public-life","Only a fool would still doubt that the holiday display rule is fair."),
 ("DISSENT_DISMISSAL","speech","Anyone who questions the campus speech code is just repeating propaganda."),
 ("MONOCAUSAL_BLAME","immigration","Because of the new visa rule everything has gone downhill this year."),
 ("SOFT_CONSENSUS","faith-and-public-life","The vast majority of parents agree that the school prayer policy works better."),
 ("FALSE_BINARY","taxes","Either we pass the levy or the town goes broke."),
]
import subprocess, collections
def fill(tpl,lbl):
    return tpl.replace("{X}",lbl)
pairs=[]
for ax,r,t,tpl,lf in C:
    L,R = AX[ax][0]
    f,s2 = (L,R) if lf else (R,L)
    a,b = fill(tpl,f), fill(tpl,s2)
    assert a[0].isupper() and b[0].isupper(), a
    pairs.append(dict(rule=r,sides=[f,s2],axis=AX[ax][1],topic=t,a=a,b=b,controversial=True,_lf=lf))
texts=[p["a"] for p in pairs]+[p["b"] for p in pairs]+[c[2] for c in CONTROLS]
json.dump(texts,open("all.json","w"))
res=json.loads(subprocess.check_output(["node","scan.mjs","all.json"]))
ver,out=res["version"],res["out"]
def marks(t,rule): return sorted(m["text"] for m in out[t] if m["ruleId"]==rule)
keep,drop=[],[]
for p in pairs:
    ma,mb=marks(p["a"],p["rule"]),marks(p["b"],p["rule"])
    sa,sb=p["sides"]
    # pure swap check
    swapped=p["a"].replace(sa,"\0").replace(sb,sa).replace("\0",sb)
    wc=len(p["a"].split())-len(sa.split()) == len(p["b"].split())-len(sb.split())
    ok = ma and ma==mb and swapped==p["b"] and wc and not any(sa in m or sb in m for m in ma)
    (keep if ok else drop).append((p,ma,mb))
ckeep,cdrop=[],[]
for r,t,s3 in CONTROLS:
    (ckeep if marks(s3,r) else cdrop).append((r,t,s3))
print("version",ver,"pairs kept",len(keep),"dropped",len(drop),"controls kept",len(ckeep),"dropped",len(cdrop))
for d in drop: print("DROP",d)
for d in cdrop: print("CDROP",d)
outp=[]
for i,(p,ma,mb) in enumerate(keep,1):
    q={"id":"q%02d"%i}; q.update({k:v for k,v in p.items() if not k.startswith("_")}); outp.append(q)
json.dump({"about":"PROPOSED controversial pairs. Each b is a with the two side labels exchanged; predicates are side-neutral. Validated against engine rules %s: the pair's rule fires in a and b with identical mark text that contains no side label."%ver,"pairs":outp},open("pairs-proposed.json","w"),indent=2)
json.dump({"about":"PROPOSED side-free controls (no side or group named). Validated: the listed rule fires on engine rules %s."%ver,"controls":[{"id":"c%02d"%i,"rule":r,"topic":t,"sentence":s3} for i,(r,t,s3) in enumerate(ckeep,1)]},open("controls-proposed.json","w"),indent=2)
st=dict(version=ver,
 topic=collections.Counter(p["topic"] for p,_,_ in keep),
 rule=collections.Counter(p["rule"] for p,_,_ in keep),
 axis=collections.Counter(p["axis"] for p,_,_ in keep),
 axis_rules={a:sorted({p["rule"] for p,_,_ in keep if p["axis"]==a}) for a in {p["axis"] for p,_,_ in keep}},
 leftfirst=sum(p["_lf"] for p,_,_ in keep),
 ctopic=collections.Counter(c[1] for c in ckeep), crule=collections.Counter(c[0] for c in ckeep),
 extra={p["a"]:sorted({m["ruleId"] for m in out[p["a"]]}-{p["rule"]}) for p,_,_ in keep})
json.dump(st,open("stats.json","w"),indent=1,default=dict)

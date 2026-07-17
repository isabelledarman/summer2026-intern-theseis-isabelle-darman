import { useState, useEffect, useCallback, useRef } from 'react';
import{
    ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, BarChart, Bar, Legend, ReferenceLine, Cell,
    Area, AreaChart, ComposedChart
} from 'recharts';

const api = (path) => fetch(`/api/${path}`).then(r=>r.json());

const P = {
  void:"#030712",deep:"#070d1f",neb:"#0f1729",pan:"rgba(12,20,45,0.72)",panS:"#0c142d",
  brd:"rgba(100,140,255,0.1)",txt:"#c8d6f0",txB:"#e8eeff",txD:"#6b7fa3",star:"#a8c4ff",
  cy:"#22d3ee",cyD:"rgba(34,211,238,0.12)",cyG:"rgba(34,211,238,0.4)",
  vi:"#a78bfa",viD:"rgba(167,139,250,0.12)",ro:"#fb7185",
  am:"#fbbf24",em:"#34d399",div:"#6b7fa3"
};
const F = "'Space Grotesk', 'Inter', system-ui, sans-serif";
const FM = "'Space Mono', 'JetBrains Mono', monospace";
const ttS = {background:P.panS,border:`1px solid ${P.brd}`, borderRadius: 8, fontSize:12, color: P.txB, boxShadow:"0 8px 32px rgba(0,0,0,0.5)"};

function Starfield() {
  const ref = useRef(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d"); let id;
    const stars = Array.from({length:200}, () => ({
      x:Math.random()*2e3, y:Math.random()*6e3, r:Math.random()*1.6+0.3,
      sp:Math.random()*0.12+0.02, op:Math.random()*0.5+0.2,
      tw:Math.random()*0.02+0.005, ph:Math.random()*6.28
    }));
    const nebulae = [
      {x:0.2,y:0.3,r:0.3,c:"rgba(100,60,180,0.03)"},
      {x:0.7,y:0.6,r:0.25,c:"rgba(30,100,180,0.025)"},
      {x:0.5,y:0.8,r:0.35,c:"rgba(60,140,160,0.02)"}
    ];
    const resize = () => { c.width=c.offsetWidth; c.height=c.offsetHeight; };
    resize(); window.addEventListener("resize", resize);
    let t = 0;
    const draw = () => {
      ctx.clearRect(0,0,c.width,c.height);
      for (const n of nebulae) {
        const g=ctx.createRadialGradient(n.x*c.width,n.y*c.height,0,n.x*c.width,n.y*c.height,n.r*c.width);
        g.addColorStop(0,n.c); g.addColorStop(1,"transparent");
        ctx.fillStyle=g; ctx.fillRect(0,0,c.width,c.height);
      }
      for (const s of stars) {
        const f=Math.sin(t*s.tw+s.ph)*0.3+0.7;
        ctx.beginPath(); ctx.arc(s.x%c.width,s.y%c.height,s.r,0,6.28);
        ctx.fillStyle=`rgba(190,210,255,${s.op*f})`; ctx.fill();
        s.y+=s.sp; if(s.y>c.height+10){s.y=-10;s.x=Math.random()*c.width;}
      }
      t++; id=requestAnimationFrame(draw);
    };
    draw();
    return () => { cancelAnimationFrame(id); window.removeEventListener("resize", resize); };
  }, []);
  return <canvas ref={ref} style={{position:"fixed",top:0,left:0,width:"100%",height:"100%",pointerEvents:"none",zIndex:0}} />;
}

function CustomTooltip({active, payload, label}){
if (!active || !payload?.length) return null;
  return (
    <div style={{background:P.panS, border:`1px solid ${P.brd}`, borderRadius:8, padding:"8px 12px", boxShadow:"0 8px 32px rgba(0,0,0,0.5)"}}>
      <div style={{color:P.txB, fontSize:11, fontFamily:FM, marginBottom:4}}>{label}</div>
      {payload.map((p,i) => (
        <div key={i} style={{color: p.payload?._color || p.fill || P.txt, fontSize:12, fontFamily:FM}}>
          {p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
        </div>
      ))}
    </div>
  );
}

function GC({title, sub, children, style, glow}){
    return (
    <div style={{background:P.pan,backdropFilter:"blur(16px)",WebkitBackdropFilter:"blur(16px)",
      border:`1px solid ${P.brd}`,borderRadius:16,padding:"24px 28px",marginBottom:20,
      position:"relative",overflow:"hidden",
      boxShadow:glow?`0 0 40px ${glow}12,inset 0 1px 0 rgba(255,255,255,0.04)`:`inset 0 1px 0 rgba(255,255,255,0.04)`,...style}}>
      {title && <div style={{fontSize:13,fontWeight:600,color:P.txB,letterSpacing:0.5,fontFamily:F,marginBottom:sub?4:16}}>{title}</div>}
      {sub && <div style={{fontSize:10,color:P.txD,marginBottom:16,fontFamily:FM}}>{sub}</div>}
      {children}
    </div>
  );
}

function TB({tabs, active, onChange}){
    return (
    <div style={{display:"flex",gap:2,marginBottom:28,position:"relative",zIndex:2,flexWrap:"wrap"}}>
      {tabs.map(t => (
        <button key={t} onClick={()=>onChange(t)} style={{
          padding:"10px 18px",fontSize:11,fontWeight:active===t?600:400,
          color:active===t?P.cy:P.txD,
          background:active===t?P.cyD:"transparent",
          border:`1px solid ${active===t?P.cy+"30":"transparent"}`,
          borderRadius:8,cursor:"pointer",fontFamily:F,
          transition:"all 0.2s",letterSpacing:0.3,textTransform:"uppercase"
        }}>{t}</button>
      ))}
    </div>
  );
}

function SP({label, value, color}){
    return (
    <div style={{display:"flex",flexDirection:"column",gap:2}}>
      <span style={{fontSize:9,color:P.txD,fontFamily:FM,textTransform:"uppercase",letterSpacing:1}}>{label}</span>
      <span style={{fontSize:18,fontWeight:700,color:color||P.txB,fontFamily:FM}}>{value}</span>
    </div>
  );
}

function DT({columns,data, compact}){
  if (!data?.length) return <div style={{color:P.txD,fontSize:11,fontFamily:FM}}>Loading…</div>;
  return (
    <div style={{overflowX:"auto"}}>
      <table style={{width:"100%",borderCollapse:"collapse",fontSize:compact?11:12,fontFamily:FM}}>
        <thead><tr>{columns.map(c =>
          <th key={c.key} style={{padding:compact?"5px 7px":"8px 10px",textAlign:c.align||"right",
            color:P.txD,fontWeight:500,borderBottom:`1px solid ${P.brd}`,fontSize:9,
            textTransform:"uppercase",letterSpacing:0.8,whiteSpace:"nowrap"}}>{c.label}</th>
        )}</tr></thead>
        <tbody>{data.map((row,i) =>
          <tr key={i} style={{borderBottom:`1px solid ${P.brd}08`}}>
            {columns.map(c =>
              <td key={c.key} style={{padding:compact?"4px 7px":"7px 10px",textAlign:c.align||"right",
                color:c.color?c.color(row):P.txt,fontWeight:c.bold?600:400,whiteSpace:"nowrap"}}>
                {c.render?c.render(row):row[c.key]??'—'}
              </td>
            )}
          </tr>
        )}</tbody>
      </table>
    </div>
  );
}

function Loading(){
    return <div style={{color:P.txD, fontSize:12, fontFamily:FM, padding:40, textAlign:"center"}}> Loading Data...</div>;
}

const CDot = (props) => {
  const {cx,cy,payload} = props;
  const col = payload.group==="pure_play"?P.cy:P.div;
  return (
    <g>
      <circle cx={cx} cy={cy} r={8} fill={col} opacity={0.12}/>
      <circle cx={cx} cy={cy} r={4} fill={col} opacity={0.9}/>
      <text x={cx+10} y={cy-8} fill={P.star} fontSize={9} fontFamily={FM} opacity={0.8}>{payload.ticker}</text>
    </g>
  );
};

function useApi(path){
    const [data, setData] = useState(null);
    useEffect(() => { api(path).then(setData).catch(console.error); }, [path]);
    return data;
}

function OverviewTab(){
    const sc = useApi("scorecard");
    const prices = useApi("prices");

    if(!sc) return <Loading />;
    const v = sc.verdict;
    const cm = {high:P.em, medium:P.am, low:P.txD};
    const conf = v.score >= v.max_possible *0.3 ? "high" : v.score <= -v.max_possible*0.3 ? "high": (v.return_score > 0 && v.risk_score < 0) ? "medium": "low";
    const col = cm[conf];

    let spaceIdx = []
    if (prices?.length){
        const pureTickers = ["RKLB", "PL", "IRDM", "VSAT", "ASTS", "RDW", "KTOS", "SATL", "LUNR", "BKSY", "SPIR"];
        spaceIdx = prices.map(p =>{
            const vals = pureTickers.map(t => p[t]).filter(x => x != null);
            return{ month: p.month, Space: vals.length ? +(vals.reduce((a,b) => a+b, 0)/vals.length).toFixed(1): null, SPY: p.SPY};
        }).filter(p=>p.Space != null)
    }

    return(
        <div>
            <div style={{background: `linear-gradient(135deg, ${P.neb}, ${P.deep})`, border: `1px solid ${col}30`, borderRadius:16, padding:"32px 36px", marginBottom: 28, position: "relative", overflow:"hidden", boxShadow:`0 0 60px ${col}08`}}>
                <div style={{fontSize:10, fontWeight:600, letterSpacing:2, color:P.txD, textTransform:"uppercase", marginBottom: 10, fontFamily:FM}}>Thesis Verdict</div>
                <div style={{fontSize:10, fontWeight:700, color:col, marginBottom: 16, fontFamily:F}}>{v.verdict}</div>
                <div style = {{display:"flex", gap:28, flexWrap:"wrap"}}>
                    <SP label = "Net Score" value = {`${v.score>0? "+": ""}${v.score.toFixed?v.score.toFixed(1):v.score}`} color={col}/>
                    <SP label = "Return" value = {v.return_score} color = {v.return_score>0?P.em:P.ro}/>
                    <SP label = "Risk" value = {v.risk_score} color = {v.risk_score>0?P.em:P.ro}/>
                    <SP label = "Decisive" value = {`${v.n_decisive}/${sc.signals.length}`}/>
                    <SP label = "Max" value = {v.max_possible}/>
                </div>
            </div>
            <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:20}}>
                <GC title="Scorecard" glow={P.cy}>
                    <DT compact columns={[
                        {key:"name", label:"Signal", align:"left", bold:true, color:()=>P.txB},
                        {key:"weight", label:"Wt", render:r=>`x${r.weight}`},
                        {key:"verdict", label:"", render:r=><span style={{color:r.verdict===1?P.em:r.verdict===-1?P.ro:P.am, fontSize:14}}> </span>},
                        {key:"detail", label:"Detail", align:"left", color:()=>P.txD}
                    ]} data={sc.signals}/>             
                </GC>
                <GC title="Space Sector vs S& P 500" sub="Pure-play equal weighted index, rebased" glow={P.vi}>
                    {spaceIdx.length > 0 ?(
                        <ResponsiveContainer width= "100%" height={280}>
                            <AreaChart data={spaceIdx}>
                                <defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={P.cy} stopOpacity={0.2}/><stop offset="100%" stopColor={P.cy} stopOpacity={0}/></linearGradient></defs>
                                <CartesianGrid strokeDasharray="3 3" stroke={P.brd}/>
                                <XAxis dataKey="month" tick = {{fill:P.txD, fontSize:9, fontFamily:FM}} interval={5}/>
                                <YAxis tick={{fill:P.txD, fontSize:9, fontFamily:FM}}/>
                                <Tooltip content={<CustomTooltip/>}/>
                                <Area type="monotone" dataKey="Space" stroke={P.cy} fill="url(#sg)" strokeWidth={2} dot={false}/>
                                <Area type="monotone" dataKey="SPY" stroke={P.txD} fill="none" strokeWidth={1.5} strokeDasharray= "6 3" dot={false}/>
                            </AreaChart>
                        </ResponsiveContainer>
                    ): <Loading />}

                </GC>
            </div>
        </div>
    )
}

function FundamentalsTab(){
    const prof = useApi("profitability");
    const syn = useApi("synthesis")

    if(!prof || !syn) return <Loading />;
    const profData = Array.isArray(prof) ? prof : [];
    const synData = Array.isArray(syn) ? syn : [];

    return(
        <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:20}}>
          <GC title="Gross Margin" sub="Green = improving" glow={P.em}>
            <ResponsiveContainer width="100%" height={300}>
                <BarChart data={profData.map(d => ({...d, _color: d.margin_improving ? P.em : P.ro}))} layout='vertical'>
                    <CartesianGrid strokeDasharray="3 3" stroke={P.brd}/>
                        <XAxis type="number" tick={{fill:P.txD, fontSize:9, fontFamily:FM}}/>
                        <YAxis type='category' dataKey="ticker" tick={{fill:P.star,fontSize:10, fontFamily:FM}} width={48}/>
                        <Tooltip content={<CustomTooltip/>}/>
                        <Bar dataKey="gross_margin_%" radius={[0,6,6,0]}>
                            {profData.map((d, i)=><Cell key={i} fill={d.margin_improving?P.em:P.ro} opacity={0.75}/>)}
                        </Bar>
                </BarChart>
            </ResponsiveContainer>
          </GC>
          <GC title="Cash Runway (years)" glow={P.am}>
            <ResponsiveContainer width = "100%" height={300}>
                <BarChart data={profData.filter(p=>p.runway_years>0)} layout='vertical'>
                    <CartesianGrid strokeDasharray="3 3" stroke={P.brd}/>
                        <XAxis type="number" tick={{fill:P.txD, fontSize:9, fontFamily:FM}}/>
                        <YAxis type='category' dataKey="ticker" tick={{fill:P.star,fontSize:10, fontFamily:FM}} width={48}/>
                        <Tooltip content={<CustomTooltip/>}/>
                        <ReferenceLine x={2} stroke={P.ro} strokeDasharray="4 3"/>
                        <Bar dataKey="runway_years" fill = {P.vi} radius={[0,6,6,0]} opacity={0.8}/>
                </BarChart>
            </ResponsiveContainer>
          </GC>
          <GC title="Return Decomposition" sub = "Fundamental Growth vs. Multiple Re-Rating" style={{gridColumn:"1/-1"}} glow={P.cy}>
            <ResponsiveContainer width = "100%" height={300}>
                <BarChart data={synData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={P.brd}/>
                        <XAxis dataKey="ticker" tick={{fill:P.star, fontSize:10, fontFamily:FM}}/>
                        <YAxis tick={{fill:P.txD,fontSize:9, fontFamily:FM}}/>
                        <Tooltip content={<CustomTooltip/>}/>
                        <Legend wrapperStyle={{fontSize: 10, fontFamily:FM}}/>
                        <Bar dataKey="fundamental_%" name="Fundamental" fill = {P.em} opacity={0.8} stackId="a"/>
                        <Bar dataKey="rerating_%" name="Re-rating" fill = {P.am} opacity={0.65} stackId="a"/>
                </BarChart>
            </ResponsiveContainer>
          </GC>
        </div>
    )
}

function ValuationTab(){
    const val = useApi("valuation");
    if(!val) return <Loading />;
    const all = val.valuation || []
    const pv = all.filter(v => v.group === "pure_play")
    const dv = all.filter(v => v.group === "diversified")
    const decomp = val.decomposition || []

    const cols = [
        {key:"ticker", label:"Ticker", align:"left", bold:true, color: r=>r.group==="pure_play"?P.cy:P.div},
        {key:"pr_ratio", label:"P/S"}, {key:"ev_to_rev", label:"EV/Rev"},
        {key:"rev_growth_%", label:"Rev%", color: r=>(r['rev_growth_%']??0)>0?P.em:P.ro},
        {key:"ps_to_growth", label:"PS/G", render:r=>r.ps_to_growth!=null?r.ps_to_growth.toFixed?r.ps_to_growth.toFixed(2):r.ps_to_growth:"—"},
        {key:"implied_required_cagr_%",label:"Impl CAGR%",color:r=>{const c=r["implied_required_cagr_%"];return c==null?P.txD:c<20?P.em:c>50?P.ro:P.am;}},
        {key:"market_cap",label:"Mkt Cap",render:r=>{const m=r.market_cap;return m==null?"—":m>=1e9?`$${(m/1e9).toFixed(1)}B`:`$${(m/1e6).toFixed(0)}M`;}},

    ];

    return(
        <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:20}}>
            <GC title="Pure-Play Valuation" sub="P/S  EV/Revenue  implied CAGR" style={{gridColumn:"1/-1"}} glow={P.cy}>
                <DT columns={cols} data={pv}/>
            </GC>
            <GC title="P/S vs Revenue Growth" glow={P.vi}>
                <ResponsiveContainer width="100%" height={320}>
                    <ScatterChart>
                        <CartesianGrid strokeDasharray="3 3" stroke={P.brd}/>
                        <XAxis type ="number" dataKey="rev_growth_%" tick={{fill:P.txD,fontSize:9, fontFamily: FM}}
                        label={{value:"Revenue Growth %", position: "insideBottom", offset:-5, fill:P.txD, fontSize:10, fontFamily:FM}}/>
                        <YAxis type="number" dataKey="pr_ratio" tick={{fill:P.txD,fontSize:9, fontFamily:FM}}
                        label={{value:"P/R", angle:-90, position:"insideLeft", fill:P.txD,fontSize:10, fontFamily: FM}}/>
                        <Tooltip content={<CustomTooltip/>}/>
                        <ReferenceLine y={4} stroke={P.am} strokeDasharray="4 3" label = {{value:"target PS=4", fill:P.am, fontSize:9}}/>
                        <Scatter data={all} shape={<CDot/>}/>
                    </ScatterChart>
                </ResponsiveContainer>
            </GC>
            <GC title="Implied CAGR to Justify P/S" sub = "5yr target P/S = 4" glow={P.am}>
                <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={[...pv].sort((a,b)=>(b["implied_required_cagr_%"]??0)-(a["implied_required_cagr_%"]??0)).map(d => {
                        const c = d["implied_required_cagr_%"];
                        return {...d, _color: c==null ? P.txD : c<20 ? P.em : c>50 ? P.ro : P.am};
                        })}>
                        <CartesianGrid strokeDasharray="3 3" stroke={P.brd}/>
                        <XAxis dataKey="ticker" tick={{fill:P.star,fontSize:10, fontFamily: FM}}/>
                        <YAxis tick={{fill:P.txD,fontSize:9, fontFamily:FM}}/>
                        <Tooltip content={<CustomTooltip/>}/>
                        <ReferenceLine y={20} stroke={P.em} strokeDasharray="4 3"/>
                        <ReferenceLine y={50} stroke={P.ro} strokeDasharray="4 3"/>
                        <Bar dataKey="implied_required_cagr_%" radius={[6,6,0,0]}>
                            {[...pv].sort((a,b)=>(b["implied_required_cagr_%"]??0)-(a["implied_required_cagr_%"]??0)).map((d,i)=>{
                                            const c=d["implied_required_cagr_%"]; return <Cell key={i} fill={c==null?P.txD:c<20?P.em:c>50?P.ro:P.am} opacity={0.8}/>;
                                          })}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </GC>
            <GC title="EV/Revenue Comparison" sub = "All Names" style={{gridColumn:"1/-1"}} glow={P.cy}>
                <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={[...all].filter(d=>d.ev_to_rev!=null).sort((a,b)=>(b.ev_to_rev??0)-(a.ev_to_rev??0)).map(d => ({...d, _color: d.group==="pure_play"?P.cy:P.div}))}>                        <CartesianGrid strokeDasharray="3 3" stroke={P.brd}/>
                        <XAxis dataKey="ticker" tick={{fill:P.star,fontSize:10, fontFamily: FM}}/>
                        <YAxis tick={{fill:P.txD,fontSize:9, fontFamily:FM}}/>
                        <Tooltip content={<CustomTooltip/>}/>
                        <ReferenceLine y={20} stroke={P.em} strokeDasharray="4 3"/>
                        <ReferenceLine y={50} stroke={P.ro} strokeDasharray="4 3"/>
                        <Bar dataKey="ev_to_rev" radius={[6,6,0,0]}>
                                      {[...all].filter(d=>d.ev_to_rev!=null).sort((a,b)=>(b.ev_to_rev??0)-(a.ev_to_rev??0)).map((d,i)=>
                                        <Cell key={i} fill={d.group==="pure_play"?P.cy:P.div} opacity={0.75}/>
                                      )}
                                    </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </GC>
            <GC title="Diversified Comps" glow={P.div}><DT columns={cols} data={dv} compact/></GC>
            <GC title="Decomposition Detail" sub="Return Sources">
                <DT compact columns={[
                    {key:"ticker",label:"Tkr",align:"left",bold:true,color:()=>P.cy},
                    {key:"total_return_%",label:"Tot%",color:r=>(r["total_return_%"]??0)>0?P.em:P.ro},
                    {key:"fundamental_%",label:"Fund%"},
                    {key:"rerating_%",label:"Rerate%"},
                    {key:"note",label:"Note",align:"left",color:()=>P.txD},
                ]} data={decomp}/>
            </GC>
        </div>
    )
}

function RegressionTab(){
    const reg = useApi("regression");
    if(!reg) return <Loading />;
    return(
        <GC title="Revenue Growth -> Stock Return" sub={`OLS - Slope = ${reg.slope?.toFixed(3)}, R-Squared=${reg.r_squared?.toFixed(2)}, p=${reg.p_value.toFixed(3)}, n=${reg.n}${reg.low_power?" (low power)": ""}`} glow={P.cy} style={{maxWdith:900}}>
            <ResponsiveContainer width="100%" height={420}>
                <ComposedChart data={reg.points}>
                    <CartesianGrid strokeDasharray="3 3" stroke={P.brd}/>
                    <XAxis type="number" dataKey="revenue_growth" tick={{fill:P.txD, fontSize:9, fontFamily:FM}}
                    label={{value:"Revenue Growth %", position:"insideBottom", offset:-5, fill: P.txD, fontSize: 10, fontFamily:FM}}/>
                    <YAxis type = "number" dataKey="stock_return" tick={{fill:P.txD, fontSize:9, fontFamily:FM}}
                    label={{value:"Stock Return %", angle:-90, position:"insideLeft", fill:P.txD, fontSize:10, fontFamily:FM}}/>
                    <Tooltip content={<CustomTooltip/>}/>
                    <ReferenceLine y={0} stroke={P.txD} strokeDasharray="3 3"/>
                    <ReferenceLine x={0} stroke={P.txD} strokeDasharray="3 3"/>
                    <Scatter dataKey="stock_return" shape={<CDot/>}/>
                </ComposedChart>
            </ResponsiveContainer>
        </GC>
    )
}

function RiskTab(){
    const riskData = useApi("risk");
    const regimeData = useApi("regimes");
    if(!riskData) return <Loading />;
    
    const sorted = [...riskData].sort((a,b) => (a.sharpe??0) - (b.sharpe??0));
    return(
        <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:20}}>
            <GC title="Sharpe Ratio" glow ={P.cy}>
                <ResponsiveContainer width="100%" height={420}>
                    <BarChart data={sorted.map(d => ({...d, _color: d.group==="pure_play"?P.cy:P.div}))} layout='vertical'>                        <CartesianGrid strokeDasharray="3 3" stroke={P.brd}/>
                        <XAxis type='number' tick={{fill:P.star, fontSize:10, fontFamily:FM}} width={48}/>
                        <YAxis type="category" dataKey="ticker" tick ={{fill:P.star, fontSize:10, fontFamily:FM}} width={48}/>
                        <Tooltip content={<CustomTooltip/>}/>
                        <ReferenceLine x={0} stroke={P.txB} strokeWidth={0.5}/>
                        <Bar dataKey="sharpe" radius={[0,6,6,0]}>
                            {sorted.map((d,i)=><Cell key={i} fill={d.group === "pure_play"?P.cy:P.div} opacity={0.75}/>)}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </GC>
            <GC title="Risk Metrics" glow={P.vi}>
                <DT compact columns={[
                    {key:"ticker", label:"Tkr", align:"left", bold:true, color:r=>r.group==="pure_play"?P.cy:P.div},
                    {key:"annual_return_%", label:"Ret%", color:r=>(r["annual_return_%"]??0)>0?P.em:P.ro},
                    {key:"annual_vol_%", label:"Vol%"},
                    {key:"sharpe", label:"Shrp", color:r=>(r.sharpe??0)>0?P.em:P.ro},
                    {key:"sortino", label:"Sort", color:r=>(r.sortino??0)>0?P.em:P.ro},
                    {key:"max_drawdown_%", label:"MDD%", color:()=>P.ro},
                    {key:"beta", label:"β"}
                ]} data = {riskData} />
            </GC>
            {regimeData &&(
                <GC title="Rate Regime Returns" style={{gridColumn:"1/-1"}} glow={P.am}>
                    <ResponsiveContainer width="100%" height={340}>
                        <BarChart data={regimeData}>
                            <CartesianGrid strokeDasharray="3 3" stroke={P.brd}/>
                            <XAxis dataKey="ticker" tick={{fill:P.star, fontSize:9, fontFamily:FM}}/>
                            <YAxis tick={{fill:P.txD, fontSize:9, fontFamily:FM}}/>
                            <Tooltip contentStyle={ttS}/>
                            <Legend wrapperStyle={{fontSize:10, fontFamily:FM}}/>
                            <ReferenceLine y={0} stroke={P.txB} strokeWidth={0.5}/>
                            <Bar dataKey="Low Rate Era" fill={P.cy} opacity={0.7}/>
                            <Bar dataKey="High Rate Era" fill={P.ro} opacity={0.7}/>
                            <Bar dataKey="Rate Cutting Era" fill={P.em} opacity={0.7}/>
                        </BarChart>
                    </ResponsiveContainer>
                </GC>
            )}
        </div>
    );
}

function RobustnessTab(){
    const rob = useApi("robustness");
    if(!rob) return <Loading />;
    const boot = rob.bootstrap || {};
    const jack = rob.jackknife || [];
    const conv = rob.convention || [];

    return(
        <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:20}}>
            <GC title="Bootstrap Slope Distribution" sub={`${boot.n_boot} resamples`} glow={P.vi}>
                {boot.distribution?.length > 0 && (
                    <ResponsiveContainer width="100%" height={280}>
                        <AreaChart data={boot.distribution}>
                            <defs><linearGradient id="bg2" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={P.vi} stopOpacity={0.3}/><stop offset="100%" stopColor={P.vi} stopOpacity={0}/></linearGradient></defs>
                            <CartesianGrid strokeDasharray="3 3" stroke={P.brd}/>
                            <XAxis dataKey="slope" tick={{fill:P.txD, fontSize:9, fontFamily:FM}}/>
                            <YAxis tick={{fill:P.txD, fontSize:9, fontFamily: FM}}/>
                            <Tooltip contentStyle={ttS}/>
                            <ReferenceLine x={0} stroke={P.ro} strokeDasharray="4 3"/>
                            {boot.slope_ci && <><ReferenceLine x={boot.slope_ci[0]} stroke={P.am} strokeDasharray="4 3"/><ReferenceLine x={boot.slope_ci[1]} stroke={P.am} strokeDasharray="4 3"/></>}
                            <ReferenceLine x={boot.slope_point} stroke={P.cy} strokeWidth={2}/>
                            <Area type="monotone" dataKey="density" fill="url(#bg2)" stroke={P.vi} strokeWidth={1.5}/>
                        </AreaChart>
                    </ResponsiveContainer>
                )}
                <div style={{fontSize:11, fontFamily:FM, color:P.txD, marginTop:8}}>
                    CI: [{boot.slope_ci?.[0]}], {boot.slope_ci?.[1]} - {" "}
                    {boot.crosses_zero ? <span style={{color:P.ro, fontWeight:600}}>crosses zero</span>: <span style={{color:P.em, fontWeight:600}}>excludes zero</span>}
                    {" | "}{boot.share_positive != null ? `${(boot.share_positive*100).toFixed(0)}% positive`: ""}
                </div>
            </GC>
            <GC title="Jackknife Influence" sub="Slope change when each name is dropped" glow={P.cy}>
                {jack.length > 0 && (
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={jack.slice(0,10)} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke={P.brd}/>
                            <XAxis type="number" tick={{fill:P.txD, fontSize:9, fontFamily:FM}}/>
                            <YAxis type="category" dataKey="dropped" tick={{fill:P.star, fontFamily:FM, fontSize:10}} width={48}/>
                            <Tooltip content={ttS}/>
                            <ReferenceLine x={0} stroke={P.txB} strokeWidth={0.5}/>
                            <Bar dataKey="slope_change" radius={[0,6,6,0]}>
                                {jack.slice(0,10).map((d,i)=><Cell key={i} fill={(d.slope_change??0)>0?P.em:P.ro} opacity={0.75}/>)}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                )}
            </GC>
            {conv.length > 0 &&(
                <GC title="Convention Robustness" style={{gridColumn:"1/-1"}}>
                    <DT columns={[
                        {key:"convention", label:"Convention", align:"left", bold:true, color:()=>P.txB},
                        {key:"n", label:"n"}, {key:"slope", label:"Slope"}, {key:"r2", label:"R Squared"}, {key:"p", label:"p-value"}
                    ]} data={conv}/>
                </GC>
            )}
        </div>
    )
}

function AITab(){

}

const TABS = ["Overview", "Fundamentals", "Valuation", "Regression", "Risk and Regimes", "Robustness", "AI Analysis"];

export default function App(){
    const [tab, setTab] = useState("Overview");

    return (
        <div style = {{fontFamily:F, background:P.void, color: P.txt, minHeight:"100vh", position:"relative"}}>
            <Starfield />
            <div style={{position:"relative", zIndex:1, padding:"28px 36px", maxWidth:1260, margin:"0 auto"}}>
            <div style={{marginBottom:6, display:"flex", alignItems:"center", gap:14}}>
                <div style={{width:36, height:36, borderRadius:"50%", background:`radial-gradient(circle at 30% 30%, ${P.cy},${P.vi})`, boxShadow:`0 0 20px ${P.cyG}`, flexShrink:0}}/>
                <div>
                    <h1 style={{fontSize:22, fontWeight:700, margin:0, letterSpacing:-0.5, color:P.txB}}>Space Economy</h1>
                    <div style={{fontSize:13, color:P.txD, fontFamily:FM, marginTop:2}}>Early Stage or Pipe Dream?</div>
                </div>
            </div>
            <div style={{fontSize:10, color:P.txD, fontFamily:FM, marginBottom:20, marginLeft:50}}>
                11 pure-play · 5 diversified · SPY/ARKX/ROKT benchmarks
            </div>
            <TB tabs={TABS} active={tab} onChange={setTab}/>
            {tab==="Overview" && <OverviewTab />}
            {tab==="Fundamentals" && <FundamentalsTab />}
            {tab==="Valuation" && <ValuationTab />}
            {tab==="Regression" && <RegressionTab />}
            {tab==="Risk and Regimes" && <RiskTab />}
            {tab==="Robustness" && <RobustnessTab />}
            {tab==="AI Analysis" && <AITab />}
        </div>
        </div>
    )
}
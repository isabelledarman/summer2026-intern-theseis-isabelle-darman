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
const ttS = {background:P.panS,border:`1px solid ${P.brd}`, borderRadius: 8, fontSize:12, color: P.txt, boxShadow:"0 8px 32px rgba(0,0,0,0.5)"};

function Starfield(){

}

function GC({title, sub, children, style, glow}){
    return(
        <div style={{background:P.pan, backdropFilter:"blur(16px)", WebkitBackdropFilter:"blur(16px)",
            border:`1px solid ${P.brd}`,borderRadius:16,padding:"24px 28px",marginBottom:20,
            position:"relative",overflow:"hidden",
            boxShadow:glow?`0 0 40px ${glow}12,inset 0 1px 0 rgba(255,255,255,0.04)`:`inset 0 1px 0 rgba(255,255,255,0.04)`,...style}}>
            {title && <div style={{fontSize:13,fontWeight:600,color:P.txB,letterSpacing:0.5,fontFamily:F,marginBottom:sub?4:16}}>{title}</div>}
            {sub && <div style={{fontSize:10,color:P.txD,marginBottom:16,fontFamily:FM}}>{sub}</div>}
            {children}
        </div>
    )
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

const cDot = (props) => {
    const {cx, cy, payload} = props;
    const col = payload.group === "pure_play"?P.cy: P.div;
    return(
        <g>
            <circle cx={cx} cy={cy} r={8} fill={col} opacity={0.12}/>
            <circle cx={cx} cy={cy} r={8} fill={col} opacity={0.9}/>
            <text x={cx+10} y = {cy-8} fill={P.star} fontSize={9} fontFamily={FM} opacity={0.8}>{payload.ticker}</text>
        </g>
    )
}

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
                                <Tooltip contentStyle={ttS}/>
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

}

function ValuationTab(){

}

function RegressionTab(){

}

function RiskTab(){

}

function RobustnessTab(){

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
                <div style={{width: 36, height: 36, borderRadius:"50%", background: `radial-gradient(circle at 30% 30%, ${P.cy},${P.vi})`, boxShadow: `0 0 20px ${P.cyG}`, flexShrink:0}}/>
                <div>
                    <h1 style={{fontSize:22, fontWeight: 700, margin:0, letterSpacing:-0.5, color:P.txB}}>Space Economy</h1>
                    <div style={{fontSize:13, color:P.txD, fontFamily:FM, marginTop:2}}>Early Stage or Pipe Dream?</div>
                </div>
            </div>
            <div style={{fontSize:10, color:P.txD, fontFamily:FM, marginBottom:20, marginLeft:50}}>
                11 pure-play  5 diversified   SPY/ARKX?ROKT benchmarks
            </div>
            <TB tabs={TABS} active = {tab} onChange={setTab}/>
            {tab==="Overview" && <OverviewTab />}
            {tab==="Fundamentals" && <FundamentalsTab />}
            {tab==="Valuation" && <ValuationTab />}
            {tab==="Regression" && <RegressionTab />}
            {tab==="Risk & Regimes" && <RiskTab />}
            {tab==="Robustness" && <RobustnessTab />}
            {tab==="AI Analysis" && <AITab />}
        </div>
    )
}
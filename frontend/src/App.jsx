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

const RISK_PROFILES = {
    conservative: {
        label: "Conservative",
        color: "#4fc3f7",
        criteria: `RISK TOLERANCE: CONSERVATIVE
- Require FCF-positive for any favorable score; negative FCF is an automatic red flag
- Share dilution above 30% is heavily penalized (not 50%)
- Runway under 3 years = critical concern
- Only "Earned" verdicts count positively; "Mixed" is treated as negative
- P/S above 8x is considered overvalued regardless of growth
- Demand a Sharpe ratio above 0.5 to consider risk-adjusted returns acceptable
- Position sizing should be minimal (1-2% max) given the speculative nature
- Default to AVOID unless evidence is overwhelming`,
    },
    moderate: {
    label: "Moderate",
    emoji: "⚖️",
    color: "#ffd54f",
    criteria: `RISK TOLERANCE: MODERATE (thesis-aligned)
    - The commercial space sector is REAL but NOT YET DERISKED — more narrative than earned at the sector level
    - The sector as a whole is NOT investable as a basket; it is only investable on a name-by-name basis where fundamentals justify it
    - FCF trajectory matters more than current profitability — improving is acceptable, but still-negative with no trend is a red flag
    - Share dilution above 50% is concerning; under 30% is fine
    - Runway under 2 years is a serious concern given how capital-intensive space is
    - "Earned" verdicts are the only names worth owning; "Mixed" names are watchlist-only; "Narrative" names should be avoided
    - P/S up to 12x can be justified ONLY with demonstrated revenue growth, not projected TAM capture
    - Sharpe near 0 is tolerable for individual names with strong fundamental trajectories, but the sector median Sharpe confirms the risk is real
    - Position sizing: 2-4% per name for the strongest 2-3 names only, NOT a sector-wide allocation
    - The verdict should reflect that a few names have earned their valuations through operational progress, but the majority remain speculative and narrative-driven
    - Frame the conclusion around selectivity: the opportunity is real but narrow`,
},
    aggressive: {
        label: "Aggressive",
        color: "#ff8a65",
        criteria: `RISK TOLERANCE: AGGRESSIVE / GROWTH-SEEKING
- FCF negativity is expected and acceptable for pre-profit growth companies
- Dilution is the cost of scaling; only penalize if >100% with no revenue growth to show for it
- Runway under 1 year is the only real concern
- Even "Narrative" verdicts can be positive if TAM is large and management is executing
- P/S up to 20x is justified for high-growth names in expanding TAMs
- Negative Sharpe is tolerable for high-conviction asymmetric bets
- Position sizing 5-10%+ for the sector; this is a generational opportunity
- Default to BUY unless the company is clearly failing`,
    },
};
const AI_PROMPTS = {
    sentiment: {
        label: "Earnings Call Sentiment",
        description: "Score each company's management language: are they talking revenue milestones or still pitching TAM & vision?",
        buildPrompt: (ctx, riskProfile) => `You are a finance research analyst. Given the following data snapshot for 11 pure-play space companies, score each company's likely management communication style on a scale from 1 (pure narrative/vision/TAM talk) to 5 (operational metrics, revenue milestones, margin targets).

Base your assessment on the financial data provided — companies with strong fundamental returns, improving margins, and FCF positivity are more likely to have shifted to operational language. Companies with narrative verdicts, high dilution, and negative FCF are likely still in pitch mode.

${riskProfile}

Apply the risk tolerance above when scoring: a conservative lens should be stricter about what counts as "Operational" (require strong FCF + margins), while an aggressive lens should be more generous (early revenue traction can count as operational progress).

Return ONLY valid JSON (no markdown, no backticks) as an array of objects with keys: ticker, score (1-5), commStyle ("Narrative" | "Transitioning" | "Operational"), reasoning (one sentence).

DATA:
${ctx}`,
    },
    riskFactors: {
        label: "Risk Profile Classification",
        description: "Classify each company's dominant risk type: execution, market, or financial.",
        buildPrompt: (ctx, riskProfile) => `You are a finance research analyst. Given the following data snapshot for 11 pure-play space companies, classify each company's dominant risk type based on the financial evidence.

Risk types:
- "Financial" = might run out of money (negative FCF, low runway, high dilution)
- "Market" = demand might not exist (requires huge TAM share, unproven segment)
- "Execution" = demand exists but company might not deliver (has revenue but margins weak)

Companies further along their maturity journey shift from Financial→Market→Execution risk.

${riskProfile}

Apply the risk tolerance above when assigning maturity scores: a conservative lens should require stronger evidence before rating a company as mature (4-5), while an aggressive lens can credit early momentum more generously.

Return ONLY valid JSON (no markdown, no backticks) as an array of objects with keys: ticker, primary_risk ("Financial" | "Market" | "Execution"), secondary_risk, maturity (1-5 where 5=most mature), reasoning (one sentence).

DATA:
${ctx}`,
    },
    investmentMemo: {
        label: "Investment Memo",
        description: "Generate a structured investment thesis with a clear BUY / AVOID verdict for the sector.",
        buildPrompt: (ctx, riskProfile) => `You are a senior portfolio strategist writing a decisive investment memo. Based on the data below, write a 400-word investment memo on the commercial space sector.

${riskProfile}
Structure:
1. VERDICT (one sentence: "The commercial space sector IS / IS NOT investable for a [risk tolerance level] portfolio because...")
2. THE BULL CASE (2-3 strongest evidence points from the data)
3. THE BEAR CASE (2-3 strongest counter-evidence)
4. NAME-LEVEL PICKS (which 2-3 names have the best risk/reward given the stated risk tolerance, and which 2-3 should be avoided)
5. POSITION SIZING (calibrate allocation % specifically to the risk tolerance above)

Be decisive. The risk tolerance should clearly shift your verdict — a conservative investor might AVOID what an aggressive investor would BUY. Let the risk lens drive the answer alongside the data.

Do not include a title or header line — start directly with the VERDICT section.

DATA:
${ctx}`,
    },
};

function SimpleMD({ text }) {
    const lines = text.split('\n');
    return (
        <div>
            {lines.map((line, i) => {
                let html = line
                    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#e8eeff">$1</strong>')
                    .replace(/\*(.+?)\*/g, '<em>$1</em>');
                
                if (line.startsWith('## ')) return <h3 key={i} style={{ color: P.cy, fontSize: 14, fontFamily: F, margin: '16px 0 8px' }}>{line.slice(3)}</h3>;
                if (line.startsWith('# ')) return <h2 key={i} style={{ color: P.cy, fontSize: 16, fontFamily: F, margin: '20px 0 8px' }}>{line.slice(2)}</h2>;
                if (line.trim().startsWith('* ') || line.trim().startsWith('- ')) {
                    const content = line.trim().slice(2);
                    let bulletHtml = content.replace(/\*\*(.+?)\*\*/g, '<strong style="color:#e8eeff">$1</strong>').replace(/\*(.+?)\*/g, '<em>$1</em>');
                    return <div key={i} style={{ paddingLeft: 16, marginBottom: 4 }} dangerouslySetInnerHTML={{ __html: '• ' + bulletHtml }} />;
                }
                if (line.trim() === '') return <div key={i} style={{ height: 12 }} />;
                return <div key={i} style={{ marginBottom: 6 }} dangerouslySetInnerHTML={{ __html: html }} />;
            })}
        </div>
    );
}

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
      <text x={cx+10} y={cy-8} fill={col} fontSize={9} fontFamily={FM} opacity={0.8}>{payload.ticker}</text>
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
    const hrd = useApi("hurdle")

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
            {hrd && hrd.verdict && (
                <div style={{
                    background: hrd.compensated ? `${P.em}10` : `${P.ro}10`,
                    border: `1px solid ${hrd.compensated ? P.em : P.ro}30`,
                    borderRadius: 12, padding: "16px 24px", marginBottom: 20,
                    display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16,
                }}>
                    <div>
                        <div style={{ fontSize: 9, fontFamily: FM, color: P.txD, textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>Hurdle Rate Test</div>
                        <div style={{ fontSize: 13, fontFamily: F, fontWeight: 600, color: hrd.compensated ? P.em : P.ro }}>{hrd.verdict}</div>
                    </div>
                    <div style={{ display: "flex", gap: 24 }}>
                        <SP label="Space Sharpe" value={hrd.space_median_sharpe} color={P.cy} />
                        <SP label="SPY Sharpe" value={hrd.benchmark_sharpe} color={P.txD} />
                        <SP label="Premium" value={hrd.sharpe_premium > 0 ? `+${hrd.sharpe_premium}` : hrd.sharpe_premium} color={hrd.sharpe_premium > 0 ? P.em : P.ro} />
                    </div>
                </div>
            )}
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
        {key:"ps_ratio", label:"P/S"}, {key:"ev_to_rev", label:"EV/Rev"},
        {key:"rev_growth_%", label:"Rev%", color: r=>(r['rev_growth_%']??0)>0?P.em:P.ro},
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
                        <YAxis type="number" dataKey="ps_ratio" tick={{fill:P.txD,fontSize:9, fontFamily:FM}}
                        label={{value:"P/S", angle:-90, position:"insideLeft", fill:P.txD,fontSize:10, fontFamily: FM}}/>
                        <Tooltip content={<CustomTooltip/>}/>
                        <ReferenceLine y={4} stroke={P.am} strokeDasharray="4 3" label = {{value:"target PS=4", fill:P.am, fontSize:9, position:"insideBottomRight"}}/>
                        <Scatter data={all.map(d => ({...d, _color: d.group === "pure_play" ? P.cy : P.div}))} shape={<CDot/>}/>
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
                <ComposedChart data={reg.points.map(d => ({...d, _color: d.group === "pure_play" ? P.cy : P.div}))}>
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
    const drop = rob.drop_top || {};
    const synStress = rob.synthesis_stress || {};
    const valSens = (rob.valuation_sensitivity || []).filter(v => v.cagr_ps4 != null);

    return(
        <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:20}}>
            <GC title="Winner Dependence Test" sub= "Does the revenue to retunr link survive without the top 2 stocks?" glow={P.am} style = {{gridColumn:"1/-1"}}>
                <div style={{display:"flex", gap:40, flexWrap:"wrap", alignItems:"center"}}>
                    <div>
                        <div style={{fontSize:11, fontFamily:FM, color:P.txD, marginBottom:6}}>Full Sample</div>
                        <div style={{display:"flex", gap:20}}>
                            <SP label="Slope" value={drop.slope_full?.toFixed(4) ?? "-"} color={P.cy}/>
                            <SP label="R-Squared" value={drop.r2_full?.toFixed(3) ?? "-"} color={P.cy}/>
                        </div>
                    </div>
                    <div style={{fontSize:24, color:P.txD}}>arrow</div>
                    <div>
                        <div style={{fontSize:11, fontFamily:FM, color:P.txD, marginBottom:6}}>Without {(drop.dropped || []).join(", ")}</div>
                        <div style={{display:"flex", gap:20}}>
                            <SP label="Slope" value={drop.slope_without_top?.toFixed(4) ?? "-"} color={drop.sign_flipped ? P.ro : P.em}/>
                            <SP label="R-Squared" value={drop.r2_without_top?.toFixed(3) ?? "-"} color={drop.sign_flipped ? P.ro : P.em}/>
                            <SP label = "p-value" value = {drop.p_without_top?.toFixed(3) ?? "-"}/>
                        </div>
                    </div>
                    <div style = {{padding:"8px 16px", borderRadius:8, fontSize:12, fontFamily:FM, fontWeight:600,
                        background: drop.sign_flipped ? P.ro + "20" : P.em+"20",
                        color: drop.sign_flipped ? P.ro : P.em,
                        border: `1px solid ${drop.sign_flipped ? P.ro : P.em}30`}}>
                        {drop.sign_flipped ? "Sign Flipped -- Result is Fragile": "Sign Holds -- Result is Robust"}
                    </div>                
                </div>
                {drop.note && <div style={{fontSize:11, fontFamily:FM, color:P.txD, marginTop:12}}>{drop.note}</div>}
            </GC>
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
            <GC title="Verdict Sensitivity" sub = "How many names flope from Earned to Mixed if we raise the fundamental share threshold from 50% to 60%?" glow={P.am} style={{gridColumn:"1/-1"}}>
                <div style={{display:"flex", gap:40, flexWrap:"wrap", alignItems:"center", marginBottom: 16}}>
                    <div>
                        <div style={{fontSize:11, fontFamily:FM, color:P.txD, marginBottom:6}}>Base (greather than 50% fundamental share = Earned)</div>
                        <div style={{display:"flex", gap:20}}>
                            <SP label="Earned" value={synStress.base_counts?.Earned ?? 0} color={P.em}/>
                            <SP label="Mixed" value={synStress.base_counts?.Mixed ?? 0} color={P.am}/>
                            <SP label="Narrative" value={synStress.base_counts?.Narrative ?? 0} color={P.ro}/>
                        </div>
                    </div>
                    <div style={{fontSize:24, color:P.txD}}>arrow</div>
                    <div>
                        <div style={{fontSize:11, fontFamily:FM, color:P.txD, marginBottom:6}}>String (greater than 60%)</div>
                        <SP label="Flipped" value={`${synStress.n_flipped ?? 0} names`} color={synStress.n_flipped > 2 ? P.ro : P.em}/>
                    </div>
                </div>
                {(synStress.details || []).filter(d => d.flipped).length > 0 && (
                    <DT compact columns={[
                        {key:"ticker", label:"Ticker", align:"left", bold:true, color:()=>P.cy},
                        {key:"base_verdict", label:"Base", color:r=>r.base_verdict==="Earned"?P.em:r.base_verdict==="Narrative"?P.ro:P.am},
                        {key:"strict_verdict", label:"Strict", color:r=>r.strict_verdict==="Earned"?P.em:r.strict_verdict==="Narrative"?P.ro:P.am},
                    ]} data={(synStress.details || []).filter(d => d.flipped)}/>
                )}
            </GC>
            <GC title="Valuation Target Sensitivity" sub="Implied CAGR if target P/S  = 4 vs P/S = 3" glow={P.cy}>
                {valSens.length > 0 &&(
                    <ResponsiveContainer width="100%" height={300}>
                        <CartesianGrid strokeDasharray="3 3" stroke={P.brd}/>
                        <XAxis dataKey="ticker" tick = {{fill:P.star, fontSize:10, fontFamily:FM}}/>
                        <YAxis tick={{fill:P.txD, fontSize:9, fontFamily:FM}}/>
                        <Tooltip content={<CustomTooltip/>}/>
                        <Legend wrapperStyle={{fontSize: 10, fontFamily:FM}}/>
                        <Bar dataKey="cagr_ps4" name="Target P/S = 4" fill = {P.cy} opacity={0.7}/>
                        <Bar dataKey="cagr_ps3" name="Target P/S = 3" fill = {P.am} opacity={0.7}/>
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
    const [context, setContext] = useState(null);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState({});
    const [activePrompt, setActivePrompt] = useState(null);
    const [riskTolerance, setRiskTolerance] = useState("moderate")

    useEffect(() => {
        api("ai-context").then(d => setContext(d.context)).catch(console.error);
    }, []);

    const runAnalysis = async (key) => {
        if (!context) return;
        setActivePrompt(key)
        setLoading(true);
        try{
            const prompt = AI_PROMPTS[key];
            const response = await fetch("/api/ai-analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    model: "claude-sonnet-4-6",
                    max_tokens: 1000,
                    messages: [{ role: "user", content: prompt.buildPrompt(context, RISK_PROFILES[riskTolerance].criteria) }],
                }),
            });
            const data = await response.json();
            if(data.error || !data.content){
                throw new Error(data.error?.message || data.error || "No response");
            }
            const text = data.content?.map(i => i.text || "").join("\n") || "";

            let parsed;
            try{
                const clean = text.replace(/```json|```/g, "").trim();
                parsed = { type: "json", data: JSON.parse(clean)};
            } catch{
                parsed = {type: "text", data: text};
            }
            setResults(prev => ({...prev, [key]: parsed}));
        } catch (err){
            setResults(prev => ({...prev, [key]: {type:"error", data: err.message }}));
        } finally{
            setLoading(false);
            setActivePrompt(null);
        }
    };

    const styleColor = (style) =>
        style === "Operational" ? P.em : style === "Transitioning" ? P.am: P.ro;
    const riskColor = (risk) =>
        risk === "Execution" ? P.em : risk === "Market" ? P.am : P.ro;

    return(
        <div>
            <div style = {{ background: `linear-gradient(135deg, ${P.neb}, ${P.deep})`,
                border: `1px solid ${P.vi}30`, borderRadius: 16, padding: "24px 28px", marginBottom: 24, }}>
                    <div style = {{fontSize: 13, fontWeight: 600, color: P.txB, fontFamily: F, marginBottom: 8}}>
                        AI-Powered Analysis
                    </div>
                    <div style = {{ fontSize: 11, color: P.txD, fontFamily: FM, marginBottom: 20}}>
                        Uses Gemini to analyse the thesis data and produce assessments. Each analysis sends the full data snapshot as context.
                    </div>
                    <div style = {{marginBottom: 20}}>
                        <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: 2, color: P.txD, textTransform: "uppercase", marginBottom: 10, fontFamily: FM }}>
                            Risk Tolerance
                        </div>
                        <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
                            {Object.entries(RISK_PROFILES).map(([key, profile]) => (
                                <button key={key} onClick={() => { setRiskTolerance(key); setResults({}); }}
                                    style={{
                                        padding: "10px 20px", borderRadius: 10, cursor: "pointer",
                                        background: riskTolerance === key ? `${profile.color}20` : P.pan,
                                        border: `1px solid ${riskTolerance === key ? profile.color : P.brd}`,
                                        color: riskTolerance === key ? profile.color : P.txD,
                                        fontFamily: F, fontSize: 12, fontWeight: riskTolerance === key ? 700 : 400,
                                        transition: "all 0.2s",
                                    }}>
                                    {profile.label}
                                </button>
                            ))}
                        </div>
                        <div style={{ fontSize: 9, color: RISK_PROFILES[riskTolerance].color, fontFamily: FM, textAlign: "center", marginTop: 8, opacity: 0.8 }}>
                            {riskTolerance === "conservative" && "Strict thresholds — FCF required, low dilution tolerance, favors AVOID"}
                            {riskTolerance === "moderate" && "Balanced view — weighs trajectory, nuanced verdicts"}
                            {riskTolerance === "aggressive" && "Growth-seeking — tolerates losses for upside, favors BUY on momentum"}
                        </div>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 12, alignItems: "center"}}>
                        {Object.entries(AI_PROMPTS).map(([key, prompt]) => (
                            <button key={key} onClick={() => runAnalysis(key)} disabled={loading || !context}
                                style={{
                                    padding: "12px 20px", borderRadius: 10, cursor: loading ? "wait" : "pointer",
                                    background: results[key] ? P.cyD : P.pan,
                                    border: `1px solid ${results[key] ? P.cy + "40" : P.brd}`,
                                    color: P.txB, fontFamily: F, fontSize: 12, fontWeight: 500,
                                    opacity: loading && activePrompt !== key ? 0.5 : 1,
                                    transition: "all 0.2s",
                                }}>
                                {activePrompt === key ? "Analyzing…" : prompt.label}
                                <div style={{ fontSize: 9, color: P.txD, marginTop: 4 }}>{prompt.description}</div>
                            </button>
                        ))}
                    </div>
                </div>

                {results.sentiment && results.sentiment.type === "json" && (
                    <div style = {{display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20}}>
                        <GC title="Narrative -> Operational Score" sub="1 = pure vision talk, 5 = operational metrics" glow = {P.vi} style = {{gridColumn: "1/-1"}}>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={[...results.sentiment.data].sort((a, b) => b.score - a.score)}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={P.brd} />
                                    <XAxis dataKey="ticker" tick={{ fill: P.star, fontSize: 10, fontFamily: FM }} />
                                    <YAxis domain={[0, 5]} tick={{ fill: P.txD, fontSize: 9, fontFamily: FM }} />
                                    <Tooltip content={<CustomTooltip />} />
                                    <ReferenceLine y={3} stroke={P.am} strokeDasharray="4 3" label={{ value: "Transition", fill: P.am, fontSize: 9 }} />
                                    <Bar dataKey="score" name="Maturity Score" radius={[6, 6, 0, 0]}>
                                        {[...results.sentiment.data].sort((a, b) => b.score - a.score).map((d, i) =>
                                            <Cell key={i} fill={styleColor(d.style)} opacity={0.8} />
                                        )}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </GC>
                        <GC title= "Sentiment Detail" style={{gridColumn: "1/-1"}}>
                            <DT compact columns = {[
                                { key: "ticker", label: "Ticker", align: "left", bold: true, color: () => P.cy },
                                { key: "score", label: "Score" },
                                { key: "style", label: "Style", color: r => styleColor(r.style) },
                                { key: "reasoning", label: "Reasoning", align: "left", color: () => P.txD },
                            ]} data = {results.sentiment.data}/>
                        </GC>
                    </div>
                )}
                {results.riskFactors && results.riskFactors.type === "json" && (
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginTop: 20 }}>
                        <GC title="Risk Maturity" sub="1 = earliest stage, 5 = most mature" glow={P.cy}>
                            <ResponsiveContainer width="100%" height={340}>
                                <BarChart data={[...results.riskFactors.data].sort((a, b) => b.maturity - a.maturity)} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" stroke={P.brd} />
                                    <XAxis type="number" domain={[0, 5]} tick={{ fill: P.txD, fontSize: 9, fontFamily: FM }} />
                                    <YAxis type="category" dataKey="ticker" tick={{ fill: P.star, fontSize: 10, fontFamily: FM }} width={48} />
                                    <Tooltip content={<CustomTooltip />} />
                                    <Bar dataKey="maturity" name="Maturity" radius={[0, 6, 6, 0]}>
                                        {[...results.riskFactors.data].sort((a, b) => b.maturity - a.maturity).map((d, i) =>
                                            <Cell key={i} fill={riskColor(d.primary_risk)} opacity={0.8} />
                                        )}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </GC>
                        <GC title="Risk Classification" glow={P.vi}>
                            <DT compact columns={[
                                { key: "ticker", label: "Ticker", align: "left", bold: true, color: () => P.cy },
                                { key: "primary_risk", label: "Primary", color: r => riskColor(r.primary_risk) },
                                { key: "secondary_risk", label: "Secondary", color: r => riskColor(r.secondary_risk) },
                                { key: "maturity", label: "Maturity" },
                                { key: "reasoning", label: "Reasoning", align: "left", color: () => P.txD },
                            ]} data={results.riskFactors.data} />
                        </GC>
                    </div>
                )}

                {results.investmentMemo && results.investmentMemo.type === "text" && (
                <GC title="Investment Memo" glow={P.cy} style={{ marginTop: 20 }}>
                    <div style={{
                        fontSize: 12, fontFamily: FM, color: P.txt, lineHeight: 1.7,
                        whiteSpace: "pre-wrap", maxWidth: 800,
                    }}>
                        <SimpleMD text={results.investmentMemo.data}/>
                    </div>
                </GC>
            )}

            {Object.entries(results).filter(([, v]) => v.type === "error").map(([key, v]) => (
                <GC key={key} title={`Error: ${AI_PROMPTS[key].label}`}>
                    <div style={{ color: P.ro, fontSize: 11, fontFamily: FM }}>{v.data}</div>
                </GC>
            ))}
     
        </div>
    )
}

function DilutionTab(){
    const dil = useApi("dilution");
    if(!dil) return <Loading />;
    const table = (dil.table || []).filter(d => d.group === "pure_play");
    const sum = dil.summary || {};

    const sorted = [...table].filter(d=>d.share_growth_pct != null || d['share_growth_%'] != null)
        .sort((a, b) => (b['share_growth_%'] ?? 0) - (a['share_growth_%'] ?? 0));
    
    return(
        <div style={{display: "grid", gridTemplateColumns:"1fr 1fr", gap: 20}}>
            <div style={{
                gridColumn: "1/-1",
                background: (sum.heavily_dilutive_count > sum.pure_play_total / 2) ? `${P.ro}10` : `${P.am}10`,
                border: `1px solid ${(sum.heavily_dilutive_count > sum.pure_play_total / 2) ? P.ro : P.am}30`,
                borderRadius: 12, padding: "16px 24px",
                display: "flex", gap: 32, alignItems: "center", flexWrap: "wrap",
            }}>
                <div>
                    <div style={{fontSize: 9, fontFamily: FM, color: P.txD, textTransform: "uppercase", letterSpacing: 1, marginBottom: 4}}>Dilution Impact</div>
                    <div style={{fontSize: 13, fontFamily:F, fontWeight: 600, color: P.txB}}>
                        {sum.heavily_dilutive_count}/{sum.pure_play_total} pure-plays have diluted shareholders {">"}50%
                    </div>
                    <SP label = "Median Share Growth" value ={sum['median_share_growth_%'] != null ? `${sum['median_share_growth_%']}` : '-'} color = {P.am}/>
                    <SP label = "Median Dilution-Adj Return" value ={sum['median_dilution_adj_return_%'] != null ? `${sum['median_dilution_adj_return_%']}` : '-'} color = {sum["median_dilution_adj_return_%"] > 0 ? P.em : P.ro}/>
                </div>
            </div>
                <GC title = "Share Count Growth %" sub = "Higher = More Dilutive" glow = {P.ro}>
                    <ResponsiveContainer width="100%" height={340}>
                        <BarChart data={sorted.map(d => ({...d, _color: d["share_growth_%"] > 50 ? P.ro : P.am}))} layout="vertical">                            <CartesianGrid strokeDasharray="3 3" stroke={P.brd} />
                            <XAxis type="number" tick={{ fill: P.txD, fontSize: 9, fontFamily: FM }} />
                            <YAxis type="category" dataKey="ticker" tick={{ fill: P.star, fontSize: 10, fontFamily: FM }} width={48} />
                            <Tooltip content={<CustomTooltip />} />
                            <ReferenceLine x={50} stroke={P.ro} strokeDasharray="4 3" label={{ value: "50%", fill: P.ro, fontSize: 9, position:"insideBottomRight" }} />
                            <Bar dataKey="share_growth_%" radius={[0, 6, 6, 0]}>
                                {sorted.map((d, i) => <Cell key={i} fill={d["share_growth_%"] > 50 ? P.ro : P.am} opacity={0.75} />)}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </GC>
                <GC title = "Price Return vs Dilution-Adjusted" sub = "What Shareholders Actually Earned" glow = {P.cy}>
                    <ResponsiveContainer width="100%" height={340}>
                        <BarChart data={table.filter(d=> d['price_return_%'] != null)}>
                            <CartesianGrid strokeDasharray="3 3" stroke={P.brd} />
                            <XAxis dataKey='ticker' tick={{ fill: P.star, fontSize: 10, fontFamily: FM }} />
                            <YAxis tick={{ fill: P.txD, fontSize: 9, fontFamily: FM }} />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend wrapperStyle={{fontSize: 10, fontFamily: FM}}/>
                            <ReferenceLine y = {0} stroke={P.txB} strokeWidth={0.5}/>
                            <Bar dataKey="price_return_%" name = "Price Return" fill={P.cy} opacity={0.7} />
                            <Bar dataKey="dilution_adj_return_%" name = "Dilution Adjusted" fill={P.vi} opacity={0.7} />
                        </BarChart>
                    </ResponsiveContainer>
                </GC>
                <GC title="Full Dilution Table" style={{gridColumn: "1/-1"}}>
                    <DT compact columns = {[
                        { key: "ticker", label: "Ticker", align: "left", bold: true, color: () => P.cy },
                        { key: "price_return_%", label: "Price Ret%", color: r => (r["price_return_%"] ?? 0) > 0 ? P.em : P.ro },
                        { key: "share_growth_%", label: "Share Growth%", color: r => (r["share_growth_%"] ?? 0) > 50 ? P.ro : P.am },
                        { key: "dilution_drag_%", label: "Drag%" },
                        { key: "dilution_adj_return_%", label: "Adj Return%", color: r => (r["dilution_adj_return_%"] ?? 0) > 0 ? P.em : P.ro },
                        { key: "heavily_dilutive", label: "Flag", render: r => r.heavily_dilutive ? "⚠" : "—", color: r => r.heavily_dilutive ? P.ro : P.txD }, 
                    ]} data={table} />
                </GC>
            </div>
    );

}

function TAMTab(){
    const tamData = useApi("tam")
    if (!tamData) return <Loading />;
    const table = tamData.table || [];
    const sum = tamData.summary || {};

    return (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20}}>
            <div style={{
                gridColumn: "1/-1",
                background: sum.stretch_count > sum.feasible_count ? `${P.ro}10` : `${P.em}10`,
                border: `1px solid ${sum.stretch_count > sum.feasible_count ? P.ro : P.em}30`,
                borderRadius: 12, padding: "16px 24px",
                display: "flex", gap: 32, alignItems: "center", flexWrap: "wrap",
            }}>
                <div>
                    <div style={{fontSize: 9, fontFamily: FM, color: P.txD, textTransform:"uppercase", letterSpacing: 1, marginBottom: 4}}>TAM Feasibility</div>
                    <div style={{ fontSize: 13, fontFamily: F, fontWeight: 600, color: P.txB }}>
                        {sum.feasible_count} feasible, {sum.stretch_count} stretch, {sum.no_data_count} no data — of {sum.total} names
                    </div>
                </div>
                <SP label="Median Required Share" value = {sum['median_required_share_%'] != null ? `${sum['median_required_share_%']}%` : '-'} color={P.am}/>
            </div>
            <GC title = "Current vs Required Market Share" sub ="Required Share to Justify Valuation at Target P/S = 4" style={{gridColumn: "1/-1"}} glow={P.cy}>
                <ResponsiveContainer width="100%" height={360}>
                    <BarChart data={table.filter(d => d["current_share_%"] != null)}>
                        <CartesianGrid strokeDasharray="3 3" stroke={P.brd} />
                        <XAxis dataKey="ticker" tick={{ fill: P.star, fontSize: 10, fontFamily: FM }} />
                        <YAxis tick={{ fill: P.txD, fontSize: 9, fontFamily: FM }} label={{ value: "% of TAM", angle: -90, position: "insideLeft", fill: P.txD, fontSize: 10, fontFamily: FM }} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ fontSize: 10, fontFamily: FM }} />
                        <ReferenceLine y={20} stroke={P.ro} strokeDasharray="4 3" label={{ value: "20% ceiling", fill: P.ro, fontSize: 9, offset: 10, position:"insideTopRight"}} />
                        <Bar dataKey="current_share_%" name="Current Share" fill={P.em} opacity={0.8} />
                        <Bar dataKey="required_share_%" name="Required Share" fill={P.am} opacity={0.7} />
                    </BarChart>
                </ResponsiveContainer>
            </GC>
            <GC title="TAM Detail" style={{ gridColumn: "1/-1" }}>
                <DT compact columns={[
                    { key: "ticker", label: "Ticker", align: "left", bold: true, color: () => P.cy },
                    { key: "tam_bn", label: "TAM ($B)" },
                    { key: "current_rev_bn", label: "Rev ($B)" },
                    { key: "current_share_%", label: "Share%" },
                    { key: "required_rev_bn", label: "Req Rev ($B)" },
                    { key: "required_share_%", label: "Req Share%", color: r => (r["required_share_%"] ?? 0) > 20 ? P.ro : P.em },
                    { key: "feasible", label: "Feasible", render: r => r.feasible === true ? "✓" : r.feasible === false ? "✗" : "—", color: r => r.feasible === true ? P.em : r.feasible === false ? P.ro : P.txD },
                ]} data={table} />
            </GC>
        </div>
    )
}

function SignalScannerTab() {
    const [signals, setSignals] = useState(null);
    const [loading, setLoading] = useState(false);
    const [scanPhase, setScanPhase] = useState(0);
    const [error, setError] = useState(null);
    const intervalRef = useRef(null);

    const TICKERS = ["RKLB","PL","IRDM","VSAT","ASTS","RDW","KTOS","SATL","LUNR","BKSY","SPIR"];

    const runScan = async () => {
        setLoading(true);
        setError(null);
        setScanPhase(0);
        intervalRef.current = setInterval(() => setScanPhase(p => p + 1), 1800);
        try {
            const response = await fetch("/api/ai-news-signal", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tickers: TICKERS }),
            });
            const data = await response.json();
            if (data.error || !data.content) throw new Error(data.error?.message || data.error || "No response");
            const text = data.content.map(i => i.text || "").join("\n");
            const clean = text.replace(/```json|```/g, "").trim();
            setSignals(JSON.parse(clean));
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
            clearInterval(intervalRef.current);
        }
    };

    const scanMessages = [
        "Scanning orbital frequencies...",
        "Intercepting market telemetry...",
        "Decoding news transmissions...",
        "Correlating sentiment vectors...",
        "Triangulating signal strength...",
        "Compiling intelligence brief...",
    ];

    const sigColor = s => s === "BUY" ? P.em : s === "SELL" ? P.ro : P.am;
    const sigIcon = s => s === "BUY" ? "▲" : s === "SELL" ? "▼" : "◆";

    const buyCount = signals?.filter(s => s.signal === "BUY").length || 0;
    const sellCount = signals?.filter(s => s.signal === "SELL").length || 0;
    const holdCount = signals?.filter(s => s.signal === "HOLD").length || 0;
    const avgConf = signals ? (signals.reduce((a, s) => a + s.confidence, 0) / signals.length).toFixed(1) : 0;
    const sectorBias = buyCount > sellCount ? "BULLISH" : sellCount > buyCount ? "BEARISH" : "NEUTRAL";
    const biasColor = sectorBias === "BULLISH" ? P.em : sectorBias === "BEARISH" ? P.ro : P.am;

    return (
        <div>
            {/* Scanner Header */}
            <div style={{
                background: `linear-gradient(135deg, ${P.deep}, ${P.neb})`,
                border: `1px solid ${P.cy}20`, borderRadius: 16,
                padding: "32px 36px", marginBottom: 24,
                position: "relative", overflow: "hidden",
            }}>
                <div style={{
                    position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
                    background: `radial-gradient(ellipse at 50% 0%, ${P.cy}08 0%, transparent 70%)`,
                }} />
                <div style={{ position: "relative", zIndex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
                        <div style={{
                            width: 10, height: 10, borderRadius: "50%",
                            background: loading ? P.am : signals ? P.em : P.txD,
                            boxShadow: `0 0 12px ${loading ? P.am : signals ? P.em : P.txD}`,
                            animation: loading ? "pulse 1.5s infinite" : "none",
                        }} />
                        <span style={{ fontSize: 9, fontFamily: FM, color: P.txD, textTransform: "uppercase", letterSpacing: 2 }}>
                            {loading ? "scanning" : signals ? "scan complete" : "standing by"}
                        </span>
                    </div>
                    <div style={{ fontSize: 20, fontWeight: 700, fontFamily: F, color: P.txB, marginBottom: 4 }}>
                        Signal Scanner
                    </div>
                    <div style={{ fontSize: 11, color: P.txD, fontFamily: FM, marginBottom: 20, maxWidth: 600 }}>
                        Scans live news for all 11 pure-play space companies and generates BUY / HOLD / SELL signals
                        based on recent catalysts, sentiment, and risk factors.
                    </div>
                    <button onClick={runScan} disabled={loading} style={{
                        padding: "12px 32px", borderRadius: 10, cursor: loading ? "wait" : "pointer",
                        background: loading ? P.pan : `linear-gradient(135deg, ${P.cy}30, ${P.vi}30)`,
                        border: `1px solid ${loading ? P.brd : P.cy}50`,
                        color: P.txB, fontFamily: FM, fontSize: 12, fontWeight: 600,
                        letterSpacing: 1, textTransform: "uppercase",
                        transition: "all 0.3s",
                    }}>
                        {loading ? "Scanning..." : signals ? "Re-Scan" : "Initiate Scan"}
                    </button>
                </div>
            </div>

            {/* Scanning Animation */}
            {loading && (
                <GC glow={P.cy}>
                    <div style={{ textAlign: "center", padding: "30px 0" }}>
                        <div style={{ position: "relative", width: 120, height: 120, margin: "0 auto 20px" }}>
                            <svg width="120" height="120" viewBox="0 0 120 120">
                                <circle cx="60" cy="60" r="55" fill="none" stroke={P.brd} strokeWidth="1" />
                                <circle cx="60" cy="60" r="40" fill="none" stroke={P.brd} strokeWidth="0.5" />
                                <circle cx="60" cy="60" r="25" fill="none" stroke={P.brd} strokeWidth="0.5" />
                                <circle cx="60" cy="60" r="3" fill={P.cy} opacity="0.8" />
                                <line x1="60" y1="60" x2="60" y2="8" stroke={P.cy} strokeWidth="1.5" opacity="0.6"
                                    style={{ transformOrigin: "60px 60px", animation: "spin 2s linear infinite" }} />
                                {TICKERS.slice(0, 8).map((_, i) => {
                                    const angle = (i / 8) * Math.PI * 2 - Math.PI / 2;
                                    const r = 35 + Math.random() * 18;
                                    return <circle key={i} cx={60 + Math.cos(angle) * r} cy={60 + Math.sin(angle) * r}
                                        r="2" fill={P.cy} opacity={scanPhase > i ? 0.8 : 0.15} />;
                                })}
                            </svg>
                        </div>
                        <div style={{ fontSize: 12, fontFamily: FM, color: P.cy, marginBottom: 6 }}>
                            {scanMessages[Math.min(scanPhase, scanMessages.length - 1)]}
                        </div>
                        <div style={{ fontSize: 9, fontFamily: FM, color: P.txD }}>
                            {Math.min(scanPhase + 1, TICKERS.length)} / {TICKERS.length} targets acquired
                        </div>
                    </div>
                </GC>
            )}

            {/* Sector Summary */}
            {signals && (
                <div style={{
                    background: biasColor + "08",
                    border: `1px solid ${biasColor}25`,
                    borderRadius: 16, padding: "24px 32px", marginBottom: 24,
                    display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 20,
                }}>
                    <div>
                        <div style={{ fontSize: 9, fontFamily: FM, color: P.txD, textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 6 }}>
                            Sector Bias
                        </div>
                        <div style={{ fontSize: 22, fontWeight: 700, fontFamily: F, color: biasColor, letterSpacing: 1 }}>
                            {sectorBias}
                        </div>
                    </div>
                    <div style={{ display: "flex", gap: 28 }}>
                        <div style={{ textAlign: "center" }}>
                            <div style={{ fontSize: 28, fontWeight: 700, fontFamily: FM, color: P.em }}>{buyCount}</div>
                            <div style={{ fontSize: 9, fontFamily: FM, color: P.txD, letterSpacing: 1 }}>BUY</div>
                        </div>
                        <div style={{ textAlign: "center" }}>
                            <div style={{ fontSize: 28, fontWeight: 700, fontFamily: FM, color: P.am }}>{holdCount}</div>
                            <div style={{ fontSize: 9, fontFamily: FM, color: P.txD, letterSpacing: 1 }}>HOLD</div>
                        </div>
                        <div style={{ textAlign: "center" }}>
                            <div style={{ fontSize: 28, fontWeight: 700, fontFamily: FM, color: P.ro }}>{sellCount}</div>
                            <div style={{ fontSize: 9, fontFamily: FM, color: P.txD, letterSpacing: 1 }}>SELL</div>
                        </div>
                    </div>
                    <div style={{ display: "flex", gap: 24 }}>
                        <SP label="Avg Confidence" value={`${avgConf} / 5`} color={P.cy} />
                        <SP label="Coverage" value={`${signals.length} names`} color={P.txB} />
                    </div>
                </div>
            )}

            {/* Signal Cards */}
            {signals && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                    {[...signals]
                        .sort((a, b) => {
                            const order = { BUY: 0, HOLD: 1, SELL: 2 };
                            return (order[a.signal] ?? 1) - (order[b.signal] ?? 1) || b.confidence - a.confidence;
                        })
                        .map((d, i) => {
                            const sc = sigColor(d.signal);
                            return (
                                <div key={i} style={{
                                    background: P.pan, backdropFilter: "blur(16px)",
                                    border: `1px solid ${sc}25`,
                                    borderRadius: 14, padding: "20px 22px",
                                    position: "relative", overflow: "hidden",
                                    transition: "border-color 0.3s",
                                }}>
                                    {/* Glow accent */}
                                    <div style={{
                                        position: "absolute", top: 0, left: 0, right: 0, height: 2,
                                        background: `linear-gradient(90deg, transparent, ${sc}, transparent)`,
                                        opacity: 0.6,
                                    }} />

                                    {/* Header */}
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                                        <div>
                                            <div style={{ fontSize: 18, fontWeight: 700, fontFamily: FM, color: P.cy }}>{d.ticker}</div>
                                        </div>
                                        <div style={{
                                            display: "flex", alignItems: "center", gap: 6,
                                            background: sc + "15", border: `1px solid ${sc}30`,
                                            padding: "5px 14px", borderRadius: 8,
                                        }}>
                                            <span style={{ fontSize: 14, color: sc }}>{sigIcon(d.signal)}</span>
                                            <span style={{ fontSize: 13, fontWeight: 700, fontFamily: FM, color: sc, letterSpacing: 1 }}>
                                                {d.signal}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Confidence */}
                                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 14 }}>
                                        <div style={{ display: "flex", gap: 3 }}>
                                            {[1, 2, 3, 4, 5].map(n => (
                                                <div key={n} style={{
                                                    width: 20, height: 4, borderRadius: 2,
                                                    background: n <= d.confidence ? sc : P.brd,
                                                    transition: "background 0.3s",
                                                }} />
                                            ))}
                                        </div>
                                        <span style={{ fontSize: 9, fontFamily: FM, color: P.txD, marginLeft: 2 }}>
                                            {d.confidence}/5 confidence
                                        </span>
                                    </div>

                                    {/* Headline */}
                                    <div style={{
                                        fontSize: 12, fontFamily: F, fontWeight: 600, color: P.txB,
                                        marginBottom: 12, lineHeight: 1.5,
                                        borderLeft: `2px solid ${sc}40`, paddingLeft: 10,
                                    }}>
                                        {d.headline}
                                    </div>

                                    {/* Catalyst & Risk */}
                                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                                        <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                                            <span style={{
                                                fontSize: 8, fontFamily: FM, color: P.em,
                                                background: P.em + "15", padding: "2px 6px",
                                                borderRadius: 4, flexShrink: 0, marginTop: 1,
                                                letterSpacing: 0.5,
                                            }}>CATALYST</span>
                                            <span style={{ fontSize: 10, fontFamily: FM, color: P.txt, lineHeight: 1.5 }}>{d.catalyst}</span>
                                        </div>
                                        <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                                            <span style={{
                                                fontSize: 8, fontFamily: FM, color: P.ro,
                                                background: P.ro + "15", padding: "2px 6px",
                                                borderRadius: 4, flexShrink: 0, marginTop: 1,
                                                letterSpacing: 0.5,
                                            }}>RISK</span>
                                            <span style={{ fontSize: 10, fontFamily: FM, color: P.txt, lineHeight: 1.5 }}>{d.risk}</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                </div>
            )}

            <style>{`
                @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
                @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }
            `}</style>
        </div>
    );
}

const TABS = ["Overview", "Fundamentals", "Valuation", "Dilution", "TAM", "Regression", "Risk and Regimes", "Signal Scanner", "AI Analysis"];

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
            {tab === "Dilution" && <DilutionTab />}
            {tab === "TAM" && <TAMTab />}
            {tab==="Regression" && <RegressionTab />}
            {tab==="Risk and Regimes" && <RiskTab />}
            {tab === "Signal Scanner" && <SignalScannerTab />}
            {tab==="AI Analysis" && <AITab />}
        </div>
        </div>
    )
}
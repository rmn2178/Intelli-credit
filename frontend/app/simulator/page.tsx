'use client';
import { useState, useCallback } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const SLIDERS = [
    { key: 'interest_rate_delta_bps', label: 'Interest Rate Change', unit: 'bps', min: -200, max: 500, step: 25, default: 0 },
    { key: 'revenue_change_pct', label: 'Revenue Change', unit: '%', min: -30, max: 30, step: 1, default: 0 },
    { key: 'churn_rate_pct', label: 'Customer Churn Rate', unit: '%', min: 0, max: 20, step: 0.5, default: 0 },
    { key: 'working_capital_days_delta', label: 'Working Capital Cycle', unit: 'days', min: -30, max: 60, step: 5, default: 0 },
    { key: 'gst_compliance_score', label: 'GST Compliance Score', unit: '%', min: 50, max: 100, step: 1, default: 100 },
    { key: 'mrr_growth_rate', label: 'MRR Growth Rate', unit: '%', min: -20, max: 50, step: 1, default: 0 },
];

export default function SimulatorPage() {
    const [params, setParams] = useState<Record<string, number>>(() => {
        const p: Record<string, number> = {};
        SLIDERS.forEach(s => { p[s.key] = s.default; });
        p['top_customer_exit'] = 0;
        return p;
    });
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [baseMetrics, setBaseMetrics] = useState<any>(null);

    const simulate = useCallback(async () => {
        const sid = localStorage.getItem('session_id');
        if (!sid) return;
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/sessions/${sid}/simulate`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sid, ...params, top_customer_exit: !!params.top_customer_exit }),
            });
            const data = await res.json();
            setResult(data); setBaseMetrics(data.base_metrics);
        } catch (err) { console.error(err); }
        setLoading(false);
    }, [params]);

    const riskScore = result?.scenarios?.[0]?.default_probability_after ?? baseMetrics?.default_probability ?? 0;
    const riskPct = (riskScore * 100).toFixed(1);

    return (
        <div className="p-6">
            <div className="mb-4">
                <h1 className="text-title font-bold text-navy-500">Causal Stress Test</h1>
                <p className="text-data text-[#94A3B8]">Digital Twin — simulate business variable impacts on default probability</p>
            </div>

            <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2 space-y-[2px]">
                    <div className="card">
                        <table className="w-full">
                            <thead><tr className="border-b border-border text-left">
                                <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Variable</th>
                                <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase w-[320px]">Control</th>
                                <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase w-[80px] text-right">Value</th>
                            </tr></thead>
                            <tbody className="divide-y divide-border">
                                {SLIDERS.map((s) => (
                                    <tr key={s.key}>
                                        <td className="px-4 py-2 text-body font-medium text-[#334155]">{s.label}</td>
                                        <td className="px-4 py-2">
                                            <input type="range" min={s.min} max={s.max} step={s.step} value={params[s.key]} onChange={e => setParams(prev => ({ ...prev, [s.key]: parseFloat(e.target.value) }))} className="w-full" />
                                            <div className="flex justify-between text-[9px] text-[#CBD5E1] font-mono mt-[2px]"><span>{s.min}{s.unit}</span><span>{s.max}{s.unit}</span></div>
                                        </td>
                                        <td className="px-4 py-2 text-right">
                                            <span className={`text-body font-bold font-mono ${params[s.key] !== s.default ? 'text-navy-500' : 'text-[#94A3B8]'}`}>
                                                {params[s.key] > 0 ? '+' : ''}{params[s.key]}{s.unit}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                                <tr>
                                    <td className="px-4 py-2 text-body font-medium text-[#334155]">Top Customer Exit</td>
                                    <td className="px-4 py-2" colSpan={2}>
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input type="checkbox" checked={!!params.top_customer_exit} onChange={e => setParams(prev => ({ ...prev, top_customer_exit: e.target.checked ? 1 : 0 }))} className="w-[14px] h-[14px] accent-navy-500" />
                                            <span className="text-data text-[#64748B]">Simulate exit of largest revenue contributor</span>
                                        </label>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <button onClick={simulate} disabled={loading} className="btn-primary w-full mt-2">
                        {loading ? 'Running Simulation...' : 'Run Simulation'}
                    </button>
                </div>

                <div className="space-y-4">
                    {/* Risk Score */}
                    <div className="card">
                        <div className="px-4 py-2 border-b border-border"><span className="text-label font-semibold text-[#64748B] uppercase">Default Probability</span></div>
                        <div className="px-4 py-4 text-center">
                            <p className={`text-[36px] font-bold font-mono leading-none ${riskScore > 0.5 ? 'text-danger-500' : riskScore > 0.2 ? 'text-[#B45309]' : 'text-emerald-600'}`}>
                                {riskPct}%
                                <span className="micro-badge micro-badge-smt">SMT</span>
                            </p>
                            <div className="w-full h-[3px] bg-border mt-3">
                                <div className={`h-full transition-all ${riskScore > 0.5 ? 'bg-danger-500' : riskScore > 0.2 ? 'bg-[#B45309]' : 'bg-emerald-500'}`} style={{ width: `${Math.min(riskScore * 100, 100)}%` }} />
                            </div>
                        </div>
                    </div>

                    {baseMetrics && (
                        <div className="card">
                            <div className="px-4 py-2 border-b border-border"><span className="text-label font-semibold text-[#64748B] uppercase">Base Metrics</span></div>
                            <div className="divide-y divide-border">
                                {[['DSCR', baseMetrics.dscr], ['Op. Margin', `${baseMetrics.operating_margin}%`], ['Z-Score', baseMetrics.z_score]].map(([l, v]) => (
                                    <div key={l as string} className="flex justify-between px-4 py-2 text-data">
                                        <span className="text-[#64748B]">{l}</span>
                                        <span className="font-bold text-navy-500 font-mono">{v}<span className="micro-badge micro-badge-verified">V</span></span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {result?.scenarios && (
                        <div className="card">
                            <div className="px-4 py-2 border-b border-border"><span className="text-label font-semibold text-[#64748B] uppercase">Scenario Results</span></div>
                            <div className="divide-y divide-border">
                                {result.scenarios.slice(0, 6).map((s: any, i: number) => (
                                    <div key={i} className="flex justify-between px-4 py-2 text-data">
                                        <span className="text-[#64748B] truncate mr-2">{s.scenario_name}</span>
                                        <span className={`font-bold font-mono ${s.default_probability_after > 0.5 ? 'text-danger-500' : 'text-[#B45309]'}`}>{(s.default_probability_after * 100).toFixed(1)}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

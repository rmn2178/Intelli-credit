'use client';
import { useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const REGIMES = [
    { id: 'RBI Framework 2022', label: 'RBI 2022', desc: 'Historical framework' },
    { id: 'RBI Framework 2024', label: 'RBI 2024', desc: 'Current active' },
    { id: 'Future Simulated', label: 'Future Regime', desc: 'Projected stricter norms' },
];

export default function RegulatoryPage() {
    const [selected, setSelected] = useState('RBI Framework 2024');
    const [results, setResults] = useState<any>(null);
    const [comparison, setComparison] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const checkCompliance = async (regime: string) => {
        const sid = localStorage.getItem('session_id'); if (!sid) return;
        setSelected(regime); setLoading(true);
        try { setResults(await (await fetch(`${API}/api/sessions/${sid}/regulatory`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ regime }) })).json()); } catch (err) { console.error(err); }
        setLoading(false);
    };

    const compareAll = async () => {
        const sid = localStorage.getItem('session_id'); if (!sid) return; setLoading(true);
        try { setComparison(await (await fetch(`${API}/api/sessions/${sid}/regulatory/compare`)).json()); } catch (err) { console.error(err); }
        setLoading(false);
    };

    return (
        <div className="p-6 max-w-[960px]">
            <div className="mb-4">
                <h1 className="text-title font-bold text-navy-500">Regulatory Constitution</h1>
                <p className="text-data text-[#94A3B8]">Constitutional AI compliance engine — toggle between RBI policy regimes</p>
            </div>

            <div className="card mb-4">
                <table className="w-full text-data">
                    <thead><tr className="border-b border-border text-left">
                        <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Regime</th>
                        <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Description</th>
                        <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase w-[80px]">Action</th>
                    </tr></thead>
                    <tbody className="divide-y divide-border">
                        {REGIMES.map(r => (
                            <tr key={r.id} className={selected === r.id ? 'bg-[#F8FAFC]' : ''}>
                                <td className="px-4 py-2 font-medium text-[#334155]">{r.label} {selected === r.id && <span className="badge-gold">Active</span>}</td>
                                <td className="px-4 py-2 text-[#64748B]">{r.desc}</td>
                                <td className="px-4 py-2"><button onClick={() => checkCompliance(r.id)} className="btn-secondary text-[11px] py-[4px] px-[8px]">Check</button></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <button onClick={compareAll} disabled={loading} className="btn-primary w-full mb-4">{loading ? 'Checking...' : 'Compare All Regimes'}</button>

            {results && (
                <div className="card mb-4">
                    <div className="flex items-center justify-between px-4 py-2 border-b border-border">
                        <span className="text-body font-semibold text-[#334155]">{results.regime}</span>
                        <span className={results.overall_status === 'COMPLIANT' ? 'badge-pass' : results.overall_status === 'CONDITIONAL' ? 'badge-warn' : 'badge-fail'}>{results.overall_status}</span>
                    </div>
                    <div className="flex gap-4 px-4 py-2 border-b border-border text-data">
                        <span className="text-emerald-600 font-semibold">{results.passed} Passed</span>
                        <span className="text-[#B45309] font-semibold">{results.warnings} Warnings</span>
                        <span className="text-danger-500 font-semibold">{results.failed} Failed</span>
                    </div>
                    <div className="divide-y divide-border">
                        {results.checks?.map((c: any, i: number) => (
                            <div key={i} className="flex items-start gap-3 px-4 py-2">
                                <span className={`mt-[2px] ${c.status === 'PASS' ? 'badge-pass' : c.status === 'FAIL' ? 'badge-fail' : 'badge-warn'}`}>{c.status}</span>
                                <div>
                                    <p className="text-body font-medium text-[#334155]">{c.rule}</p>
                                    <p className="text-data text-[#94A3B8]">{c.detail}</p>
                                    {c.reference && <p className="text-[10px] text-[#CBD5E1]">{c.reference}</p>}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {comparison && (
                <div className="card">
                    <div className="px-4 py-2 border-b border-border"><span className="text-label font-semibold text-[#64748B] uppercase">Regime Comparison</span></div>
                    <div className="grid grid-cols-3 divide-x divide-border">
                        {Object.entries(comparison).map(([regime, data]: [string, any]) => (
                            <div key={regime} className="px-4 py-3 text-center">
                                <p className="text-body font-semibold text-[#334155] mb-1">{regime.replace('RBI Framework ', '')}</p>
                                <span className={data.overall_status === 'COMPLIANT' ? 'badge-pass' : data.overall_status === 'CONDITIONAL' ? 'badge-warn' : 'badge-fail'}>{data.overall_status}</span>
                                <p className="text-[10px] text-[#94A3B8] mt-2">{data.passed}P · {data.warnings}W · {data.failed}F</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

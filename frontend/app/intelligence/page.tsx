'use client';
import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function IntelligencePage() {
    const [data, setData] = useState<any>(null);
    useEffect(() => { const sid = localStorage.getItem('session_id'); if (!sid) return; fetch(`${API}/api/sessions/${sid}/results`).then(r => r.json()).then(setData).catch(console.error); }, []);

    const fraud = data?.fraud_report || {};
    const evidence = data?.evidence || {};
    const graph = fraud?.graph_summary || { nodes: [], edges: [] };

    return (
        <div className="p-6">
            <div className="mb-4">
                <h1 className="text-title font-bold text-navy-500">Intelligence Hub</h1>
                <p className="text-data text-[#94A3B8]">Federated intelligence, relational graph analysis, and systemic risk patterns</p>
            </div>

            {/* Stats */}
            <div className="card mb-4">
                <div className="grid grid-cols-4 divide-x divide-border">
                    {[
                        { label: 'Fraud Score', value: `${((fraud.fraud_probability || 0) * 100).toFixed(0)}%`, badge: 'grounded' },
                        { label: 'Signals', value: fraud.total_signals || 0, badge: 'verified' },
                        { label: 'Graph Nodes', value: graph.nodes?.length || 0, badge: 'verified' },
                        { label: 'Evidence Flags', value: (evidence.red?.length || 0) + (evidence.yellow?.length || 0), badge: 'grounded' },
                    ].map((s) => (
                        <div key={s.label} className="px-4 py-3 text-center">
                            <p className="text-[24px] font-bold text-navy-500 font-mono leading-none">{s.value}<span className={`micro-badge micro-badge-${s.badge}`}>{s.badge === 'grounded' ? 'G' : 'V'}</span></p>
                            <p className="text-label text-[#94A3B8] uppercase mt-1">{s.label}</p>
                        </div>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                {/* Fraud Signals */}
                <div className="card">
                    <div className="px-4 py-2 border-b border-border"><span className="text-label font-semibold text-[#64748B] uppercase">Fraud Radar Signals</span></div>
                    {fraud.all_signals?.length > 0 ? (
                        <div className="divide-y divide-border">
                            {fraud.all_signals.map((s: any, i: number) => (
                                <div key={i} className="px-4 py-2">
                                    <p className="text-data font-semibold text-danger-500 uppercase">{s.type?.replace(/_/g, ' ')}</p>
                                    <p className="text-data text-[#64748B] mt-[2px]">{s.description}</p>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="px-4 py-6 text-center"><span className="badge-pass">No Signals Detected</span></div>
                    )}
                </div>

                {/* Evidence */}
                <div className="card">
                    <div className="px-4 py-2 border-b border-border"><span className="text-label font-semibold text-[#64748B] uppercase">Evidence Classification</span></div>
                    <div className="divide-y divide-border">
                        {[{ key: 'red', badge: 'badge-fail' }, { key: 'yellow', badge: 'badge-warn' }, { key: 'green', badge: 'badge-pass' }].map(({ key, badge }) => (
                            <div key={key} className="px-4 py-2">
                                <div className="flex items-center gap-2 mb-1"><span className={badge}>{key.toUpperCase()}</span><span className="text-[10px] text-[#94A3B8] font-mono">{evidence[key]?.length || 0} items</span></div>
                                {evidence[key]?.slice(0, 2).map((e: any, i: number) => (<p key={i} className="text-[11px] text-[#64748B] ml-2">• {e.summary?.slice(0, 100)}</p>))}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Knowledge Graph */}
            <div className="card mt-4">
                <div className="px-4 py-2 border-b border-border"><span className="text-label font-semibold text-[#64748B] uppercase">Financial Knowledge Graph</span></div>
                <div className="grid grid-cols-2 divide-x divide-border">
                    <div>
                        <div className="px-4 py-2 border-b border-border"><span className="text-[10px] text-[#94A3B8] uppercase font-semibold">Entities ({graph.nodes?.length || 0})</span></div>
                        <div className="max-h-[200px] overflow-auto divide-y divide-border">
                            {graph.nodes?.map((n: any, i: number) => (
                                <div key={i} className="flex items-center gap-2 px-4 py-[4px] text-data">
                                    <span className="badge-info">{n.type}</span><span className="text-[#334155]">{n.id}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div>
                        <div className="px-4 py-2 border-b border-border"><span className="text-[10px] text-[#94A3B8] uppercase font-semibold">Relationships ({graph.edges?.length || 0})</span></div>
                        <div className="max-h-[200px] overflow-auto divide-y divide-border">
                            {graph.edges?.map((e: any, i: number) => (
                                <div key={i} className="px-4 py-[4px] text-data text-[#64748B]">
                                    <span className="text-[#334155] font-medium">{e.source}</span>
                                    <span className="text-[#94A3B8]"> → {e.relationship} → </span>
                                    <span className="text-[#334155] font-medium">{e.target}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

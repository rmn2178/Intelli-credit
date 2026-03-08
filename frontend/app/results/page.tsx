'use client';
import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ResultsPage() {
    const [data, setData] = useState<any>(null);
    const [tab, setTab] = useState('decision');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const sid = localStorage.getItem('session_id');
        if (!sid) { setLoading(false); return; }
        fetch(`${API}/api/sessions/${sid}/results`)
            .then(r => r.json())
            .then(d => { setData(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, []);

    if (loading) return <div className="p-6 text-data text-[#94A3B8]">Loading results...</div>;
    if (!data) return <div className="p-6 text-data text-[#94A3B8]">No results available. Run processing first.</div>;

    const decision = data.credit_decision || {};
    const calcs = data.calculations || {};
    const cam = data.cam_report || {};
    const debate = data.committee_debate || {};
    const evidence = data.evidence || {};
    const forensic = data.forensic_audit || {};
    const checkpoints = forensic.audit_scores || [];
    const camFiveCs = forensic.cam_five_cs || cam;

    const sessionId = typeof window !== 'undefined' ? localStorage.getItem('session_id') : null;
    const tierColor = (t: string) => t === 'Score_3' ? 'text-emerald-600' : t === 'Score_2' ? 'text-[#B45309]' : 'text-danger-500';
    const tierBg = (t: string) => t === 'Score_3' ? 'badge-pass' : t === 'Score_2' ? 'badge-warn' : 'badge-fail';

    const TABS = ['decision', 'forensic', 'cam', 'committee', 'ratios', 'evidence'];
    const TAB_LABELS: Record<string, string> = {
        decision: 'Decision', forensic: 'Forensic Audit', cam: 'CAM Report',
        committee: 'Committee', ratios: 'Financial Ratios', evidence: 'Evidence Trail'
    };

    return (
        <div className="p-6">
            <div className="mb-4">
                <h1 className="text-title font-bold text-navy-500">Credit Decision & CAM</h1>
                <p className="text-data text-[#94A3B8]">{decision.borrower || 'Borrower'}</p>
            </div>

            {/* Decision Card */}
            <div className={`card mb-4 border-l-[3px] ${decision.decision === 'APPROVED' ? 'border-l-emerald-500' :
                    decision.decision === 'REJECTED' ? 'border-l-danger-500' :
                        decision.decision === 'Approve' ? 'border-l-emerald-500' :
                            decision.decision === 'Reject' ? 'border-l-danger-500' : 'border-l-[#B45309]'
                }`}>
                <div className="grid grid-cols-5 divide-x divide-border">
                    {[
                        { label: 'Decision', value: decision.decision || 'PENDING', color: decision.decision === 'APPROVED' || decision.decision === 'Approve' ? 'text-emerald-600' : decision.decision === 'REJECTED' || decision.decision === 'Reject' ? 'text-danger-500' : 'text-[#B45309]' },
                        { label: 'Score', value: `${decision.risk_score || 0}/300`, color: 'text-navy-500' },
                        { label: 'Risk Grade', value: decision.risk_grade || '—', color: 'text-[#B45309]' },
                        { label: 'Loan Limit', value: decision.loan_limit || '—', color: 'text-navy-500' },
                        { label: 'Rate / Tenure', value: `${decision.interest_rate || '—'} / ${decision.tenure || '—'}`, color: 'text-[#64748B]' },
                    ].map(m => (
                        <div key={m.label} className="px-4 py-3 text-center">
                            <p className={`text-heading font-bold font-mono ${m.color}`}>{m.value}</p>
                            <p className="text-label text-[#94A3B8] uppercase mt-1">{m.label}</p>
                        </div>
                    ))}
                </div>
                {decision.reason && (
                    <div className="px-4 py-2 border-t border-border text-data text-[#64748B]">
                        <strong>Reason:</strong> {decision.reason}
                    </div>
                )}
            </div>

            {/* Tabs */}
            <div className="flex border-b border-border mb-4">
                {TABS.map(t => (
                    <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 text-body font-medium border-b-[2px] -mb-[1px] ${tab === t ? 'border-navy-500 text-navy-500' : 'border-transparent text-[#94A3B8]'}`}>{TAB_LABELS[t]}</button>
                ))}
            </div>

            {/* Decision Tab */}
            {tab === 'decision' && (
                <div className="grid grid-cols-2 gap-4">
                    <div className="card">
                        <div className="px-4 py-2 border-b border-border"><span className="text-label font-semibold text-[#64748B] uppercase">Evidence Summary</span></div>
                        <div className="divide-y divide-border">
                            {[{ key: 'green', badge: 'badge-pass' }, { key: 'yellow', badge: 'badge-warn' }, { key: 'red', badge: 'badge-fail' }].map(({ key, badge }) => (
                                <div key={key} className="px-4 py-2">
                                    <div className="flex items-center gap-2 mb-1"><span className={badge}>{key.toUpperCase()} ({evidence[key]?.length || 0})</span></div>
                                    {evidence[key]?.slice(0, 3).map((e: any, i: number) => (<p key={i} className="text-[11px] text-[#64748B] ml-2">• {e.summary?.slice(0, 140)}</p>))}
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="card">
                        <div className="px-4 py-2 border-b border-border"><span className="text-label font-semibold text-[#64748B] uppercase">Forensic Audit Summary</span></div>
                        <div className="divide-y divide-border">
                            <div className="px-4 py-3 flex justify-between">
                                <span className="text-body text-[#64748B]">Aggregate Score</span>
                                <span className="font-bold font-mono text-navy-500">{forensic.aggregate_score || 0}/300</span>
                            </div>
                            <div className="px-4 py-3 flex justify-between">
                                <span className="text-body text-[#64748B]">Risk Grade</span>
                                <span className={`font-bold ${forensic.risk_grade === 'Prime Borrower' || forensic.risk_grade === 'Strong Borrower' ? 'text-emerald-600' : 'text-[#B45309]'}`}>
                                    {forensic.risk_grade || '—'}
                                </span>
                            </div>
                            <div className="px-4 py-3 flex justify-between">
                                <span className="text-body text-[#64748B]">Checkpoints Passed</span>
                                <span className="font-bold font-mono text-navy-500">{checkpoints.filter((c: any) => c.score_tier === 'Score_3').length}/{checkpoints.length}</span>
                            </div>
                            <div className="px-4 py-3 flex justify-between">
                                <span className="text-body text-[#64748B]">Hard Veto</span>
                                <span className={`font-bold ${forensic.vetoed ? 'text-danger-500' : 'text-emerald-600'}`}>
                                    {forensic.vetoed ? 'TRIGGERED' : 'CLEAR'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Forensic Audit Tab */}
            {tab === 'forensic' && (
                <div className="card">
                    <div className="px-4 py-2 border-b border-border flex items-center justify-between">
                        <span className="text-label font-semibold text-[#64748B] uppercase">
                            30-Checkpoint Forensic Audit Results
                        </span>
                        <span className="font-mono text-data text-navy-500 font-bold">
                            Total: {forensic.aggregate_score || 0}/300 — {forensic.risk_grade || 'Pending'}
                        </span>
                    </div>
                    <table className="w-full text-data">
                        <thead><tr className="border-b border-border text-left">
                            <th className="px-3 py-2 text-label font-semibold text-[#64748B] uppercase w-[40px]">ID</th>
                            <th className="px-3 py-2 text-label font-semibold text-[#64748B] uppercase w-[60px]">Cat</th>
                            <th className="px-3 py-2 text-label font-semibold text-[#64748B] uppercase">Checkpoint</th>
                            <th className="px-3 py-2 text-label font-semibold text-[#64748B] uppercase">Result</th>
                            <th className="px-3 py-2 text-label font-semibold text-[#64748B] uppercase w-[90px]">Score</th>
                            <th className="px-3 py-2 text-label font-semibold text-[#64748B] uppercase w-[50px]">Pts</th>
                        </tr></thead>
                        <tbody className="divide-y divide-border">
                            {checkpoints.map((cp: any) => (
                                <tr key={cp.id} className={cp.is_veto ? 'bg-[#FEF2F2]' : ''}>
                                    <td className="px-3 py-2 font-mono text-[#94A3B8]">{String(cp.id).padStart(2, '0')}</td>
                                    <td className="px-3 py-2"><span className="badge-info">{cp.cat}</span></td>
                                    <td className="px-3 py-2 font-medium text-[#334155]">
                                        {cp.name}
                                        {cp.is_veto && <span className="badge-fail ml-2">VETO</span>}
                                    </td>
                                    <td className="px-3 py-2 text-[#64748B] font-mono">{cp.result_label}</td>
                                    <td className="px-3 py-2">
                                        <span className={tierBg(cp.score_tier)}>{cp.score_tier?.replace('Score_', 'Score ')}</span>
                                    </td>
                                    <td className={`px-3 py-2 font-bold font-mono ${tierColor(cp.score_tier)}`}>{cp.score_points}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* CAM Report Tab */}
            {tab === 'cam' && (
                <div className="card">
                    <div className="px-4 py-2 border-b border-border flex items-center justify-between">
                        <span className="text-label font-semibold text-[#64748B] uppercase">Credit Appraisal Memorandum — Five Cs</span>
                        <div className="flex gap-2">
                            {sessionId && (
                                <>
                                    <a href={`${API}/api/sessions/${sessionId}/download-cam?format=pdf`} className="btn-primary text-[11px] py-[4px] px-[10px]" download>↓ PDF</a>
                                    <a href={`${API}/api/sessions/${sessionId}/download-cam?format=docx`} className="btn-secondary text-[11px] py-[4px] px-[10px]" download>↓ DOCX</a>
                                </>
                            )}
                        </div>
                    </div>
                    {/* Five Cs summary */}
                    {camFiveCs.five_cs_summary && (
                        <div className="grid grid-cols-5 divide-x divide-border border-b border-border">
                            {Object.entries(camFiveCs.five_cs_summary).map(([key, val]: [string, any]) => (
                                <div key={key} className="px-3 py-3 text-center">
                                    <p className="text-body font-bold text-navy-500">{val}</p>
                                    <p className="text-label text-[#94A3B8] uppercase mt-1">{key}</p>
                                </div>
                            ))}
                        </div>
                    )}
                    <div className="px-4 py-4 text-body text-[#334155] whitespace-pre-wrap leading-relaxed">
                        {camFiveCs.full_narrative || cam.full_narrative || 'CAM report not yet generated.'}
                    </div>
                </div>
            )}

            {/* Committee Tab */}
            {tab === 'committee' && (
                <div className="card">
                    <div className="px-4 py-2 border-b border-border"><span className="text-label font-semibold text-[#64748B] uppercase">Credit Committee Deliberation</span></div>
                    <div className="px-4 py-2 border-b border-border bg-[#F8FAFC]"><span className="text-body font-semibold text-navy-500">Final Decision: {debate.final_decision || 'Pending'}</span></div>
                    <div className="divide-y divide-border">
                        {debate.personas?.map((p: any, i: number) => (
                            <div key={i} className="px-4 py-3"><p className="text-body font-semibold text-[#334155] mb-1">{p.role}</p><p className="text-data text-[#64748B] whitespace-pre-wrap">{p.opinion}</p></div>
                        ))}
                    </div>
                    {debate.decision_narrative && (<div className="px-4 py-3 border-t border-border bg-emerald-50"><p className="text-body font-semibold text-emerald-700 mb-1">Consensus</p><p className="text-data text-[#64748B] whitespace-pre-wrap">{debate.decision_narrative}</p></div>)}
                </div>
            )}

            {/* Financial Ratios Tab */}
            {tab === 'ratios' && (
                <div className="card">
                    <table className="w-full text-data">
                        <thead><tr className="border-b border-border text-left">
                            <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Ratio</th>
                            <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Value</th>
                            <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Formula</th>
                            <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Status</th>
                        </tr></thead>
                        <tbody className="divide-y divide-border">
                            {Object.entries(calcs).map(([key, info]: [string, any]) => (
                                <tr key={key}>
                                    <td className="px-4 py-2 font-medium text-[#334155]">{key.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}</td>
                                    <td className="px-4 py-2 font-bold font-mono text-navy-500">{info.value}{info.unit || ''}</td>
                                    <td className="px-4 py-2 text-[#94A3B8] font-mono text-[10px]">{info.formula}</td>
                                    <td className="px-4 py-2"><span className={info.status === 'GREEN' ? 'badge-pass' : info.status === 'RED' ? 'badge-fail' : 'badge-warn'}>{info.status}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Evidence Trail Tab */}
            {tab === 'evidence' && (
                <div className="card">
                    <div className="divide-y divide-border">
                        {['red', 'yellow', 'green'].map(sev => (
                            evidence[sev]?.map((e: any, i: number) => (
                                <div key={`${sev}-${i}`} className={`px-4 py-2 border-l-[3px] ${sev === 'red' ? 'border-l-danger-500' : sev === 'yellow' ? 'border-l-[#D97706]' : 'border-l-emerald-500'}`}>
                                    <div className="flex items-center gap-2 mb-[2px]"><span className={sev === 'red' ? 'badge-fail' : sev === 'yellow' ? 'badge-warn' : 'badge-pass'}>{sev.toUpperCase()}</span><span className="text-[10px] text-[#94A3B8]">{e.variable}</span></div>
                                    <p className="text-body text-[#334155]">{e.summary}</p>
                                    {e.formula && <p className="text-[10px] text-[#94A3B8] font-mono mt-[2px]">{e.formula}</p>}
                                    {e.sources && <p className="text-[10px] text-[#CBD5E1]">Sources: {e.sources.join(', ')}</p>}
                                </div>
                            ))
                        ))}
                    </div>
                </div>
            )}

            {/* JSON */}
            <div className="card mt-4">
                <div className="px-4 py-2 border-b border-border"><span className="text-label font-semibold text-[#64748B] uppercase">Structured Decision Output</span></div>
                <pre className="px-4 py-3 text-[11px] font-mono text-navy-500 overflow-auto max-h-[200px]">{JSON.stringify({
                    borrower: decision.borrower,
                    risk_score: decision.risk_score,
                    max_score: 300,
                    risk_grade: decision.risk_grade,
                    decision: decision.decision,
                    loan_limit: decision.loan_limit,
                    interest_rate: decision.interest_rate,
                    tenure: decision.tenure,
                    vetoed: decision.vetoed,
                }, null, 2)}</pre>
            </div>
        </div>
    );
}

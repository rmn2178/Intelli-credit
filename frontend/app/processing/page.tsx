'use client';
import { useState, useEffect, useRef } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const STAGES = ['Extraction', 'Qualitative', 'Evidence', 'Financial', 'GST Recon', 'Fraud Radar', 'OSINT', 'CAM', 'Committee'];
const STAGE_IDS = ['ocr', 'unstructured', 'evidence', 'financial', 'gst', 'fraud', 'osint', 'cam', 'committee'];

export default function ProcessingPage() {
    const [logs, setLogs] = useState<{ stage: string; message: string; ts: string }[]>([]);
    const [activeStage, setActiveStage] = useState('');
    const [completedStages, setCompletedStages] = useState<string[]>([]);
    const [decision, setDecision] = useState<any>(null);
    const [running, setRunning] = useState(false);
    const logRef = useRef<HTMLDivElement>(null);

    const startProcessing = () => {
        const sessionId = localStorage.getItem('session_id');
        if (!sessionId) return;
        setRunning(true); setLogs([]);
        const es = new EventSource(`${API}/api/sessions/${sessionId}/process`);
        es.addEventListener('stage', (e) => { const d = JSON.parse(e.data); if (d.status === 'running') setActiveStage(d.stage); if (d.status === 'complete') setCompletedStages(prev => [...prev, d.stage]); });
        [...STAGE_IDS, 'verification'].forEach(evt => {
            es.addEventListener(evt, (e) => { const d = JSON.parse(e.data); setLogs(prev => [...prev, { stage: evt, message: d.message, ts: new Date().toISOString().split('T')[1].slice(0, 8) }]); });
        });
        es.addEventListener('decision', (e) => setDecision(JSON.parse(e.data)));
        es.addEventListener('complete', () => { es.close(); setRunning(false); });
        es.onerror = () => { es.close(); setRunning(false); };
    };

    useEffect(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight; }, [logs]);

    const progress = completedStages.length;

    return (
        <div className="p-6">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h1 className="text-title font-bold text-navy-500">AI Processing Pipeline</h1>
                    <p className="text-data text-[#94A3B8]">9-stage autonomous analysis — {progress}/9 complete</p>
                </div>
                {!running && !decision && <button onClick={startProcessing} className="btn-primary">Start Analysis</button>}
            </div>

            {/* Stage Table */}
            <div className="card mb-4">
                <table className="w-full text-data">
                    <thead><tr className="border-b border-border text-left">
                        <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase w-[32px]">#</th>
                        <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Stage</th>
                        <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase w-[100px]">Status</th>
                    </tr></thead>
                    <tbody className="divide-y divide-border">
                        {STAGES.map((s, i) => {
                            const id = STAGE_IDS[i];
                            const isComplete = completedStages.includes(id);
                            const isActive = activeStage === id && !isComplete;
                            return (
                                <tr key={id}>
                                    <td className="px-4 py-2 font-mono text-[#94A3B8]">{String(i + 1).padStart(2, '0')}</td>
                                    <td className="px-4 py-2 font-medium text-[#334155]">{s}</td>
                                    <td className="px-4 py-2">
                                        {isComplete ? <span className="badge-pass">Complete</span> :
                                            isActive ? <span className="badge-gold">Running</span> :
                                                <span className="badge-info">Queued</span>}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Reasoning Trace */}
            <div className="card">
                <div className="flex items-center justify-between px-4 py-2 border-b border-border">
                    <div className="flex items-center gap-2">
                        <div className={`w-[5px] h-[5px] ${running ? 'bg-emerald-500' : 'bg-[#CBD5E1]'}`} />
                        <span className="text-label font-semibold text-[#64748B] uppercase">Reasoning Trace</span>
                    </div>
                    <span className="text-[10px] text-[#94A3B8] font-mono">{logs.length} entries</span>
                </div>
                <div ref={logRef} className="h-[360px] overflow-y-auto font-mono text-data">
                    {logs.map((log, i) => (
                        <div key={i} className="flex gap-0 border-b border-border hover:bg-[#F8FAFC]">
                            <span className="text-[#CBD5E1] w-[64px] shrink-0 px-3 py-[4px] border-r border-border text-right">{log.ts}</span>
                            <span className="text-[#94A3B8] w-[80px] shrink-0 px-3 py-[4px] border-r border-border uppercase font-semibold text-[10px]">{log.stage}</span>
                            <span className="text-[#334155] px-3 py-[4px] whitespace-pre-wrap">{log.message}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Decision */}
            {decision && (
                <div className="card mt-4 border-l-[3px] border-l-emerald-500">
                    <div className="px-4 py-2 border-b border-border">
                        <span className="text-label font-semibold text-[#64748B] uppercase">Credit Decision</span>
                    </div>
                    <div className="grid grid-cols-4 divide-x divide-border">
                        {[
                            { label: 'Decision', value: decision.decision, color: 'text-navy-500' },
                            { label: 'Risk Score', value: `${(decision.risk_score * 100).toFixed(0)}%`, color: 'text-[#B45309]' },
                            { label: 'Fraud Score', value: `${(decision.fraud_score * 100).toFixed(0)}%`, color: 'text-danger-500' },
                            { label: 'Confidence', value: `${(decision.confidence * 100).toFixed(0)}%`, color: 'text-emerald-600' },
                        ].map(m => (
                            <div key={m.label} className="px-4 py-3 text-center">
                                <p className={`text-heading font-bold ${m.color}`}>{m.value}<span className="micro-badge micro-badge-grounded">Grounded</span></p>
                                <p className="text-label text-[#94A3B8] uppercase mt-1">{m.label}</p>
                            </div>
                        ))}
                    </div>
                    <div className="px-4 py-2 border-t border-border">
                        <a href="/results" className="text-body font-semibold text-navy-500 hover:underline">View Full Results & CAM Report →</a>
                    </div>
                </div>
            )}
        </div>
    );
}

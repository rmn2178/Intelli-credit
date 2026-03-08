'use client';
import { useState, useEffect, useRef } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const STAGES = [
    'Extraction', 'Qualitative', 'Evidence', 'Financial', 'GST Recon',
    'Fraud Radar', 'OSINT', 'Forensic Audit', 'CAM Report', 'Committee'
];
const STAGE_IDS = [
    'ocr', 'unstructured', 'evidence', 'financial', 'gst',
    'fraud', 'osint', 'forensic', 'cam', 'committee'
];

interface CheckpointResult {
    checkpoint_id: number;
    checkpoint_name: string;
    category: string;
    formula: string;
    result_value: any;
    result_label: string;
    score_tier: string;
    score_points: number;
    is_veto: boolean;
    data_missing: boolean;
    progress: number;
    message: string;
}

export default function ProcessingPage() {
    const [logs, setLogs] = useState<{ stage: string; message: string; ts: string }[]>([]);
    const [activeStage, setActiveStage] = useState('');
    const [completedStages, setCompletedStages] = useState<string[]>([]);
    const [decision, setDecision] = useState<any>(null);
    const [running, setRunning] = useState(false);
    const [checkpoints, setCheckpoints] = useState<CheckpointResult[]>([]);
    const [forensicProgress, setForensicProgress] = useState(0);
    const [vetoAlert, setVetoAlert] = useState<any>(null);
    const [forensicComplete, setForensicComplete] = useState<any>(null);
    const [camReport, setCamReport] = useState<any>(null);
    const logRef = useRef<HTMLDivElement>(null);

    const startProcessing = () => {
        const sessionId = localStorage.getItem('session_id');
        if (!sessionId) return;
        setRunning(true); setLogs([]); setCheckpoints([]); setForensicProgress(0);
        setVetoAlert(null); setForensicComplete(null); setCamReport(null); setDecision(null);
        setCompletedStages([]);

        const es = new EventSource(`${API}/api/sessions/${sessionId}/process`);

        es.addEventListener('stage', (e) => {
            const d = JSON.parse(e.data);
            if (d.status === 'running') setActiveStage(d.stage);
            if (d.status === 'complete') setCompletedStages(prev => [...prev, d.stage]);
        });

        // Existing stage events
        [...STAGE_IDS, 'verification'].forEach(evt => {
            if (evt === 'forensic') return; // handled separately
            es.addEventListener(evt, (e) => {
                const d = JSON.parse(e.data);
                if (d.message) {
                    setLogs(prev => [...prev, {
                        stage: evt, message: d.message,
                        ts: new Date().toISOString().split('T')[1].slice(0, 8)
                    }]);
                }
            });
        });

        // Forensic checkpoint events
        es.addEventListener('forensic', (e) => {
            const d = JSON.parse(e.data);
            if (d.checkpoint_id) {
                setCheckpoints(prev => [...prev, d as CheckpointResult]);
                setForensicProgress(d.progress || 0);
            }
            if (d.message) {
                setLogs(prev => [...prev, {
                    stage: 'forensic', message: d.message,
                    ts: new Date().toISOString().split('T')[1].slice(0, 8)
                }]);
            }
        });

        es.addEventListener('forensic_veto', (e) => {
            const d = JSON.parse(e.data);
            setVetoAlert(d);
            setLogs(prev => [...prev, {
                stage: 'VETO', message: d.message,
                ts: new Date().toISOString().split('T')[1].slice(0, 8)
            }]);
        });

        es.addEventListener('forensic_complete', (e) => {
            const d = JSON.parse(e.data);
            setForensicComplete(d);
            setForensicProgress(100);
            setLogs(prev => [...prev, {
                stage: 'forensic', message: d.message,
                ts: new Date().toISOString().split('T')[1].slice(0, 8)
            }]);
        });

        es.addEventListener('cam', (e) => {
            const d = JSON.parse(e.data);
            if (d.report) setCamReport(d.report);
            if (d.message) {
                setLogs(prev => [...prev, {
                    stage: 'cam', message: d.message,
                    ts: new Date().toISOString().split('T')[1].slice(0, 8)
                }]);
            }
        });

        es.addEventListener('decision', (e) => setDecision(JSON.parse(e.data)));
        es.addEventListener('complete', () => { es.close(); setRunning(false); });
        es.onerror = () => { es.close(); setRunning(false); };
    };

    useEffect(() => {
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
    }, [logs]);

    const sessionId = typeof window !== 'undefined' ? localStorage.getItem('session_id') : null;
    const stageProgress = completedStages.length;
    const tierColor = (t: string) => t === 'Score_3' ? 'text-emerald-600' : t === 'Score_2' ? 'text-[#B45309]' : 'text-danger-500';
    const tierBg = (t: string) => t === 'Score_3' ? 'badge-pass' : t === 'Score_2' ? 'badge-warn' : 'badge-fail';

    return (
        <div className="p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h1 className="text-title font-bold text-navy-500">Forensic Credit Audit Engine</h1>
                    <p className="text-data text-[#94A3B8]">
                        30-checkpoint forensic validation — {stageProgress}/{STAGES.length} stages complete
                    </p>
                </div>
                {!running && !decision && (
                    <button onClick={startProcessing} className="btn-primary" id="start-analysis-btn">
                        Start Forensic Audit
                    </button>
                )}
            </div>

            {/* Forensic Audit Progress Bar */}
            {running && activeStage === 'forensic' && (
                <div className="mb-4">
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-label font-semibold text-[#64748B] uppercase">
                            Forensic Audit Progress
                        </span>
                        <span className="text-data font-mono text-navy-500">
                            {checkpoints.length}/30 checkpoints
                        </span>
                    </div>
                    <div className="w-full h-[4px] bg-border">
                        <div
                            className="h-full bg-navy-500 transition-all duration-300"
                            style={{ width: `${forensicProgress}%` }}
                        />
                    </div>
                </div>
            )}

            {/* Hard Veto Alert */}
            {vetoAlert && (
                <div className="card mb-4 border-l-[4px] border-l-danger-500 bg-[#FEF2F2]" id="veto-alert">
                    <div className="px-4 py-3 flex items-center gap-3">
                        <span className="text-[24px]">⚠</span>
                        <div>
                            <p className="text-body font-bold text-[#991B1B]">HARD VETO — Loan Rejected</p>
                            <p className="text-data text-[#991B1B]">{vetoAlert.message}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Aggregate Score Card */}
            {forensicComplete && (
                <div className={`card mb-4 border-l-[3px] ${forensicComplete.vetoed ? 'border-l-danger-500' :
                        forensicComplete.risk_grade === 'Prime Borrower' ? 'border-l-emerald-500' :
                            forensicComplete.risk_grade === 'Strong Borrower' ? 'border-l-emerald-500' :
                                forensicComplete.risk_grade === 'Moderate Risk' ? 'border-l-[#B45309]' :
                                    'border-l-danger-500'
                    }`} id="aggregate-score">
                    <div className="grid grid-cols-5 divide-x divide-border">
                        <div className="px-4 py-3 text-center">
                            <p className="text-heading font-bold font-mono text-navy-500">
                                {forensicComplete.aggregate_score}
                                <span className="text-data text-[#94A3B8] font-normal">/300</span>
                            </p>
                            <p className="text-label text-[#94A3B8] uppercase mt-1">Aggregate Score</p>
                        </div>
                        <div className="px-4 py-3 text-center">
                            <p className={`text-heading font-bold ${forensicComplete.risk_grade === 'Prime Borrower' ? 'text-emerald-600' :
                                    forensicComplete.risk_grade === 'Strong Borrower' ? 'text-emerald-600' :
                                        forensicComplete.risk_grade === 'Moderate Risk' ? 'text-[#B45309]' :
                                            'text-danger-500'
                                }`}>{forensicComplete.risk_grade}</p>
                            <p className="text-label text-[#94A3B8] uppercase mt-1">Risk Grade</p>
                        </div>
                        <div className="px-4 py-3 text-center">
                            <p className="text-heading font-bold font-mono text-navy-500">
                                {forensicComplete.checkpoints_completed}
                                <span className="text-data text-[#94A3B8] font-normal">/30</span>
                            </p>
                            <p className="text-label text-[#94A3B8] uppercase mt-1">Checkpoints</p>
                        </div>
                        <div className="px-4 py-3 text-center">
                            <p className={`text-heading font-bold ${forensicComplete.vetoed ? 'text-danger-500' : 'text-emerald-600'}`}>
                                {forensicComplete.vetoed ? 'VETOED' : 'PASS'}
                            </p>
                            <p className="text-label text-[#94A3B8] uppercase mt-1">Fraud Check</p>
                        </div>
                        <div className="px-4 py-3 text-center">
                            <p className={`text-heading font-bold font-mono ${(forensicComplete.data_completeness_pct || 0) >= 80 ? 'text-emerald-600' :
                                    (forensicComplete.data_completeness_pct || 0) >= 50 ? 'text-[#B45309]' : 'text-danger-500'
                                }`}>
                                {forensicComplete.data_completeness_pct || 0}%
                            </p>
                            <p className="text-label text-[#94A3B8] uppercase mt-1">Data Quality</p>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-2 gap-4 mb-4">
                {/* Stage Table */}
                <div className="card">
                    <div className="px-4 py-2 border-b border-border">
                        <span className="text-label font-semibold text-[#64748B] uppercase">Processing Stages</span>
                    </div>
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
                                        <td className={`px-4 py-2 font-medium ${id === 'forensic' ? 'text-navy-500 font-semibold' : 'text-[#334155]'}`}>{s}</td>
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
                    <div ref={logRef} className="h-[320px] overflow-y-auto font-mono text-data">
                        {logs.map((log, i) => (
                            <div key={i} className={`flex gap-0 border-b border-border hover:bg-[#F8FAFC] ${log.stage === 'VETO' ? 'bg-[#FEF2F2]' : ''
                                }`}>
                                <span className="text-[#CBD5E1] w-[56px] shrink-0 px-2 py-[4px] border-r border-border text-right">{log.ts}</span>
                                <span className={`w-[70px] shrink-0 px-2 py-[4px] border-r border-border uppercase font-semibold text-[10px] ${log.stage === 'VETO' ? 'text-[#991B1B]' : 'text-[#94A3B8]'
                                    }`}>{log.stage}</span>
                                <span className={`px-2 py-[4px] whitespace-pre-wrap ${log.stage === 'VETO' ? 'text-[#991B1B] font-semibold' : 'text-[#334155]'
                                    }`}>{log.message}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* 30-Checkpoint Table */}
            {checkpoints.length > 0 && (
                <div className="card mb-4" id="checkpoint-table">
                    <div className="px-4 py-2 border-b border-border flex items-center justify-between">
                        <span className="text-label font-semibold text-[#64748B] uppercase">
                            Forensic Audit Checkpoints ({checkpoints.length}/30)
                        </span>
                        {forensicComplete && (
                            <span className="font-mono text-data text-navy-500 font-bold">
                                Total: {forensicComplete.aggregate_score}/300
                            </span>
                        )}
                    </div>
                    <div className="max-h-[400px] overflow-y-auto">
                        <table className="w-full text-data">
                            <thead><tr className="border-b border-border text-left sticky top-0 bg-white">
                                <th className="px-3 py-2 text-label font-semibold text-[#64748B] uppercase w-[40px]">ID</th>
                                <th className="px-3 py-2 text-label font-semibold text-[#64748B] uppercase w-[60px]">Cat</th>
                                <th className="px-3 py-2 text-label font-semibold text-[#64748B] uppercase">Checkpoint</th>
                                <th className="px-3 py-2 text-label font-semibold text-[#64748B] uppercase">Result</th>
                                <th className="px-3 py-2 text-label font-semibold text-[#64748B] uppercase w-[90px]">Score</th>
                                <th className="px-3 py-2 text-label font-semibold text-[#64748B] uppercase w-[50px]">Pts</th>
                            </tr></thead>
                            <tbody className="divide-y divide-border">
                                {checkpoints.map((cp) => (
                                    <tr key={cp.checkpoint_id} className={cp.is_veto ? 'bg-[#FEF2F2]' : cp.data_missing ? 'bg-[#FFFBEB]' : ''}>
                                        <td className="px-3 py-2 font-mono text-[#94A3B8]">{String(cp.checkpoint_id).padStart(2, '0')}</td>
                                        <td className="px-3 py-2"><span className="badge-info">{cp.category}</span></td>
                                        <td className="px-3 py-2 font-medium text-[#334155]">
                                            {cp.checkpoint_name}
                                            {cp.is_veto && <span className="badge-fail ml-2">VETO</span>}
                                            {cp.data_missing && !cp.is_veto && <span className="badge-warn ml-2">NO DATA</span>}
                                        </td>
                                        <td className="px-3 py-2 text-[#64748B] font-mono">{cp.result_label}</td>
                                        <td className="px-3 py-2">
                                            <span className={tierBg(cp.score_tier)}>{cp.score_tier.replace('Score_', 'Score ')}</span>
                                        </td>
                                        <td className={`px-3 py-2 font-bold font-mono ${tierColor(cp.score_tier)}`}>{cp.score_points}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* CAM Preview */}
            {camReport && (
                <div className="card mb-4" id="cam-preview">
                    <div className="px-4 py-2 border-b border-border flex items-center justify-between">
                        <span className="text-label font-semibold text-[#64748B] uppercase">
                            Credit Appraisal Memo — Five Cs
                        </span>
                        <div className="flex gap-2">
                            {sessionId && (
                                <>
                                    <a
                                        href={`${API}/api/sessions/${sessionId}/download-cam?format=pdf`}
                                        className="btn-primary text-[11px] py-[4px] px-[10px]"
                                        download
                                    >
                                        ↓ PDF
                                    </a>
                                    <a
                                        href={`${API}/api/sessions/${sessionId}/download-cam?format=docx`}
                                        className="btn-secondary text-[11px] py-[4px] px-[10px]"
                                        download
                                    >
                                        ↓ DOCX
                                    </a>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Five Cs Summary */}
                    <div className="grid grid-cols-5 divide-x divide-border border-b border-border">
                        {camReport.five_cs_summary && Object.entries(camReport.five_cs_summary).map(([key, val]: [string, any]) => (
                            <div key={key} className="px-3 py-3 text-center">
                                <p className="text-body font-bold text-navy-500">{val}</p>
                                <p className="text-label text-[#94A3B8] uppercase mt-1">{key}</p>
                            </div>
                        ))}
                    </div>

                    {/* Decision Row */}
                    {camReport.decision && (
                        <div className={`px-4 py-3 border-b border-border ${camReport.decision.status === 'APPROVED' ? 'bg-[#ECFDF5]' :
                            camReport.decision.status === 'REJECTED' ? 'bg-[#FEF2F2]' : 'bg-[#FFFBEB]'
                            }`}>
                            <div className="flex items-center justify-between">
                                <div>
                                    <span className={`text-body font-bold ${camReport.decision.status === 'APPROVED' ? 'text-emerald-700' :
                                        camReport.decision.status === 'REJECTED' ? 'text-[#991B1B]' : 'text-[#92400E]'
                                        }`}>
                                        Decision: {camReport.decision.status}
                                    </span>
                                    <span className="text-data text-[#64748B] ml-4">
                                        {camReport.decision.loan_limit} · {camReport.decision.interest_rate} · {camReport.decision.tenure}
                                    </span>
                                </div>
                                <span className="text-data text-[#64748B]">
                                    {camReport.decision.risk_grade} ({camReport.decision.aggregate_score}/300)
                                </span>
                            </div>
                            <p className="text-data text-[#64748B] mt-1">{camReport.decision.reason}</p>
                        </div>
                    )}

                    {/* Full Narrative */}
                    <div className="px-4 py-3">
                        <pre className="text-[11px] font-mono text-[#334155] whitespace-pre-wrap leading-relaxed max-h-[300px] overflow-y-auto">
                            {camReport.full_narrative || 'Generating...'}
                        </pre>
                    </div>
                </div>
            )}

            {/* Final Decision Card */}
            {decision && (
                <div className={`card mt-4 border-l-[3px] ${decision.vetoed ? 'border-l-danger-500' :
                    decision.decision === 'APPROVED' ? 'border-l-emerald-500' :
                        decision.decision === 'REJECTED' ? 'border-l-danger-500' : 'border-l-[#B45309]'
                    }`} id="final-decision">
                    <div className="px-4 py-2 border-b border-border">
                        <span className="text-label font-semibold text-[#64748B] uppercase">Final Credit Decision</span>
                    </div>
                    <div className="grid grid-cols-5 divide-x divide-border">
                        {[
                            { label: 'Decision', value: decision.decision, color: decision.decision === 'APPROVED' ? 'text-emerald-600' : decision.decision === 'REJECTED' ? 'text-danger-500' : 'text-[#B45309]' },
                            { label: 'Score', value: `${decision.risk_score}/300`, color: 'text-navy-500' },
                            { label: 'Risk Grade', value: decision.risk_grade, color: 'text-[#B45309]' },
                            { label: 'Loan Limit', value: decision.loan_limit || '—', color: 'text-navy-500' },
                            { label: 'Rate / Tenure', value: `${decision.interest_rate || '—'} / ${decision.tenure || '—'}`, color: 'text-[#64748B]' },
                        ].map(m => (
                            <div key={m.label} className="px-4 py-3 text-center">
                                <p className={`text-heading font-bold ${m.color}`}>{m.value}</p>
                                <p className="text-label text-[#94A3B8] uppercase mt-1">{m.label}</p>
                            </div>
                        ))}
                    </div>
                    {decision.reason && (
                        <div className="px-4 py-2 border-t border-border text-data text-[#64748B]">
                            <strong>Reason:</strong> {decision.reason}
                        </div>
                    )}
                    <div className="px-4 py-2 border-t border-border">
                        <a href="/results" className="text-body font-semibold text-navy-500 hover:underline">
                            View Full Results & CAM Report →
                        </a>
                    </div>
                </div>
            )}
        </div>
    );
}

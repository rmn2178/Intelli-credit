'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const DOC_LIST = [
    'Balance Sheet', 'Profit & Loss', 'Cash Flow', 'Bank Statement',
    'GSTR-1', 'GSTR-3B', 'GSTR-2A', 'ITR', 'Form 26AS',
    'Certificate of Incorp.', 'MOA', 'AOA', 'Annual Report',
    'Business Plan', 'Board Resolution', 'Shareholding', 'Industry Report',
];

export default function HomePage() {
    const router = useRouter();
    const [form, setForm] = useState({ company_name: '', cin: '', gstin: '', loan_amount: '', loan_purpose: '' });
    const [loading, setLoading] = useState(false);
    const [companyName, setCompanyName] = useState('');

    useEffect(() => {
        if (typeof window !== 'undefined') setCompanyName(localStorage.getItem('company_name') || '');
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!form.company_name) return;
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/sessions`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...form, loan_amount: form.loan_amount ? parseFloat(form.loan_amount) : null }),
            });
            const data = await res.json();
            if (data.session_id) {
                localStorage.setItem('session_id', data.session_id);
                localStorage.setItem('company_name', form.company_name);
                router.push('/upload');
            }
        } catch (err) { console.error(err); }
        setLoading(false);
    };

    return (
        <div className="p-6">
            {/* ── Regulatory Constitution Bar ── */}
            <div className="card flex items-center justify-between px-4 py-2 mb-6 border-l-[3px] border-l-[#B45309]">
                <div className="flex items-center gap-4">
                    <span className="text-label font-semibold text-[#B45309] uppercase">Regulatory Constitution</span>
                    <span className="badge-gold">RBI 2024 Active</span>
                    <span className="badge-info">Ind AS Compliant</span>
                    <span className="badge-info">SEBI Norms</span>
                </div>
                <span className="text-[10px] text-[#94A3B8] font-mono">Penta-Layer Neuro-Symbolic AI Framework</span>
            </div>

            <div className="grid grid-cols-3 gap-4">
                {/* ── Col 1+2: Initialize Assessment ── */}
                <div className="col-span-2">
                    <div className="card p-6">
                        <h2 className="text-heading font-bold text-navy-500 mb-1">Initialize Credit Assessment</h2>
                        <p className="text-data text-[#94A3B8] mb-5">Create a new assessment session for the corporate borrower</p>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-label font-semibold text-[#64748B] uppercase mb-1">Company Name *</label>
                                <input type="text" value={form.company_name} onChange={e => setForm({ ...form, company_name: e.target.value })} placeholder="Rcubes Technologies Pvt Ltd" className="input-field" required />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-label font-semibold text-[#64748B] uppercase mb-1">CIN</label>
                                    <input type="text" value={form.cin} onChange={e => setForm({ ...form, cin: e.target.value })} placeholder="U72900TN2018PTC124567" className="input-field" />
                                </div>
                                <div>
                                    <label className="block text-label font-semibold text-[#64748B] uppercase mb-1">GSTIN</label>
                                    <input type="text" value={form.gstin} onChange={e => setForm({ ...form, gstin: e.target.value })} placeholder="33AABCR1234A1Z5" className="input-field" />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-label font-semibold text-[#64748B] uppercase mb-1">Loan Amount (₹)</label>
                                    <input type="number" value={form.loan_amount} onChange={e => setForm({ ...form, loan_amount: e.target.value })} placeholder="25000000" className="input-field" />
                                </div>
                                <div>
                                    <label className="block text-label font-semibold text-[#64748B] uppercase mb-1">Loan Purpose</label>
                                    <input type="text" value={form.loan_purpose} onChange={e => setForm({ ...form, loan_purpose: e.target.value })} placeholder="Working Capital" className="input-field" />
                                </div>
                            </div>
                            <button type="submit" disabled={loading || !form.company_name} className="btn-primary w-full">
                                {loading ? 'Initializing...' : 'Launch Credit Assessment'}
                            </button>
                        </form>
                    </div>

                    {/* ── Engine Capabilities ── */}
                    <div className="card mt-4">
                        <table className="w-full text-data">
                            <thead><tr className="border-b border-border text-left">
                                <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Module</th>
                                <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Function</th>
                                <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Layer</th>
                            </tr></thead>
                            <tbody className="divide-y divide-border">
                                {[
                                    ['Fraud Radar', 'Graph neural network analysis for circular trading, shell companies', 'Relational Graph'],
                                    ['Digital Twin', 'Interest rate, revenue, working capital causal stress testing', 'Causal AI'],
                                    ['Credit Committee', 'Multi-persona AI debate — Risk, Compliance, Business officers', 'Multi-Agent'],
                                    ['CAM Generator', 'Bank-grade Credit Appraisal Memo with audit citations', 'Neuro-Symbolic'],
                                    ['Regulatory Engine', 'RBI Master Direction compliance across regimes', 'Constitutional AI'],
                                    ['OSINT Intelligence', 'External forensic research — NCLT, MCA, SEBI, RBI', 'Federated Intel'],
                                ].map(([mod, fn, layer]) => (
                                    <tr key={mod} className="text-body">
                                        <td className="px-4 py-2 font-semibold text-navy-500">{mod}</td>
                                        <td className="px-4 py-2 text-[#64748B]">{fn}</td>
                                        <td className="px-4 py-2"><span className="badge-info">{layer}</span></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* ── Col 3: Dossier Health Widget ── */}
                <div className="card p-4">
                    <h3 className="text-heading font-bold text-navy-500 mb-1">Dossier Health</h3>
                    <p className="text-[10px] text-[#94A3B8] uppercase tracking-[0.06em] font-semibold mb-3">17-Document Status Matrix</p>
                    <div className="grid grid-cols-1 gap-[2px]">
                        {DOC_LIST.map((doc, i) => (
                            <div key={i} className="flex items-center justify-between py-[6px] px-2 border-b border-border last:border-0">
                                <div className="flex items-center gap-2">
                                    <span className="text-data text-[#94A3B8] font-mono w-[18px]">{String(i + 1).padStart(2, '0')}</span>
                                    <span className="text-data text-[#334155]">{doc}</span>
                                </div>
                                <span className="badge-info">Pending</span>
                            </div>
                        ))}
                    </div>
                    <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
                        <span className="text-label font-semibold text-[#64748B] uppercase">Total</span>
                        <span className="text-data font-bold text-navy-500">0 / 17</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

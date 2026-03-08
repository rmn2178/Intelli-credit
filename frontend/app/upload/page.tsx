'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const DOSSIER = [
    { type: 'balance_sheet', label: 'Balance Sheet', cat: 'Financial' },
    { type: 'profit_loss', label: 'Profit & Loss Statement', cat: 'Financial' },
    { type: 'cash_flow', label: 'Cash Flow Statement', cat: 'Financial' },
    { type: 'bank_statement', label: '12-Month Bank Statement', cat: 'Financial' },
    { type: 'gstr_1', label: 'GSTR-1 (Outward Supplies)', cat: 'GST/Tax' },
    { type: 'gstr_3b', label: 'GSTR-3B (Tax Payment)', cat: 'GST/Tax' },
    { type: 'gstr_2a', label: 'GSTR-2A (Vendor ITC)', cat: 'GST/Tax' },
    { type: 'itr', label: 'Income Tax Return', cat: 'GST/Tax' },
    { type: 'form_26as', label: 'Form 26AS', cat: 'GST/Tax' },
    { type: 'certificate_of_incorporation', label: 'Certificate of Incorporation', cat: 'Legal' },
    { type: 'moa', label: 'Memorandum of Association', cat: 'Legal' },
    { type: 'aoa', label: 'Articles of Association', cat: 'Legal' },
    { type: 'annual_report', label: 'Annual Report', cat: 'Legal' },
    { type: 'business_plan', label: 'Business Plan', cat: 'Legal' },
    { type: 'board_resolution', label: 'Board Resolution', cat: 'Legal' },
    { type: 'shareholding_pattern', label: 'Shareholding Pattern', cat: 'Legal' },
    { type: 'industry_report', label: 'Industry Report', cat: 'Legal' },
];

export default function UploadPage() {
    const router = useRouter();
    const [files, setFiles] = useState<Record<string, File | null>>({});
    const [uploading, setUploading] = useState(false);
    const [uploaded, setUploaded] = useState<string[]>([]);
    const sessionId = typeof window !== 'undefined' ? localStorage.getItem('session_id') : null;

    const handleFile = (docType: string, file: File | null) => {
        if (file) setFiles(prev => ({ ...prev, [docType]: file }));
    };

    const handleUpload = async () => {
        if (!sessionId) return;
        const fileEntries = Object.entries(files).filter(([_, f]) => f !== null);
        if (fileEntries.length === 0) return;
        setUploading(true);
        const formData = new FormData();
        const types: string[] = [];
        fileEntries.forEach(([type, file]) => { if (file) { formData.append('files', file); types.push(type); } });
        formData.append('doc_types', types.join(','));
        try { await fetch(`${API}/api/sessions/${sessionId}/upload`, { method: 'POST', body: formData }); setUploaded(types); } catch (err) { console.error(err); }
        setUploading(false);
    };

    const selectedCount = Object.keys(files).length;
    const getStatus = (type: string) => {
        if (uploaded.includes(type)) return 'extracted';
        if (files[type]) return 'selected';
        return 'pending';
    };

    return (
        <div className="p-6 max-w-[960px]">
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h1 className="text-title font-bold text-navy-500">Dossier Checklist</h1>
                    <p className="text-data text-[#94A3B8]">Upload the 17-document corporate dossier. Each document is verified for extraction and SMT consistency.</p>
                </div>
                <div className="text-right">
                    <span className="text-heading font-bold text-navy-500">{selectedCount}</span>
                    <span className="text-data text-[#94A3B8]"> / 17</span>
                </div>
            </div>

            {/* Progress bar — thin, no radius */}
            <div className="w-full h-[3px] bg-border mb-6">
                <div className="h-full bg-navy-500 transition-all" style={{ width: `${(selectedCount / 17) * 100}%` }} />
            </div>

            {/* Dossier Table */}
            <div className="card">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-border text-left">
                            <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase w-[32px]">#</th>
                            <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Document</th>
                            <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Category</th>
                            <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">Status</th>
                            <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase">File</th>
                            <th className="px-4 py-2 text-label font-semibold text-[#64748B] uppercase w-[80px]">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {DOSSIER.map((doc, i) => {
                            const status = getStatus(doc.type);
                            return (
                                <tr key={doc.type} className="text-body">
                                    <td className="px-4 py-2 text-data text-[#94A3B8] font-mono">{String(i + 1).padStart(2, '0')}</td>
                                    <td className="px-4 py-2 font-medium text-[#334155]">{doc.label}</td>
                                    <td className="px-4 py-2"><span className="badge-info">{doc.cat}</span></td>
                                    <td className="px-4 py-2">
                                        {status === 'extracted' ? <span className="badge-pass">Extracted</span> :
                                            status === 'selected' ? <span className="badge-gold">Selected</span> :
                                                <span className="badge-info">Pending</span>}
                                    </td>
                                    <td className="px-4 py-2 text-data text-[#94A3B8] truncate max-w-[160px]">{files[doc.type]?.name || '—'}</td>
                                    <td className="px-4 py-2">
                                        <label className="btn-secondary text-[11px] py-[4px] px-[8px] cursor-pointer inline-block">
                                            Browse
                                            <input type="file" className="hidden" accept=".pdf,.md,.txt,.csv" onChange={e => handleFile(doc.type, e.target.files?.[0] || null)} />
                                        </label>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            <div className="flex gap-2 mt-4">
                <button onClick={handleUpload} disabled={uploading || selectedCount === 0} className="flex-1 btn-primary disabled:opacity-35">
                    {uploading ? 'Uploading...' : `Upload ${selectedCount} Documents`}
                </button>
                {uploaded.length > 0 && (
                    <button onClick={() => router.push('/processing')} className="btn-emerald">Start Processing</button>
                )}
            </div>
        </div>
    );
}

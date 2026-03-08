import '../styles/globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'Intelli-Credit Decisioning Engine',
    description: 'Autonomous Corporate Credit Intelligence Operating System for Indian Banking',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
            <body className="bg-workspace min-h-screen">
                <div className="flex min-h-screen">
                    {/* ── Fixed Sidebar ── */}
                    <aside className="w-[232px] sidebar flex flex-col shrink-0 border-r border-white/[0.06]">
                        <div className="px-4 py-4 border-b border-white/[0.06]">
                            <p className="text-[13px] font-bold text-white tracking-tight leading-none">Intelli-Credit</p>
                            <p className="text-[10px] text-[#475569] mt-[4px] font-medium uppercase tracking-[0.08em]">Decisioning Engine v2.0</p>
                        </div>

                        <nav className="flex-1 px-2 py-3 space-y-[2px]">
                            {[
                                { href: '/', label: 'Command Center', d: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z' },
                                { href: '/upload', label: 'Document Upload', d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6 M12 18v-6 M9 15l3-3 3 3' },
                                { href: '/processing', label: 'AI Processing', d: 'M22 12h-4l-3 9L9 3l-3 9H2' },
                                { href: '/simulator', label: 'Credit Flight Simulator', d: 'M4 21V14M4 10V3M12 21V12M12 8V3M20 21V16M20 12V3M1 14h6M9 8h6M17 16h6' },
                                { href: '/regulatory', label: 'Regulatory Engine', d: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z M9 12l2 2 4-4' },
                                { href: '/intelligence', label: 'Intelligence Hub', d: 'M12 2a10 10 0 100 20 10 10 0 000-20z M2 12h20 M12 2a15 15 0 014 10 15 15 0 01-4 10 15 15 0 01-4-10 15 15 0 014-10z' },
                                { href: '/results', label: 'Decision & CAM', d: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8' },
                            ].map((item) => (
                                <a key={item.href} href={item.href} className="sidebar-link">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d={item.d} /></svg>
                                    {item.label}
                                </a>
                            ))}
                        </nav>

                        <div className="px-4 py-3 border-t border-white/[0.06]">
                            <div className="flex items-center gap-[6px]">
                                <div className="w-[5px] h-[5px] bg-emerald-500"></div>
                                <span className="text-[10px] text-[#64748B] font-medium">Operational</span>
                            </div>
                        </div>
                    </aside>

                    {/* ── Main Workspace ── */}
                    <main className="flex-1 overflow-auto">{children}</main>
                </div>
            </body>
        </html>
    );
}

'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  Shield,
  Layers,
  Star,
  Kanban,
  Settings,
  Search,
  RefreshCw,
  Clock,
  ExternalLink,
  Download,
  Share2,
  Copy,
  Moon,
  Sun,
  Building2,
  Calendar,
  Check,
  X,
  FileText,
  AlertCircle,
  Bookmark,
} from 'lucide-react';

interface TenderItem {
  id: string;
  externalRef: string | null;
  title: string;
  clientName: string;
  clientNormalized?: string | null;
  category?: string | null;
  publicationDate: string | null;
  deadline: string | null;
  directUrl: string;
  dceUrl?: string;
  status: string;
  isHighPriority: boolean;
  matchedKeywords: string[];
  relevanceScore: number;
  sourceSlug: string;
  sourceName: string;
  createdAt: string;
}

export default function OriginalStyleApp() {
  const [tenders, setTenders] = useState<TenderItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'cyber' | 'priority' | 'pipeline'>('all');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [selectedTender, setSelectedTender] = useState<TenderItem | null>(null);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState<string | null>(null);

  // Initialize theme
  useEffect(() => {
    const savedTheme = localStorage.getItem('cyberrfp_theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      setIsDarkMode(true);
      document.documentElement.classList.add('dark');
    } else {
      setIsDarkMode(false);
      document.documentElement.classList.remove('dark');
    }
  }, []);

  const toggleTheme = () => {
    setIsDarkMode((prev) => {
      const next = !prev;
      if (next) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('cyberrfp_theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('cyberrfp_theme', 'light');
      }
      return next;
    });
  };

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  };

  const cleanClientName = (name: string): string => {
    if (!name) return 'Acheteur public';
    let cleaned = name.trim();
    if (cleaned.includes('Acheteur public :')) {
      const parts = cleaned.split('Acheteur public :');
      cleaned = parts[0].trim() || parts[1].trim();
    }
    return cleaned;
  };

  const formatCleanTitle = (title: string): string => {
    if (!title) return '';
    const str = title.trim();
    const letters = str.replace(/[^a-zA-ZÀ-ÿ]/g, '');
    const uppers = str.replace(/[^A-ZÀ-Ý]/g, '');
    if (letters.length > 5 && (uppers.length / letters.length) > 0.6) {
      const acronyms = new Set([
        'SOC', 'SIEM', 'EDR', 'XDR', 'WAF', 'PAM', 'IAM', 'MFA', 'PKI', 'ISO',
        'CPS', 'DCE', 'TDR', 'PMMP', 'ANRT', 'CNSS', 'DGI', 'OFPPT', 'ANRF',
        'DGSSI', 'NDR', 'API', 'IT', 'SSI', 'ERP', 'MAD', 'TTC', 'DH', 'STEP',
        'CL', 'SCR', 'AOO', 'AOI', 'SMI', 'LAN', 'WAN', 'NOC', 'SLA', 'VPN'
      ]);
      const words = str.toLowerCase().split(/\s+/);
      return words.map((w, idx) => {
        const cleanW = w.replace(/[^a-zA-ZÀ-ÿ0-9]/g, '').toUpperCase();
        if (acronyms.has(cleanW)) return w.toUpperCase();
        if (idx === 0) return w.charAt(0).toUpperCase() + w.slice(1);
        const lowers = new Set(['de', 'du', 'des', 'le', 'la', 'les', 'un', 'une', "d'", "l'", 'à', 'au', 'aux', 'et', 'en', 'pour', 'sur', 'par', 'dans']);
        if (lowers.has(w)) return w;
        return w.charAt(0).toUpperCase() + w.slice(1);
      }).join(' ');
    }
    return str;
  };

  const copyText = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    showToast(`✓ ${label} copié !`);
  };

  const toggleTrack = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSavedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
        showToast('Retiré du pipeline commercial');
      } else {
        next.add(id);
        showToast('★ Ajouté au pipeline commercial !');
      }
      return next;
    });
  };

  const fetchPMMPTenders = async () => {
    try {
      setLoading(true);
      // Explicitly request PMMP source only
      const res = await fetch('/api/tenders?source=pmmp&limit=200');
      if (res.ok) {
        const data = await res.json();
        // Strictly filter to PMMP only
        const items: TenderItem[] = (data.items || []).filter(
          (t: TenderItem) => !t.sourceSlug || t.sourceSlug.toLowerCase() === 'pmmp' || t.sourceName?.toUpperCase().includes('PMMP')
        );
        setTenders(items);
      }
    } catch (err) {
      console.error('Erreur chargement PMMP:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPMMPTenders();
  }, []);

  const triggerSync = async () => {
    setRefreshing(true);
    showToast('Interrogation directe du portail PMMP en cours...');
    try {
      await fetch('/api/cron/scrape');
      await fetchPMMPTenders();
      showToast('✓ Portail PMMP synchronisé !');
    } catch {
      showToast('Erreur lors de la synchronisation PMMP');
    } finally {
      setRefreshing(false);
    }
  };

  const getDaysDiff = (deadline: string | null) => {
    if (!deadline) return null;
    const end = new Date(deadline);
    if (isNaN(end.getTime())) return null;
    const now = new Date();
    return Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  };

  // Filtered tenders based on active navigation tab & search
  const filteredTenders = useMemo(() => {
    return tenders.filter((t) => {
      if (activeTab === 'priority' && !t.isHighPriority) return false;
      if (activeTab === 'pipeline' && !savedIds.has(t.id)) return false;

      const allWords = `${t.title} ${t.clientName} ${t.externalRef || ''} ${(t.matchedKeywords || []).join(' ')}`.toLowerCase();

      if (activeTab === 'cyber') {
        const isCyber =
          allWords.includes('cyber') ||
          allWords.includes('sécurité') ||
          allWords.includes('securite') ||
          allWords.includes('soc') ||
          allWords.includes('siem') ||
          allWords.includes('edr') ||
          allWords.includes('audit') ||
          allWords.includes('pentest') ||
          allWords.includes('firewall');
        if (!isCyber) return false;
      }

      if (search.trim()) {
        const q = search.toLowerCase();
        if (!allWords.includes(q)) return false;
      }

      return true;
    });
  }, [tenders, activeTab, savedIds, search]);

  const cyberCount = useMemo(() => {
    return tenders.filter((t) => {
      const w = `${t.title} ${t.clientName} ${(t.matchedKeywords || []).join(' ')}`.toLowerCase();
      return (
        w.includes('cyber') ||
        w.includes('sécurité') ||
        w.includes('securite') ||
        w.includes('soc') ||
        w.includes('siem') ||
        w.includes('edr') ||
        w.includes('audit') ||
        w.includes('firewall')
      );
    }).length;
  }, [tenders]);

  const priorityCount = useMemo(() => tenders.filter((t) => t.isHighPriority).length, [tenders]);
  const urgentCount = useMemo(() => {
    return tenders.filter((t) => {
      const d = getDaysDiff(t.deadline);
      return d !== null && d >= 0 && d <= 7;
    }).length;
  }, [tenders]);

  const openWhatsApp = (tender: TenderItem) => {
    const days = getDaysDiff(tender.deadline);
    const deadlineStr = tender.deadline ? new Date(tender.deadline).toLocaleDateString('fr-FR') : 'Non précisée';
    const text = `🚨 *Appel d'Offres PMMP Maroc*\n` +
      `🏛️ *Acheteur :* ${tender.clientName}\n` +
      `📌 *Réf :* ${tender.externalRef || 'N/A'}\n` +
      `📑 *Objet :* ${tender.title}\n` +
      `⏳ *Date limite :* ${deadlineStr} ${days !== null ? `(J-${days})` : ''}\n` +
      `🔗 *Lien DCE :* ${tender.directUrl}\n\n` +
      `_Veille CyberRFP Maroc_`;
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-[#080c15] text-slate-800 dark:text-slate-100 font-sans transition-colors">
      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-slate-900 text-white px-4 py-2.5 rounded-xl shadow-xl text-xs font-semibold border border-slate-700 animate-fade-in">
          <Check className="w-4 h-4 text-emerald-400" />
          <span>{toast}</span>
        </div>
      )}

      {/* TOP NAVIGATION BAR (ORIGINAL STYLE) */}
      <header className="sticky top-0 z-40 bg-white/95 dark:bg-slate-900/95 border-b border-slate-200/90 dark:border-slate-800 text-slate-900 dark:text-white shadow-xs backdrop-blur-md transition-colors">
        <div className="max-w-[1720px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14 gap-3">
            
            {/* Brand Logo & Name */}
            <div className="flex items-center space-x-3 shrink-0">
              <div className="h-9 w-9 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 rounded-xl flex items-center justify-center p-1 shadow-2xs">
                <Shield className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-sm sm:text-base tracking-tight text-slate-900 dark:text-white">
                  DPA <span className="text-emerald-500">CYBER-RFP</span>
                </span>
                <span className="hidden md:inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span>PMMP DIRECT</span>
                </span>
              </div>
            </div>

            {/* Center Navigation Tabs */}
            <nav className="hidden lg:flex items-center space-x-1 bg-slate-100/90 dark:bg-slate-800/90 p-1 rounded-xl text-xs font-semibold border border-slate-200/60 dark:border-slate-700/60">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-3 py-1.5 rounded-lg flex items-center space-x-1.5 transition ${
                  activeTab === 'all'
                    ? 'text-white bg-slate-900 dark:bg-slate-700 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Layers className="w-3.5 h-3.5 text-orange-400" />
                <span>Toutes les Offres ({tenders.length})</span>
              </button>

              <button
                onClick={() => setActiveTab('cyber')}
                className={`px-3 py-1.5 rounded-lg flex items-center space-x-1.5 transition ${
                  activeTab === 'cyber'
                    ? 'text-white bg-slate-900 dark:bg-slate-700 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Shield className="w-3.5 h-3.5 text-emerald-500" />
                <span>Cybersécurité & SSI ({cyberCount})</span>
              </button>

              <button
                onClick={() => setActiveTab('priority')}
                className={`px-3 py-1.5 rounded-lg flex items-center space-x-1.5 transition ${
                  activeTab === 'priority'
                    ? 'text-white bg-slate-900 dark:bg-slate-700 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Star className="w-3.5 h-3.5 text-amber-500" />
                <span>Acheteurs Prioritaires ({priorityCount})</span>
              </button>

              <button
                onClick={() => setActiveTab('pipeline')}
                className={`px-3 py-1.5 rounded-lg flex items-center space-x-1.5 transition ${
                  activeTab === 'pipeline'
                    ? 'text-white bg-slate-900 dark:bg-slate-700 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Kanban className="w-3.5 h-3.5 text-blue-500" />
                <span>Pipeline Commercial ({savedIds.size})</span>
              </button>
            </nav>

            {/* Right Side: Quick Actions */}
            <div className="flex items-center space-x-2 shrink-0">
              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                title="Basculer Mode Clair / Sombre"
              >
                {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
              </button>

              {/* Sync Button */}
              <button
                onClick={triggerSync}
                disabled={refreshing}
                className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition disabled:opacity-50"
                title="Interroger le portail PMMP en temps réel"
              >
                <RefreshCw className={`w-4 h-4 text-emerald-600 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
            </div>

          </div>
        </div>
      </header>

      {/* MAIN CONTENT AREA */}
      <main className="max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 flex flex-col gap-6">
        
        {/* STATS OVERVIEW CARDS */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs">
            <div className="text-[11px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">Marchés Indexés</div>
            <div className="text-2xl font-black text-slate-900 dark:text-white mt-1">{tenders.length}</div>
            <div className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-1 flex items-center gap-1 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              Flux PMMP direct
            </div>
          </div>

          <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs">
            <div className="text-[11px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">Cybersécurité</div>
            <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">{cyberCount}</div>
            <div className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">SOC, SIEM, EDR, Audit</div>
          </div>

          <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs">
            <div className="text-[11px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">Acheteurs Cibles</div>
            <div className="text-2xl font-black text-amber-500 mt-1">{priorityCount}</div>
            <div className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">Ministères & Banques</div>
          </div>

          <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xs">
            <div className="text-[11px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold">Échéances &lt; 7J</div>
            <div className="text-2xl font-black text-rose-500 mt-1">{urgentCount}</div>
            <div className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">Remise imminente</div>
          </div>
        </div>

        {/* SEARCH & FILTERS BAR */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher par organisme, mot-clé, référence PMMP..."
              className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>

          {/* Quick tab chips for mobile/tablets */}
          <div className="flex lg:hidden items-center gap-1.5 overflow-x-auto pb-1 text-xs">
            {[
              { id: 'all', label: 'Toutes' },
              { id: 'cyber', label: 'Cyber' },
              { id: 'priority', label: 'Prioritaires' },
              { id: 'pipeline', label: 'Pipeline' },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id as any)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap ${
                  activeTab === t.id
                    ? 'bg-slate-900 dark:bg-slate-700 text-white'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* CARD GRID (ORIGINAL card-modern STYLE) */}
        {loading ? (
          <div className="py-24 text-center text-slate-400 text-xs">
            <RefreshCw className="w-6 h-6 mx-auto mb-2 animate-spin text-emerald-500" />
            Chargement des appels d'offres PMMP...
          </div>
        ) : filteredTenders.length === 0 ? (
          <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 text-sm text-slate-500">
            Aucun appel d'offres PMMP ne correspond à vos filtres.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTenders.map((tender) => {
              const days = getDaysDiff(tender.deadline);
              const isSaved = savedIds.has(tender.id);

              let badgeStyle = 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300';
              let badgeText = 'Date non précisée';
              if (days !== null) {
                if (days < 0) {
                  badgeStyle = 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800/60';
                  badgeText = 'Expiré';
                } else if (days <= 5) {
                  badgeStyle = 'bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800/60 font-bold';
                  badgeText = `J-${days} (Urgent)`;
                } else if (days <= 12) {
                  badgeStyle = 'bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800/60 font-semibold';
                  badgeText = `J-${days}`;
                } else {
                  badgeStyle = 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60';
                  badgeText = `J-${days}`;
                }
              }

              return (
                <div
                  key={tender.id}
                  onClick={() => setSelectedTender(tender)}
                  className="card-modern p-5 flex flex-col justify-between cursor-pointer relative group"
                >
                  <div>
                    {/* Header: Buyer Name & Reference */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-900 dark:text-white truncate">
                        <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="truncate" title={cleanClientName(tender.clientName)}>{cleanClientName(tender.clientName)}</span>
                      </div>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full shrink-0 ${badgeStyle}`}>
                        {badgeText}
                      </span>
                    </div>

                    {/* Reference & Source Badge */}
                    <div className="flex items-center gap-2 mb-2.5 text-[11px] text-slate-500 font-mono">
                      <span>Réf: {tender.externalRef || 'En cours'}</span>
                      <span>•</span>
                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold">PMMP</span>
                      {tender.isHighPriority && (
                        <>
                          <span>•</span>
                          <span className="text-amber-500 font-semibold">★ Prioritaire</span>
                        </>
                      )}
                    </div>

                    {/* Title */}
                    <h3 className="text-xs sm:text-sm font-semibold text-slate-800 dark:text-slate-100 line-clamp-2 leading-snug mb-3 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                      {formatCleanTitle(tender.title)}
                    </h3>

                    {/* Matched Keywords */}
                    <div className="flex flex-wrap gap-1 mb-4">
                      {tender.matchedKeywords?.slice(0, 3).map((kw, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200/60 dark:border-slate-700/60"
                        >
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Card Actions Footer */}
                  <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
                    <div className="flex items-center gap-1.5">
                      {/* Direct Portal Reading */}
                      <a
                        href={tender.directUrl}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-semibold text-[11px] transition"
                        title="Consulter et lire les détails directement sur le portail PMMP"
                      >
                        <FileText className="w-3 h-3 text-slate-500 dark:text-slate-400" />
                        <span>Lire PMMP</span>
                        <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                      </a>

                      {/* Direct Official DCE Download */}
                      <a
                        href={tender.dceUrl || `/api/tenders/${tender.id}/download-dce`}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-[11px] transition shadow-2xs"
                        title="Télécharger directement le dossier DCE officiel sur PMMP"
                      >
                        <Download className="w-3 h-3" />
                        <span>DCE</span>
                      </a>
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          openWhatsApp(tender);
                        }}
                        className="p-1.5 rounded-lg text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 transition"
                        title="Partager sur WhatsApp"
                      >
                        <Share2 className="w-4 h-4" />
                      </button>

                      <button
                        onClick={(e) => toggleTrack(tender.id, e)}
                        className={`p-1.5 rounded-lg transition ${
                          isSaved
                            ? 'text-amber-500 bg-amber-50 dark:bg-amber-950/40'
                            : 'text-slate-400 hover:text-slate-600 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
                        }`}
                        title={isSaved ? 'Suivi dans le pipeline' : 'Ajouter au pipeline'}
                      >
                        <Bookmark className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

      </main>

      {/* TENDER DETAIL MODAL (ORIGINAL STYLE) */}
      {selectedTender && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-fade-in"
          onClick={() => setSelectedTender(null)}
        >
          <div
            className="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 p-6 space-y-5 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                  DPA-CYBER-RFP · Consultation PMMP
                </span>
                <h2 className="text-base font-bold text-slate-900 dark:text-white mt-1">
                  {cleanClientName(selectedTender.clientName)}
                </h2>
              </div>
              <button
                onClick={() => setSelectedTender(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Object */}
            <div>
              <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">Objet du Marché :</div>
              <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
                {formatCleanTitle(selectedTender.title)}
              </p>
            </div>

            {/* Grid details */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
                <span className="text-slate-500 dark:text-slate-400">Référence PMMP :</span>
                <div className="font-mono font-bold text-slate-900 dark:text-white mt-0.5 flex items-center justify-between">
                  <span>{selectedTender.externalRef || 'N/A'}</span>
                  {selectedTender.externalRef && (
                    <button
                      onClick={() => copyText(selectedTender.externalRef || '', 'Référence')}
                      className="text-slate-400 hover:text-slate-600 dark:hover:text-white"
                      title="Copier la référence"
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
                <span className="text-slate-500 dark:text-slate-400">Date Limite de Remise :</span>
                <div className="font-mono font-bold text-rose-600 dark:text-rose-400 mt-0.5">
                  {selectedTender.deadline
                    ? new Date(selectedTender.deadline).toLocaleDateString('fr-FR')
                    : 'Non précisée'}
                </div>
              </div>
            </div>

            {/* Matched Keywords */}
            <div>
              <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1.5">
                Mots-clés Détectés :
              </div>
              <div className="flex flex-wrap gap-1.5">
                {selectedTender.matchedKeywords?.map((kw, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 rounded-lg text-xs font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            </div>

            {/* Actions Bar */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 pt-3 border-t border-slate-100 dark:border-slate-800">
              <a
                href={selectedTender.directUrl}
                target="_blank"
                rel="noreferrer"
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-100 text-xs font-bold transition border border-slate-200 dark:border-slate-700"
              >
                <FileText className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span>Lire la Consultation sur PMMP</span>
                <ExternalLink className="w-3.5 h-3.5 opacity-70" />
              </a>

              <a
                href={selectedTender.dceUrl || `/api/tenders/${selectedTender.id}/download-dce`}
                target="_blank"
                rel="noreferrer"
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition shadow-xs"
              >
                <Download className="w-4 h-4" />
                <span>Télécharger le DCE Officiel</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>

              <button
                onClick={() => openWhatsApp(selectedTender)}
                className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800/60 text-emerald-700 dark:text-emerald-300 text-xs font-bold hover:bg-emerald-100 transition"
              >
                <Share2 className="w-4 h-4" />
                <span>WhatsApp</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* FOOTER */}
      <footer className="border-t border-slate-200 dark:border-slate-800 py-4 text-xs text-slate-500 text-center bg-white dark:bg-slate-900">
        DPA-CYBER-RFP — Veille Spécialisée Appels d'Offres Publics Cybersécurité & Marchés Publics
      </footer>
    </div>
  );
}

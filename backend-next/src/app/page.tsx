'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  Shield,
  Search,
  RefreshCw,
  Clock,
  ExternalLink,
  Building2,
  Share2,
  Copy,
  ChevronRight,
  Download,
  Calendar,
  Sparkles,
  Bookmark,
  Check,
  Layers,
  ArrowUpRight,
  Filter,
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
  status: string;
  isHighPriority: boolean;
  matchedKeywords: string[];
  relevanceScore: number;
  sourceSlug: string;
  sourceName: string;
  createdAt: string;
}

interface SourceStats {
  id: string;
  slug: string;
  name: string;
  healthStatus: string;
  itemsIndexed: number;
  lastRunAt: string | null;
}

export default function CleanCyberRFPDashboard() {
  const [tenders, setTenders] = useState<TenderItem[]>([]);
  const [sources, setSources] = useState<SourceStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [activeFilter, setActiveFilter] = useState<'all' | 'high' | 'urgent' | 'soc' | 'audit' | 'infra'>('all');
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [selectedTenderId, setSelectedTenderId] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  };

  const copyText = (text: string, key: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    showToast(`${label} copié !`);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const toggleSave = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSavedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
        showToast('Retiré de votre sélection');
      } else {
        next.add(id);
        showToast('Ajouté à vos opportunités suivies');
      }
      return next;
    });
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [tendersRes, sourcesRes] = await Promise.all([
        fetch('/api/tenders?limit=150'),
        fetch('/api/sources'),
      ]);

      if (tendersRes.ok) {
        const data = await tendersRes.json();
        const items: TenderItem[] = data.items || [];
        setTenders(items);
        if (items.length > 0 && !selectedTenderId) {
          setSelectedTenderId(items[0].id);
        }
      }
      if (sourcesRes.ok) {
        const data = await sourcesRes.json();
        setSources(data.sources || []);
      }
    } catch (err) {
      console.error('Erreur de chargement:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const runScan = async () => {
    setRefreshing(true);
    showToast('Actualisation des 7 portails en cours...');
    try {
      const res = await fetch('/api/cron/scrape');
      const data = await res.json();
      showToast(`${data.tendersNew || 0} nouveaux marchés indexés`);
      await loadData();
    } catch {
      showToast('Erreur lors du rafraîchissement');
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

  // Filter logic
  const filteredTenders = useMemo(() => {
    return tenders.filter((t) => {
      if (selectedSource !== 'all' && t.sourceSlug !== selectedSource) return false;
      if (activeFilter === 'high' && !t.isHighPriority) return false;

      const days = getDaysDiff(t.deadline);
      if (activeFilter === 'urgent') {
        if (days === null || days > 7 || days < 0) return false;
      }

      const allWords = `${t.title} ${t.clientName} ${t.externalRef || ''} ${(t.matchedKeywords || []).join(' ')}`.toLowerCase();

      if (activeFilter === 'soc') {
        if (!allWords.includes('soc') && !allWords.includes('siem') && !allWords.includes('edr') && !allWords.includes('surveillance')) {
          return false;
        }
      }
      if (activeFilter === 'audit') {
        if (!allWords.includes('audit') && !allWords.includes('pentest') && !allWords.includes('intrusion') && !allWords.includes('conformit')) {
          return false;
        }
      }
      if (activeFilter === 'infra') {
        if (!allWords.includes('reseau') && !allWords.includes('réseau') && !allWords.includes('firewall') && !allWords.includes('datacenter')) {
          return false;
        }
      }

      if (search.trim()) {
        const q = search.toLowerCase();
        if (!allWords.includes(q)) return false;
      }

      return true;
    });
  }, [tenders, selectedSource, activeFilter, search]);

  const selectedTender = useMemo(() => {
    return tenders.find((t) => t.id === selectedTenderId) || filteredTenders[0] || null;
  }, [tenders, selectedTenderId, filteredTenders]);

  const highPriorityCount = useMemo(() => tenders.filter((t) => t.isHighPriority).length, [tenders]);
  const urgentCount = useMemo(() => {
    return tenders.filter((t) => {
      const d = getDaysDiff(t.deadline);
      return d !== null && d >= 0 && d <= 7;
    }).length;
  }, [tenders]);

  const generateWhatsAppMessage = (tender: TenderItem) => {
    const days = getDaysDiff(tender.deadline);
    const deadlineStr = tender.deadline ? new Date(tender.deadline).toLocaleDateString('fr-FR') : 'Non précisée';
    const daysStr = days !== null ? (days >= 0 ? `(J-${days})` : '(Expiré)') : '';
    return `*Opportunité Cyber & IT Maroc*\n\n` +
      `*Organisme :* ${tender.clientName}\n` +
      `*Objet :* ${tender.title}\n` +
      `*Réf :* ${tender.externalRef || 'N/A'}\n` +
      `*Date limite :* ${deadlineStr} ${daysStr}\n` +
      `*Lien DCE :* ${tender.directUrl}\n\n` +
      `_Veille CyberRFP Maroc_`;
  };

  const openWhatsApp = (tender: TenderItem) => {
    const text = encodeURIComponent(generateWhatsAppMessage(tender));
    window.open(`https://wa.me/?text=${text}`, '_blank');
  };

  return (
    <div className="min-h-screen bg-[#0A0C12] text-slate-100 flex flex-col font-sans antialiased">
      {/* Toast Feedback */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-[#141824] text-slate-100 px-4 py-2.5 rounded-lg border border-slate-700/80 shadow-xl text-xs font-medium">
          <Check className="w-3.5 h-3.5 text-emerald-400" />
          <span>{toast}</span>
        </div>
      )}

      {/* MINIMALIST HEADER */}
      <header className="border-b border-white/[0.08] bg-[#0E111A]/80 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
          
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Shield className="w-4 h-4" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-semibold text-sm tracking-tight text-white">CyberRFP</span>
              <span className="text-xs text-slate-400 font-medium">Maroc</span>
            </div>
            <div className="hidden sm:flex items-center gap-1.5 ml-3 pl-3 border-l border-white/[0.08] text-xs text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              <span>7 portails surveillés</span>
            </div>
          </div>

          {/* Search Bar */}
          <div className="flex-1 max-w-md relative hidden md:block">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher par organisme, mot-clé, référence..."
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-white/[0.04] border border-white/[0.08] rounded-md text-white placeholder-slate-500 focus:outline-none focus:border-slate-500 transition-colors"
            />
          </div>

          {/* Action */}
          <div className="flex items-center gap-2">
            <button
              onClick={runScan}
              disabled={refreshing}
              className="flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium text-slate-200 bg-white/[0.06] hover:bg-white/[0.1] border border-white/[0.08] transition-colors cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-emerald-400' : ''}`} />
              <span className="hidden sm:inline">{refreshing ? 'Actualisation...' : 'Actualiser'}</span>
            </button>
          </div>

        </div>
      </header>

      {/* MAIN CONTAINER */}
      <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 flex flex-col gap-6">
        
        {/* SUBTLE KPI OVERVIEW */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-lg bg-[#11141E] border border-white/[0.06]">
            <div className="text-[11px] text-slate-400 font-medium">Marchés en cours</div>
            <div className="text-xl font-semibold text-white mt-1">{tenders.length}</div>
          </div>
          <div className="p-3.5 rounded-lg bg-[#11141E] border border-white/[0.06]">
            <div className="text-[11px] text-slate-400 font-medium">Haute priorité</div>
            <div className="text-xl font-semibold text-emerald-400 mt-1">{highPriorityCount}</div>
          </div>
          <div className="p-3.5 rounded-lg bg-[#11141E] border border-white/[0.06]">
            <div className="text-[11px] text-slate-400 font-medium">Échéances &lt; 7 jours</div>
            <div className="text-xl font-semibold text-amber-400 mt-1">{urgentCount}</div>
          </div>
          <div className="p-3.5 rounded-lg bg-[#11141E] border border-white/[0.06]">
            <div className="text-[11px] text-slate-400 font-medium">Portails actifs</div>
            <div className="text-xl font-semibold text-slate-300 mt-1">7 / 7</div>
          </div>
        </div>

        {/* CLEAN FILTER STRIP */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pb-1 border-b border-white/[0.06]">
          {/* Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none text-xs">
            {[
              { id: 'all', label: `Tous (${tenders.length})` },
              { id: 'high', label: `Prioritaires (${highPriorityCount})` },
              { id: 'urgent', label: `Échéances proches (${urgentCount})` },
              { id: 'soc', label: 'SOC & SIEM' },
              { id: 'audit', label: 'Audit & Sécurité' },
              { id: 'infra', label: 'Réseau & Datacenter' },
            ].map((tab) => {
              const active = activeFilter === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveFilter(tab.id as any)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap cursor-pointer ${
                    active
                      ? 'bg-white/10 text-white font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.03]'
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Source Select */}
          <div className="shrink-0">
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="bg-[#11141E] border border-white/[0.08] rounded-md px-2.5 py-1 text-xs text-slate-300 focus:outline-none focus:border-slate-500"
            >
              <option value="all">Toutes les sources (7)</option>
              <option value="pmmp">Portail Marchés Publics (PMMP)</option>
              <option value="albaridbank">Al Barid Bank</option>
              <option value="ofppt">OFPPT</option>
              <option value="sorec">SOREC</option>
              <option value="adm">Autoroutes du Maroc (ADM)</option>
              <option value="atlantic-re">Atlantic Re</option>
              <option value="laprophan">Laprophan</option>
            </select>
          </div>
        </div>

        {/* SPLIT VIEW: FEED + DOSSIER */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 items-start">
          
          {/* FEED (LEFT) */}
          <div className="lg:col-span-5 flex flex-col gap-2.5">
            <div className="text-xs text-slate-400 font-medium px-1">
              {filteredTenders.length} opportunité{filteredTenders.length > 1 ? 's' : ''} trouvée{filteredTenders.length > 1 ? 's' : ''}
            </div>

            {loading ? (
              <div className="py-20 text-center text-slate-500 text-xs">
                <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-slate-400" />
                Chargement des marchés...
              </div>
            ) : filteredTenders.length === 0 ? (
              <div className="p-8 text-center bg-[#11141E] rounded-lg border border-white/[0.06] text-xs text-slate-400">
                Aucun marché ne correspond à ces critères.
              </div>
            ) : (
              <div className="space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
                {filteredTenders.map((item) => {
                  const isSelected = selectedTender?.id === item.id;
                  const days = getDaysDiff(item.deadline);
                  const isSaved = savedIds.has(item.id);

                  let deadlineText = 'Date non précisée';
                  let deadlineColor = 'text-slate-400';
                  if (days !== null) {
                    if (days < 0) {
                      deadlineText = 'Expiré';
                      deadlineColor = 'text-slate-500';
                    } else if (days === 0) {
                      deadlineText = "Aujourd'hui";
                      deadlineColor = 'text-rose-400 font-medium';
                    } else if (days <= 5) {
                      deadlineText = `J-${days}`;
                      deadlineColor = 'text-rose-400 font-medium';
                    } else if (days <= 12) {
                      deadlineText = `J-${days}`;
                      deadlineColor = 'text-amber-400';
                    } else {
                      deadlineText = `J-${days}`;
                      deadlineColor = 'text-slate-400';
                    }
                  }

                  return (
                    <div
                      key={item.id}
                      onClick={() => setSelectedTenderId(item.id)}
                      className={`p-3.5 rounded-lg border cursor-pointer transition-colors relative ${
                        isSelected
                          ? 'bg-[#151926] border-emerald-500/80'
                          : 'bg-[#11141E] border-white/[0.06] hover:border-white/[0.12] hover:bg-[#141722]'
                      }`}
                    >
                      {/* Top row */}
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span className="text-xs font-medium text-slate-300 truncate max-w-[220px]">
                          {item.clientName}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] text-slate-500 font-mono">
                            {item.sourceName}
                          </span>
                          <span className={`text-[11px] font-mono ${deadlineColor}`}>
                            {deadlineText}
                          </span>
                        </div>
                      </div>

                      {/* Title */}
                      <h3 className="text-xs font-normal text-slate-100 line-clamp-2 leading-relaxed mb-2">
                        {item.title}
                      </h3>

                      {/* Bottom row */}
                      <div className="flex items-center justify-between pt-2 border-t border-white/[0.04] text-[11px] text-slate-500">
                        <div className="flex items-center gap-1.5 overflow-hidden">
                          {item.isHighPriority && (
                            <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-medium">
                              Prioritaire
                            </span>
                          )}
                          {item.matchedKeywords?.slice(0, 2).map((kw, idx) => (
                            <span key={idx} className="px-1.5 py-0.5 rounded bg-white/[0.04] text-slate-400 text-[10px]">
                              {kw}
                            </span>
                          ))}
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            onClick={(e) => toggleSave(item.id, e)}
                            title={isSaved ? 'Retirer des favoris' : 'Enregistrer'}
                            className={`p-1 rounded hover:bg-white/10 ${isSaved ? 'text-amber-400' : 'text-slate-500'}`}
                          >
                            <Bookmark className="w-3 h-3" />
                          </button>
                          <span className="font-mono text-[10px] text-slate-500">
                            {item.externalRef ? `Réf: ${item.externalRef}` : 'N/A'}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* DOSSIER (RIGHT) */}
          <div className="lg:col-span-7 sticky top-20">
            {selectedTender ? (
              <div className="p-6 rounded-lg bg-[#11141E] border border-white/[0.08] flex flex-col gap-6">
                
                {/* Dossier Header */}
                <div className="flex flex-col gap-2 pb-4 border-b border-white/[0.06]">
                  <div className="flex items-center justify-between gap-3 text-xs">
                    <span className="text-slate-400 font-medium">
                      {selectedTender.clientName}
                    </span>
                    <span className="text-slate-500 font-mono">
                      Source : {selectedTender.sourceName}
                    </span>
                  </div>

                  <h2 className="text-base sm:text-lg font-semibold text-white leading-snug">
                    {selectedTender.title}
                  </h2>

                  <div className="flex items-center gap-3 pt-1 text-xs text-slate-400">
                    <span className="font-mono text-slate-400">
                      Réf : <strong className="text-slate-200">{selectedTender.externalRef || 'Non précisée'}</strong>
                    </span>
                    {selectedTender.externalRef && (
                      <button
                        onClick={() => copyText(selectedTender.externalRef || '', 'ref', 'Référence')}
                        className="text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
                        title="Copier la référence"
                      >
                        {copiedKey === 'ref' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    )}
                  </div>
                </div>

                {/* Key Metadata Table */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                  <div className="p-3 rounded-md bg-white/[0.02] border border-white/[0.04]">
                    <div className="text-slate-500 text-[11px]">Date de publication</div>
                    <div className="text-slate-200 font-mono mt-0.5">
                      {selectedTender.publicationDate
                        ? new Date(selectedTender.publicationDate).toLocaleDateString('fr-FR')
                        : 'Non spécifiée'}
                    </div>
                  </div>

                  <div className="p-3 rounded-md bg-white/[0.02] border border-white/[0.04]">
                    <div className="text-slate-500 text-[11px]">Date limite de remise</div>
                    <div className="text-slate-200 font-mono mt-0.5">
                      {selectedTender.deadline
                        ? new Date(selectedTender.deadline).toLocaleDateString('fr-FR')
                        : 'Non spécifiée'}
                    </div>
                  </div>

                  <div className="p-3 rounded-md bg-white/[0.02] border border-white/[0.04]">
                    <div className="text-slate-500 text-[11px]">Niveau d'adéquation</div>
                    <div className="text-emerald-400 font-medium mt-0.5">
                      {selectedTender.isHighPriority ? 'Forte adéquation (Prioritaire)' : 'Standard'}
                    </div>
                  </div>
                </div>

                {/* Keywords & Scope */}
                <div className="flex flex-col gap-2">
                  <div className="text-xs text-slate-400 font-medium">Mots-clés et compétences détectés :</div>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedTender.matchedKeywords?.map((kw, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded bg-white/[0.04] border border-white/[0.06] text-slate-300 text-xs"
                      >
                        {kw}
                      </span>
                    ))}
                    {(!selectedTender.matchedKeywords || selectedTender.matchedKeywords.length === 0) && (
                      <span className="text-xs text-slate-500">Non catégorisé</span>
                    )}
                  </div>
                </div>

                {/* Submission note */}
                <div className="p-4 rounded-md bg-white/[0.02] border border-white/[0.04] text-xs text-slate-400 leading-relaxed">
                  <span className="font-medium text-slate-300 block mb-1">Recommandation de préparation :</span>
                  Consultez attentivement le règlement de consultation dans le DCE pour identifier le montant du cautionnement provisoire et les attestations d’agrément requises (notamment pour les prestations de cybersécurité, audits PASSI ou intégrations réseau).
                </div>

                {/* Actions */}
                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <a
                    href={selectedTender.directUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-2 px-4 py-2 rounded-md bg-emerald-500 hover:bg-emerald-600 text-black text-xs font-semibold transition-colors cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Accéder au DCE</span>
                    <ArrowUpRight className="w-3.5 h-3.5 opacity-70" />
                  </a>

                  <button
                    onClick={() => openWhatsApp(selectedTender)}
                    className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-white/[0.06] hover:bg-white/[0.1] border border-white/[0.08] text-slate-200 text-xs font-medium transition-colors cursor-pointer"
                  >
                    <Share2 className="w-3.5 h-3.5 text-slate-400" />
                    <span>Partager sur WhatsApp</span>
                  </button>

                  <button
                    onClick={() => copyText(generateWhatsAppMessage(selectedTender), 'pitch', 'Fiche')}
                    className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-white/[0.04] text-slate-400 hover:text-slate-200 text-xs transition-colors cursor-pointer"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copier la synthèse</span>
                  </button>
                </div>

              </div>
            ) : (
              <div className="p-12 text-center bg-[#11141E] rounded-lg border border-white/[0.06] text-slate-500 text-xs">
                Sélectionnez un appel d'offres pour afficher ses détails.
              </div>
            )}
          </div>

        </div>

      </div>

      {/* MINIMAL FOOTER */}
      <footer className="border-t border-white/[0.06] py-3 text-xs text-slate-500 text-center">
        Plateforme CyberRFP Maroc — Données synchronisées avec les portails officiels
      </footer>
    </div>
  );
}

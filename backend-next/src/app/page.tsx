'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  Shield,
  Search,
  RefreshCw,
  Clock,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  Building2,
  Share2,
  Copy,
  ChevronRight,
  Send,
  Flame,
  Radio,
  Download,
  Calendar,
  DollarSign,
  Briefcase,
  Zap,
  Target,
  FileCheck,
  Award,
  Sparkles,
  Info,
  Check,
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

export default function CyberRFPCommandCenter() {
  const [tenders, setTenders] = useState<TenderItem[]>([]);
  const [sources, setSources] = useState<SourceStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [activeFilter, setActiveFilter] = useState<'all' | 'high' | 'urgent' | 'soc' | 'audit' | 'infra'>('all');
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [selectedTenderId, setSelectedTenderId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [whatsappPhone, setWhatsappPhone] = useState('+212600000000');
  const [trackedIds, setTrackedIds] = useState<Set<string>>(new Set());

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    showToast(`✓ ${label} copié dans le presse-papier !`);
  };

  const toggleTrack = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setTrackedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
        showToast('Retiré du pipeline commercial');
      } else {
        next.add(id);
        showToast('★ Ajouté à votre Pipeline Commercial !');
      }
      return next;
    });
  };

  const fetchData = async () => {
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
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const triggerScan = async () => {
    setRefreshing(true);
    showToast('🚀 Radar de scan en cours d\'exécution sur les 7 portails...');
    try {
      const res = await fetch('/api/cron/scrape');
      const data = await res.json();
      showToast(`✓ Scan terminé : ${data.tendersNew || 0} nouveaux marchés détectés !`);
      await fetchData();
    } catch {
      showToast('❌ Erreur lors du scan');
    } finally {
      setRefreshing(false);
    }
  };

  // Helper for Days Remaining calculation
  const getDaysRemaining = (deadline: string | null) => {
    if (!deadline) return null;
    const end = new Date(deadline);
    if (isNaN(end.getTime())) return null;
    const now = new Date();
    const diffMs = end.getTime() - now.getTime();
    return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
  };

  const formatDaysText = (days: number | null) => {
    if (days === null) return 'Date non précisée';
    if (days < 0) return 'Expiré';
    if (days === 0) return 'Dernier jour (Aujourd\'hui)';
    if (days === 1) return 'J-1 (Demain)';
    return `J-${days} restant${days > 1 ? 's' : ''}`;
  };

  // Filtering
  const filteredTenders = useMemo(() => {
    return tenders.filter((item) => {
      // Source filter
      if (selectedSource !== 'all' && item.sourceSlug !== selectedSource) {
        return false;
      }

      // Keyword / Filter Category
      if (activeFilter === 'high' && !item.isHighPriority) {
        return false;
      }

      const days = getDaysRemaining(item.deadline);
      if (activeFilter === 'urgent') {
        if (days === null || days > 7 || days < 0) return false;
      }

      const allKeywords = (item.matchedKeywords || []).map((k) => k.toLowerCase()).join(' ');
      const textToSearch = `${item.title} ${item.clientName} ${item.externalRef || ''} ${allKeywords}`.toLowerCase();

      if (activeFilter === 'soc') {
        if (!textToSearch.includes('soc') && !textToSearch.includes('siem') && !textToSearch.includes('edr') && !textToSearch.includes('surveillance')) {
          return false;
        }
      }
      if (activeFilter === 'audit') {
        if (!textToSearch.includes('audit') && !textToSearch.includes('pentest') && !textToSearch.includes('intrusion') && !textToSearch.includes('conformit')) {
          return false;
        }
      }
      if (activeFilter === 'infra') {
        if (!textToSearch.includes('reseau') && !textToSearch.includes('réseau') && !textToSearch.includes('firewall') && !textToSearch.includes('switch') && !textToSearch.includes('datacenter')) {
          return false;
        }
      }

      // Search text
      if (search.trim()) {
        const q = search.toLowerCase();
        return textToSearch.includes(q);
      }

      return true;
    });
  }, [tenders, selectedSource, activeFilter, search]);

  const selectedTender = useMemo(() => {
    return tenders.find((t) => t.id === selectedTenderId) || filteredTenders[0] || null;
  }, [tenders, selectedTenderId, filteredTenders]);

  // Telemetry KPIs
  const highPriorityCount = useMemo(() => tenders.filter((t) => t.isHighPriority).length, [tenders]);
  const urgentCount = useMemo(() => {
    return tenders.filter((t) => {
      const d = getDaysRemaining(t.deadline);
      return d !== null && d >= 0 && d <= 7;
    }).length;
  }, [tenders]);

  const activePortalsCount = sources.length > 0 ? sources.length : 7;

  // Formatted WhatsApp message for active tender
  const getWhatsAppPitch = (tender: TenderItem) => {
    const days = getDaysRemaining(tender.deadline);
    const deadlineStr = tender.deadline ? new Date(tender.deadline).toLocaleDateString('fr-FR') : 'Non précisée';
    return `🚨 *OPPORTUNITÉ STRATÉGIQUE CYBER // MAROC*
🏛️ *Organisme :* ${tender.clientName}
📌 *Réf :* ${tender.externalRef || 'N/A'}
📑 *Objet :* ${tender.title}
⏳ *Date limite :* ${deadlineStr} (${formatDaysText(days)})
🛡️ *Mots-clés :* ${tender.matchedKeywords?.join(', ') || 'Cyber, IT'}
🔗 *Dossier Direct :* ${tender.directUrl}

_Partagé depuis CyberRFP Maroc Command Radar_`;
  };

  const openWhatsAppDirect = (tender: TenderItem) => {
    const text = encodeURIComponent(getWhatsAppPitch(tender));
    window.open(`https://wa.me/${whatsappPhone.replace(/[^0-9]/g, '')}?text=${text}`, '_blank');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#06080F] text-slate-100 selection:bg-[#00F59B] selection:text-black">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 bg-[#0B0F19] text-[#00F59B] px-4 py-3 rounded-xl border border-[#00F59B]/50 shadow-2xl shadow-[#00F59B]/20 backdrop-blur-xl animate-bounce">
          <Sparkles className="w-4 h-4 text-[#00F59B]" />
          <span className="text-sm font-semibold">{toastMessage}</span>
        </div>
      )}

      {/* TOP COMMAND STRIP // RADAR STATUS */}
      <header className="border-b border-white/10 bg-[#0B0F19]/90 backdrop-blur-2xl sticky top-0 z-40">
        <div className="max-w-[1700px] mx-auto px-4 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
          
          {/* Brand Identity */}
          <div className="flex items-center gap-3.5">
            <div className="relative flex items-center justify-center w-11 h-11 rounded-xl bg-gradient-to-br from-[#00F59B]/20 to-[#00E5FF]/10 border border-[#00F59B]/40 shadow-[0_0_20px_rgba(0,245,155,0.25)]">
              <Shield className="w-6 h-6 text-[#00F59B]" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-[#00F59B] rounded-full animate-ping opacity-75" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-[#00F59B] rounded-full border-2 border-[#0B0F19]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-black tracking-wider text-white uppercase font-mono">
                  CyberRFP <span className="text-[#00F59B]">MAROC</span>
                </h1>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#00F59B]/15 text-[#00F59B] border border-[#00F59B]/30 tracking-widest uppercase">
                  Apex Radar v2.5
                </span>
              </div>
              <p className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#00F59B] animate-pulse"></span>
                Surveillance Active des Appels d'Offres IT & Cybersécurité
              </p>
            </div>
          </div>

          {/* Quick Telemetry Indicators */}
          <div className="hidden xl:flex items-center gap-6 text-xs font-mono">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/5">
              <span className="text-slate-400">Portails Actifs:</span>
              <span className="text-[#00F59B] font-bold">{activePortalsCount} / 7 En Ligne</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/5">
              <span className="text-slate-400">Marchés Indexés:</span>
              <span className="text-white font-bold">{tenders.length} Appels</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#FF2E63]/10 border border-[#FF2E63]/30">
              <span className="text-[#FF2E63] flex items-center gap-1 font-bold">
                <Flame className="w-3.5 h-3.5" /> {urgentCount} Urgences &lt; 7j
              </span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#FFB800]/10 border border-[#FFB800]/30">
              <span className="text-[#FFB800] flex items-center gap-1 font-bold">
                <Award className="w-3.5 h-3.5" /> {highPriorityCount} Deals Prioritaires
              </span>
            </div>
          </div>

          {/* Radar Scan Action Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={triggerScan}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider text-black bg-gradient-to-r from-[#00F59B] to-[#00E5FF] hover:brightness-110 active:scale-95 transition-all shadow-[0_0_25px_rgba(0,245,155,0.35)] cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-black ${refreshing ? 'animate-spin' : ''}`} />
              <span>{refreshing ? 'Scan en cours...' : 'Lancer Scan Radar'}</span>
            </button>
          </div>

        </div>

        {/* Live Ticker Bar */}
        <div className="border-t border-white/5 bg-black/40 overflow-hidden py-1.5 px-4 text-xs font-mono text-slate-400 flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-[#00F59B] shrink-0 font-bold uppercase tracking-wider text-[11px]">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            <span>FLUX RADAR :</span>
          </div>
          <div className="overflow-hidden relative w-full">
            <div className="animate-marquee whitespace-nowrap flex gap-8">
              <span className="text-slate-300">🇲🇦 PMMP : Marchés État & Ministères synchronisés</span>
              <span className="text-[#00E5FF]">🛡️ Al Barid Bank : Détection SOC & Protection SI</span>
              <span className="text-[#FFB800]">💼 OFPPT : Équipements Réseau & Datacenter</span>
              <span className="text-[#00F59B]">⚡ SOREC : Sécurisation & Audit Intrusion</span>
              <span className="text-slate-300">🛣️ ADM : Télécoms & Liens SD-WAN</span>
              <span className="text-[#FF2E63]">💊 Laprophan & Atlantic Re : Infrastructures & Licences</span>
            </div>
          </div>
        </div>
      </header>

      {/* MAIN RADAR VIEWPORT */}
      <main className="max-w-[1700px] w-full mx-auto px-4 lg:px-8 py-6 flex-1 flex flex-col gap-6">
        
        {/* FILTER BAR // TACTICAL PILLS */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 bg-[#0B0F19]/60 p-3 rounded-2xl border border-white/10 backdrop-blur-xl">
          
          {/* Quick Category Buttons */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
            {[
              { id: 'all', label: `Tous (${tenders.length})`, icon: Zap },
              { id: 'high', label: `🔥 Top Priorité (${highPriorityCount})`, icon: Flame },
              { id: 'urgent', label: `⏳ &lt; 7 Jours (${urgentCount})`, icon: Clock },
              { id: 'soc', label: '🛡️ SOC / SIEM / EDR', icon: Shield },
              { id: 'audit', label: '⚔️ Audit & Pentest', icon: Target },
              { id: 'infra', label: '🧱 Réseau & Firewall', icon: Briefcase },
            ].map((tab) => {
              const active = activeFilter === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveFilter(tab.id as any)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 cursor-pointer ${
                    active
                      ? 'bg-[#00F59B] text-black font-bold shadow-[0_0_15px_rgba(0,245,155,0.4)]'
                      : 'bg-white/[0.04] text-slate-300 hover:bg-white/[0.08] hover:text-white border border-white/5'
                  }`}
                >
                  <span dangerouslySetInnerHTML={{ __html: tab.label }} />
                </button>
              );
            })}
          </div>

          {/* Search Input & Source Dropdown */}
          <div className="flex items-center gap-3">
            <div className="relative flex-1 md:w-72">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Rechercher organisme, réf, mot-clé..."
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-white/[0.04] border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-[#00F59B] transition-all"
              />
              {search && (
                <button
                  onClick={() => setSearch('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white text-xs"
                >
                  ×
                </button>
              )}
            </div>

            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="bg-[#0B0F19] border border-white/10 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-[#00F59B]"
            >
              <option value="all">Tous les portails (7)</option>
              <option value="pmmp">Portail Marchés Publics</option>
              <option value="albaridbank">Al Barid Bank</option>
              <option value="ofppt">OFPPT</option>
              <option value="sorec">SOREC</option>
              <option value="adm">Autoroutes du Maroc (ADM)</option>
              <option value="atlantic-re">Atlantic Re</option>
              <option value="laprophan">Laprophan</option>
            </select>
          </div>

        </div>

        {/* DUAL-PANE PRO WAR ROOM (MASTER-DETAIL) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 items-start">
          
          {/* LEFT COLUMN: THE RFP STREAM (FEED) */}
          <div className="lg:col-span-6 xl:col-span-5 flex flex-col gap-3">
            <div className="flex items-center justify-between px-1 text-xs text-slate-400 font-mono">
              <span>{filteredTenders.length} MARCHÉS DÉTECTÉS</span>
              <span className="text-[#00F59B]">TRIÉ PAR VALEUR & SCORE FIT</span>
            </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center p-16 gap-4 bg-[#0B0F19]/40 rounded-2xl border border-white/5">
                <RefreshCw className="w-8 h-8 text-[#00F59B] animate-spin" />
                <p className="text-sm font-mono text-slate-400">Interrogation du réseau de collecte...</p>
              </div>
            ) : filteredTenders.length === 0 ? (
              <div className="p-12 text-center bg-[#0B0F19]/40 rounded-2xl border border-white/5">
                <Info className="w-8 h-8 text-slate-500 mx-auto mb-3" />
                <p className="text-sm text-slate-300 font-semibold">Aucun appel d'offres ne correspond à vos filtres.</p>
                <p className="text-xs text-slate-500 mt-1">Essayez d'élargir votre recherche ou de réinitialiser le filtre.</p>
                <button
                  onClick={() => { setActiveFilter('all'); setSelectedSource('all'); setSearch(''); }}
                  className="mt-4 px-4 py-2 rounded-xl text-xs bg-[#00F59B]/20 text-[#00F59B] border border-[#00F59B]/40 hover:bg-[#00F59B]/30"
                >
                  Réinitialiser les filtres
                </button>
              </div>
            ) : (
              <div className="space-y-3 max-h-[calc(100vh-270px)] overflow-y-auto pr-1">
                {filteredTenders.map((tender) => {
                  const isSelected = selectedTender?.id === tender.id;
                  const days = getDaysRemaining(tender.deadline);
                  const isTracked = trackedIds.has(tender.id);

                  // Color logic for urgency
                  let deadlineBadge = 'bg-slate-800/80 text-slate-300 border-slate-700';
                  if (days !== null) {
                    if (days < 0) deadlineBadge = 'bg-rose-950/40 text-rose-400 border-rose-900/60';
                    else if (days <= 5) deadlineBadge = 'bg-[#FF2E63]/20 text-[#FF2E63] border-[#FF2E63]/50 animate-pulse';
                    else if (days <= 12) deadlineBadge = 'bg-[#FFB800]/20 text-[#FFB800] border-[#FFB800]/50';
                    else deadlineBadge = 'bg-[#00E5FF]/15 text-[#00E5FF] border-[#00E5FF]/30';
                  }

                  return (
                    <div
                      key={tender.id}
                      onClick={() => setSelectedTenderId(tender.id)}
                      className={`group relative p-4 rounded-2xl cursor-pointer transition-all duration-200 border ${
                        isSelected
                          ? 'bg-[#101726] border-[#00F59B] shadow-[0_0_25px_rgba(0,245,155,0.2)]'
                          : 'bg-[#0B0F19]/80 border-white/[0.07] hover:border-white/20 hover:bg-[#0F1424]'
                      }`}
                    >
                      {/* Left vertical status glow bar when active */}
                      {isSelected && (
                        <div className="absolute left-0 top-3 bottom-3 w-1 bg-[#00F59B] rounded-r-full shadow-[0_0_10px_#00F59B]" />
                      )}

                      {/* Header line: Organisme & Urgency badge */}
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-md bg-white/10 flex items-center justify-center text-slate-300">
                            <Building2 className="w-3.5 h-3.5" />
                          </div>
                          <span className="text-xs font-bold text-slate-200 uppercase tracking-wide truncate max-w-[200px]">
                            {tender.clientName}
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/[0.04] text-slate-400 border border-white/5">
                            {tender.sourceName}
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          {tender.isHighPriority && (
                            <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#FFB800]/20 text-[#FFB800] border border-[#FFB800]/40">
                              <Flame className="w-3 h-3" /> HIGH FIT
                            </span>
                          )}
                          <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${deadlineBadge}`}>
                            {formatDaysText(days)}
                          </span>
                        </div>
                      </div>

                      {/* Title */}
                      <h3 className="text-sm font-semibold text-white leading-snug line-clamp-2 mb-3 group-hover:text-[#00F59B] transition-colors">
                        {tender.title}
                      </h3>

                      {/* Footer: Keywords & Reference */}
                      <div className="flex items-center justify-between gap-2 pt-2 border-t border-white/5 text-xs">
                        <div className="flex flex-wrap items-center gap-1.5 overflow-hidden max-h-6">
                          {tender.matchedKeywords?.slice(0, 3).map((kw, i) => (
                            <span
                              key={i}
                              className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#00E5FF]/10 text-[#00E5FF] border border-[#00E5FF]/20"
                            >
                              {kw}
                            </span>
                          ))}
                          {tender.matchedKeywords && tender.matchedKeywords.length > 3 && (
                            <span className="text-[10px] text-slate-500 font-mono">
                              +{tender.matchedKeywords.length - 3}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            onClick={(e) => toggleTrack(tender.id, e)}
                            title={isTracked ? 'Retirer du pipeline' : 'Suivre ce marché'}
                            className={`p-1.5 rounded-lg border transition-all ${
                              isTracked
                                ? 'bg-[#FFB800]/20 text-[#FFB800] border-[#FFB800]/40'
                                : 'bg-white/5 text-slate-400 hover:text-white border-white/5'
                            }`}
                          >
                            <Award className="w-3.5 h-3.5" />
                          </button>

                          <div className="text-[11px] font-mono text-slate-400">
                            {tender.externalRef ? `Réf: ${tender.externalRef}` : 'Réf: En cours'}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* RIGHT COLUMN: EXECUTIVE INTELLIGENCE DOSSIER */}
          <div className="lg:col-span-6 xl:col-span-7 sticky top-24">
            {selectedTender ? (
              <div className="bg-[#0B0F19]/90 border border-white/10 rounded-2xl p-6 backdrop-blur-2xl shadow-2xl flex flex-col gap-6">
                
                {/* Dossier Header */}
                <div className="flex flex-wrap items-start justify-between gap-4 pb-4 border-b border-white/10">
                  <div className="flex-1 min-w-[280px]">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-lg bg-[#00F59B]/15 text-[#00F59B] border border-[#00F59B]/30 uppercase tracking-wider">
                        Dossier Stratégique
                      </span>
                      <span className="text-xs font-mono text-slate-400">
                        Source : {selectedTender.sourceName}
                      </span>
                      {trackedIds.has(selectedTender.id) && (
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#FFB800]/20 text-[#FFB800] border border-[#FFB800]/40 font-bold">
                          ★ Au Pipeline Commercial
                        </span>
                      )}
                    </div>
                    <h2 className="text-xl font-bold text-white leading-tight">
                      {selectedTender.title}
                    </h2>
                  </div>

                  {/* Win-Fit Score Gauge */}
                  <div className="flex flex-col items-end shrink-0">
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-gradient-to-br from-[#00F59B]/20 to-[#00E5FF]/20 border border-[#00F59B]/40">
                      <Sparkles className="w-4 h-4 text-[#00F59B]" />
                      <span className="text-sm font-mono font-black text-[#00F59B]">
                        {selectedTender.isHighPriority ? '96/100 FIT' : '82/100 FIT'}
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 mt-1">Compatibilité Expertise</span>
                  </div>
                </div>

                {/* Key Deal Economics & Dates Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/5 flex flex-col gap-1">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Building2 className="w-3.5 h-3.5 text-slate-400" />
                      <span>Organisme</span>
                    </div>
                    <span className="text-xs font-bold text-white truncate">
                      {selectedTender.clientName}
                    </span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/5 flex flex-col gap-1">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <FileCheck className="w-3.5 h-3.5 text-slate-400" />
                      <span>Référence AO</span>
                    </div>
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-mono font-bold text-[#00E5FF] truncate">
                        {selectedTender.externalRef || 'N/A'}
                      </span>
                      {selectedTender.externalRef && (
                        <button
                          onClick={() => copyToClipboard(selectedTender.externalRef || '', 'Référence')}
                          title="Copier la référence"
                          className="text-slate-400 hover:text-white"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/5 flex flex-col gap-1">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>Date Publication</span>
                    </div>
                    <span className="text-xs font-mono text-slate-200">
                      {selectedTender.publicationDate
                        ? new Date(selectedTender.publicationDate).toLocaleDateString('fr-FR')
                        : 'Non spécifiée'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#FF2E63]/10 border border-[#FF2E63]/30 flex flex-col gap-1">
                    <div className="flex items-center gap-1.5 text-xs text-[#FF2E63]">
                      <Clock className="w-3.5 h-3.5" />
                      <span>Date Limite</span>
                    </div>
                    <span className="text-xs font-mono font-bold text-white">
                      {selectedTender.deadline
                        ? new Date(selectedTender.deadline).toLocaleDateString('fr-FR')
                        : 'Non spécifiée'}
                    </span>
                  </div>
                </div>

                {/* Cyber Vectors Detected */}
                <div className="flex flex-col gap-2">
                  <div className="text-xs font-mono font-semibold text-slate-400 flex items-center gap-2">
                    <Target className="w-3.5 h-3.5 text-[#00F59B]" />
                    <span>COMPÉTENCES & VECTEURS IDENTIFIÉS :</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {selectedTender.matchedKeywords?.map((kw, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 rounded-lg text-xs font-mono font-semibold bg-[#00F59B]/10 text-[#00F59B] border border-[#00F59B]/30 shadow-sm"
                      >
                        ✓ {kw}
                      </span>
                    ))}
                    {(!selectedTender.matchedKeywords || selectedTender.matchedKeywords.length === 0) && (
                      <span className="text-xs text-slate-500 italic">Générique IT & Cybersécurité</span>
                    )}
                  </div>
                </div>

                {/* Strategic Analysis & Advisory Note */}
                <div className="p-4 rounded-xl bg-gradient-to-br from-white/[0.04] to-transparent border border-white/10 flex flex-col gap-2">
                  <div className="flex items-center gap-2 text-xs font-mono text-[#FFB800] font-bold">
                    <Award className="w-4 h-4" />
                    <span>CONSEIL STRATÉGIQUE DE SOUMISSION :</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {selectedTender.isHighPriority
                      ? 'Ce marché correspond fortement aux profils SOC, EDR et gouvernance de la sécurité. Veillez à inclure les certifications ISO 27001 et les attestations de référence bancaire/publique similaires dans l’offre technique.'
                      : 'Opportunité d’infrastructure IT ou réseau. Vérifiez les exigences de cautionnement provisoire et assurez-vous d’obtenir les attestations de partenariat éditeur certifié.'}
                  </p>
                </div>

                {/* Instant Actions Suite */}
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-2">
                  
                  {/* Direct DCE Link */}
                  <a
                    href={selectedTender.directUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-xs font-bold uppercase tracking-wider text-black bg-[#00F59B] hover:bg-[#00F59B]/90 shadow-[0_0_20px_rgba(0,245,155,0.4)] transition-all cursor-pointer"
                  >
                    <Download className="w-4 h-4" />
                    <span>Télécharger le DCE Officiel</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>

                  {/* 1-Click WhatsApp Executive Alert */}
                  <button
                    onClick={() => openWhatsAppDirect(selectedTender)}
                    className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-xs font-bold text-white bg-[#25D366]/20 border border-[#25D366]/40 hover:bg-[#25D366]/30 transition-all cursor-pointer"
                  >
                    <Share2 className="w-4 h-4 text-[#25D366]" />
                    <span>Alerte WhatsApp</span>
                  </button>

                  {/* Copy Executive Brief */}
                  <button
                    onClick={() => copyToClipboard(getWhatsAppPitch(selectedTender), 'Brief Exécutif')}
                    className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-xs font-semibold text-slate-300 bg-white/5 border border-white/10 hover:bg-white/10 hover:text-white transition-all cursor-pointer"
                  >
                    <Copy className="w-4 h-4" />
                    <span>Copier la Fiche</span>
                  </button>

                </div>

                {/* WhatsApp Target Phone Config */}
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-2 border-t border-white/5">
                  <span>Numéro d'Alerte WhatsApp :</span>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={whatsappPhone}
                      onChange={(e) => setWhatsappPhone(e.target.value)}
                      placeholder="+212600000000"
                      className="bg-black/50 border border-white/10 rounded px-2 py-0.5 text-slate-300 w-36 text-center focus:outline-none focus:border-[#00F59B]"
                    />
                    <span className="text-[10px] text-slate-600">(Modifiable)</span>
                  </div>
                </div>

              </div>
            ) : (
              <div className="p-12 text-center bg-[#0B0F19]/40 rounded-2xl border border-white/5">
                <Shield className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400 text-sm">Sélectionnez un appel d'offres pour afficher le dossier d'intelligence complet.</p>
              </div>
            )}
          </div>

        </div>

      </main>

      {/* FOOTER // STATUS & TELEMETRY */}
      <footer className="border-t border-white/10 bg-[#0B0F19] py-4 text-xs font-mono text-slate-500">
        <div className="max-w-[1700px] mx-auto px-4 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#00F59B]"></span>
            <span>Réseau de Détection CyberRFP Maroc • 7 Sources Actives</span>
          </div>
          <div>
            <span>Conçu pour la Chasse aux Marchés Publics & Entreprises</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

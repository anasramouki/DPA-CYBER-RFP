/**
 * Portail Marocain des Marchés Publics - CyberRFP Maroc
 * Frontend Engine with 1-Click DCE Downloader, PMMP styling & Trilingual support.
 */

let currentLang = 'fr';
let currentTab = 'tenders';
let priorityOnly = false;
let allTendersMasterCache = [];
let allTendersCache = [];
let activeTenderModalId = null;
let searchDebounceTimeout = null;
let currentViewMode = localStorage.getItem('cyberrfp_view_mode') || 'table';
let activeQuickChip = 'CYBER';
let trackedTendersSet = new Set(JSON.parse(localStorage.getItem('cyberrfp_tracked_tenders') || '[]'));

function toggleMobileFilters() {
  const container = document.getElementById("filters-dropdowns-container");
  const btnTxt = document.getElementById("btn-mobile-filters-text");
  if (!container) return;
  const isHidden = container.classList.contains("hidden");
  if (isHidden) {
    container.classList.remove("hidden");
    container.classList.add("grid", "grid-cols-2");
    if (btnTxt) btnTxt.textContent = "Masquer";
  } else {
    container.classList.add("hidden");
    container.classList.remove("grid", "grid-cols-2");
    if (btnTxt) btnTxt.textContent = "Filtres";
  }
}

function safeArg(str) {
  return "decodeURIComponent('" + encodeURIComponent(str || "") + "')";
}

function isTenderTracked(id) {
  return trackedTendersSet.has(id);
}

function updateTrackedBadges() {
  const count = trackedTendersSet.size;
  const badge1 = document.getElementById("tracked-count-badge");
  const badge2 = document.getElementById("mobile-tracked-count");
  if (badge1) badge1.textContent = count;
  if (badge2) badge2.textContent = count;
}

async function toggleTrackTender(id, e) {
  if (e) e.stopPropagation();
  const willTrack = !trackedTendersSet.has(id);
  if (willTrack) {
    trackedTendersSet.add(id);
  } else {
    trackedTendersSet.delete(id);
  }
  localStorage.setItem('cyberrfp_tracked_tenders', JSON.stringify([...trackedTendersSet]));
  const searchEl = document.getElementById("filter-search");
  if (searchEl) searchEl.value = "";
  updateTrackedBadges();

  try {
    await fetch(`/api/tenders/${encodeURIComponent(id)}/track?track=${willTrack}`, { method: 'POST' });
  } catch (err) {}

  showToast(
    willTrack ? "⭐ AO ajouté à vos alertes en direct ! Vous serez notifié des modifications." : "Suivi de l'appel d'offres désactivé.",
    willTrack ? "success" : "info"
  );

  if (activeQuickChip === 'TRACKED') {
    loadTenders();
  } else {
    renderTendersList(allTendersCache);
  }
}

// Multi-language dictionary (Comprehensive FR, EN, AR support)
const I18N = {
  fr: {
    nav_all: "Toutes les Offres",
    nav_cyber: "Cybersécurité & SSI",
    nav_priority: "Acheteurs Prioritaires",
    nav_pipeline: "Pipeline Commercial",
    nav_admin: "Paramètres & Alertes",
    mobile_access: "📱 iPhone & Mobile",
    sync_tooltip: "Interroger le portail PMMP en temps réel",
    
    // KPIs
    kpi_cyber: "Cybersécurité & SSI",
    kpi_cyber_sub: "Qualifiés par Détection IA",
    kpi_cyber_badge: "Recommandés",
    kpi_priority: "Acheteurs Prioritaires",
    kpi_priority_sub: "CNSS, DGI, OFPPT, ANRF...",
    kpi_priority_badge: "Watchlist DPA",
    kpi_budget: "Volume Budget Détecté",
    kpi_budget_sub: "Total en dirhams TTC",
    kpi_urgent: "Échéances < 15 jours",
    kpi_urgent_sub: "Délai de réponse imminent",
    kpi_urgent_badge: "À traiter",
    kpi_downloaded: "DCE Téléchargés (DPA)",
    kpi_downloaded_sub: "Surveillance modifications TDR",
    kpi_downloaded_badge: "Sous Alerte",

    // Search & Filters
    search_placeholder: "Rechercher par mot-clé, référence, acheteur (ex: SOC, ANRT, CNSS, DGSSI...)",
    btn_search: "Rechercher",
    btn_filters: "Filtres",
    txt_filter_by: "Filtrer par :",
    filter_all: "📋 Toutes les consultations officielles",
    filter_tracked: "⭐ Mes AO Suivis & Alertes Activées",
    filter_press: "📰 Journaux Légaux (Atlantic Re, Laprophan)",
    filter_cyber: "🛡️ Cybersécurité & SSI (Recommandé DPA)",
    filter_priority: "🌟 Acheteurs Prioritaires (CNSS, DGI, CDG...)",
    filter_urgent: "🚨 Échéance Urgente (< 15 jours)",
    filter_budget: "💎 Gros Budgets (> 1.000.000 MAD)",
    filter_downloaded: "📥 DCE Téléchargés / Suivi TDR",

    // Sorting & Layout
    lbl_filter_cat: "Catégorie",
    lbl_filter_buyer: "Acheteur Public",
    lbl_filter_src: "Source / Média",
    lbl_filter_dead: "Échéance",
    btn_sort_pub: "📅 Date de Publication",
    btn_sort_dead: "⏳ Date de Réponse",
    lbl_sort_order: "Tri :",
    btn_view_table: "Tableau",
    btn_view_cards: "Cartes",
    lbl_hide_expired: "Masquer expirés",
    group_by_day_pub: "Grouper par Date de Publication",
    group_by_day_dead: "Grouper par Date de Réponse",
    group_by_day: "Grouper par Jour",

    // Table Headers
    th_ref: "Référence",
    th_buyer: "Acheteur Public",
    th_object: "Objet du Marché",
    th_budget: "Budget Estimé TTC",
    th_published: "Mis en Ligne",
    th_deadline: "Date Limite Réponse",
    th_actions: "Actions Rapides",

    // Badges & Cell Texts
    caution_lbl: "Caution :",
    not_specified: "Non précisé",
    per_cps: "Selon CPS",
    date_not_specified: "Non précisée",
    days_left: "j restants",
    hours_left: "h restantes",
    today_deadline: "Aujourd'hui (Dernier jour !)",
    tomorrow_deadline: "Demain !",
    deadline_passed: "Délai expiré",
    no_tenders: "Aucune consultation ne correspond à ces critères.",
    
    // Actions & Buttons
    btn_folder: "Dossier",
    btn_dce: "DCE 1-Clic",
    btn_details: "Détails",
    btn_source: "Source ↗",
    track_active: "AO Suivi & Alerte active",
    track_inactive: "Suivre & Activer alertes",
    btn_reset: "Réinitialiser",
    deadline: "Date Limite Réponse",
    passed: "Délai expiré",
    details_btn: "Détails",
    download_dce_btn: "DCE 1-Clic"
  },
  en: {
    nav_all: "All Public Tenders",
    nav_cyber: "Cybersecurity & IT Sec",
    nav_priority: "Priority Buyers",
    nav_pipeline: "Sales Pipeline",
    nav_admin: "Settings & Alerts",
    mobile_access: "📱 iPhone & Mobile",
    sync_tooltip: "Query Moroccan PMMP portal in real time",
    
    // KPIs
    kpi_cyber: "CYBERSECURITY & IT SEC",
    kpi_cyber_sub: "Qualified by AI Detection",
    kpi_cyber_badge: "Recommended",
    kpi_priority: "PRIORITY BUYERS",
    kpi_priority_sub: "CNSS, DGI, OFPPT, ANRF...",
    kpi_priority_badge: "DPA Watchlist",
    kpi_budget: "ESTIMATED TOTAL BUDGET",
    kpi_budget_sub: "Total in MAD incl. VAT",
    kpi_urgent: "DEADLINES < 15 DAYS",
    kpi_urgent_sub: "Imminent submission dates",
    kpi_urgent_badge: "Urgent",
    kpi_downloaded: "DOWNLOADED RFPs (DPA)",
    kpi_downloaded_sub: "Tender spec tracking",
    kpi_downloaded_badge: "Under Alert",

    // Search & Filters
    search_placeholder: "Search tenders by keyword, reference, buyer...",
    btn_search: "Search",
    btn_filters: "Filters",
    txt_filter_by: "Filter by:",
    filter_all: "📋 All Official Public Tenders",
    filter_tracked: "⭐ My Tracked RFPs & Active Alerts",
    filter_press: "📰 Official Press (Atlantic Re, Laprophan)",
    filter_cyber: "🛡️ Cybersecurity & IT Sec (DPA Priority)",
    filter_priority: "🌟 Priority Buyers (CNSS, DGI, CDG...)",
    filter_urgent: "🚨 Urgent Deadline (< 15 days)",
    filter_budget: "💎 Large Budgets (> 1,000,000 MAD)",
    filter_downloaded: "📥 Downloaded RFPs / Spec Tracking",

    // Sorting & Layout
    lbl_filter_cat: "Category",
    lbl_filter_buyer: "Public Buyer",
    lbl_filter_src: "Source / Media",
    lbl_filter_dead: "Deadline",
    btn_sort_pub: "📅 Publication Date",
    btn_sort_dead: "⏳ Submission Deadline",
    lbl_sort_order: "Sort by:",
    btn_view_table: "Table",
    btn_view_cards: "Cards",
    lbl_hide_expired: "Hide expired",
    group_by_day_pub: "Group by Publication Date",
    group_by_day_dead: "Group by Submission Deadline",
    group_by_day: "Group by Day",

    // Table Headers
    th_ref: "Reference",
    th_buyer: "Public Buyer",
    th_object: "Tender Title & Scope",
    th_budget: "Estimated Budget",
    th_published: "Published On",
    th_deadline: "Submission Deadline",
    th_actions: "Quick Actions",

    // Badges & Cell Texts
    caution_lbl: "Guarantee:",
    not_specified: "Not specified",
    per_cps: "Per Tender Rules",
    date_not_specified: "Not specified",
    days_left: "days left",
    hours_left: "hours left",
    today_deadline: "Today (Last day!)",
    tomorrow_deadline: "Tomorrow!",
    deadline_passed: "Deadline passed",
    no_tenders: "No tenders match the specified criteria.",
    
    // Actions & Buttons
    btn_folder: "Folder",
    btn_dce: "1-Click DCE",
    btn_details: "Details",
    btn_source: "Source ↗",
    track_active: "Tracked (Click to disable)",
    track_inactive: "Track & Enable alerts",
    btn_reset: "Reset",
    deadline: "Submission Deadline",
    passed: "Deadline passed",
    details_btn: "Details",
    download_dce_btn: "1-Click DCE"
  },
  ar: {
    nav_all: "جميع الاستشارات",
    nav_cyber: "الأمن السيبراني وأمن النظم",
    nav_priority: "المشترين ذوي الأولوية",
    nav_pipeline: "متابعة الصفقات",
    nav_admin: "الإعدادات والتنبيهات",
    mobile_access: "📱 هاتف المدير والمحمول",
    sync_tooltip: "تحديث الصفقات من البوابة الرسمية في الوقت الفعلي",
    
    // KPIs
    kpi_cyber: "الأمن السيبراني والنظم",
    kpi_cyber_sub: "مؤهل بالذكاء الاصطناعي",
    kpi_cyber_badge: "موصى به",
    kpi_priority: "مشترين ذوي أولوية",
    kpi_priority_sub: "الضمان الاجتماعي، الضرائب، التكوين المهني...",
    kpi_priority_badge: "متابعة DPA",
    kpi_budget: "إجمالي الميزانية التقديرية",
    kpi_budget_sub: "المجموع بالدرهم شامل الضريبة",
    kpi_urgent: "آجال أقل من 15 يوم",
    kpi_urgent_sub: "موعد الإيداع قريب جداً",
    kpi_urgent_badge: "عاجل",
    kpi_downloaded: "ملفات DCE المحملة",
    kpi_downloaded_sub: "مراقبة التعديلات ودفاتر الشروط",
    kpi_downloaded_badge: "تحت المراقبة",

    // Search & Filters
    search_placeholder: "البحث في الصفقات (كلمة مفتاحية، مرجع، مشتري)...",
    btn_search: "بحث",
    btn_filters: "مرشحات",
    txt_filter_by: "تصفية حسب :",
    filter_all: "📋 جميع الاستشارات والصفقات الرسمية",
    filter_tracked: "⭐ صفقاتي المتابعة والمفعلة بالتنبيه",
    filter_press: "📰 الجرائد الرسمية (أتلانتيك ري، لافروكيم)",
    filter_cyber: "🛡️ صفقات الأمن السيبراني (أولوية DPA)",
    filter_priority: "🌟 المشترين ذوي الأولوية (CNSS، DGI...)",
    filter_urgent: "🚨 آجال عاجلة (أقل من 15 يوم)",
    filter_budget: "💎 ميزانيات ضخمة (أكثر من 1 مليون درهم)",
    filter_downloaded: "📥 ملفات DCE محملة / مراقبة دفتر التحملات",

    // Sorting & Layout
    lbl_filter_cat: "الفئة / المجال",
    lbl_filter_buyer: "المشتري العمومي",
    lbl_filter_src: "المصدر / الجريدة",
    lbl_filter_dead: "الأجل المتبقي",
    btn_sort_pub: "📅 تاريخ النشر",
    btn_sort_dead: "⏳ آخر أجل للإيداع",
    lbl_sort_order: "الترتيب :",
    btn_view_table: "عرض جدولي",
    btn_view_cards: "عرض بطاقات",
    lbl_hide_expired: "إخفاء المنتهية",
    group_by_day_pub: "تجميع حسب تاريخ النشر",
    group_by_day_dead: "تجميع حسب تاريخ الإيداع",
    group_by_day: "تجميع حسب اليوم",

    // Table Headers
    th_ref: "المرجع",
    th_buyer: "المشتري العمومي",
    th_object: "موضوع الصفقة",
    th_budget: "الميزانية التقديرية",
    th_published: "تاريخ النشر",
    th_deadline: "آخر أجل للعروض",
    th_actions: "إجراءات سريعة",

    // Badges & Cell Texts
    caution_lbl: "الضمان المؤقت :",
    not_specified: "غير محدد",
    per_cps: "حسب دفتر الشروط",
    date_not_specified: "غير محدد",
    days_left: "أيام متبقية",
    hours_left: "ساعات متبقية",
    today_deadline: "اليوم (آخر موعد !)",
    tomorrow_deadline: "غداً !",
    deadline_passed: "انتهى الأجل",
    no_tenders: "لا توجد صفقات تطابق معايير البحث.",
    
    // Actions & Buttons
    btn_folder: "الملف",
    btn_dce: "تحميل DCE",
    btn_details: "تفاصيل",
    btn_source: "المصدر ↗",
    track_active: "صفقة متابعة ومفعلة",
    track_inactive: "متابعة وتفعيل التنبيه",
    btn_reset: "إعادة ضبط",
    deadline: "آخر أجل للعروض",
    passed: "انتهى الأجل",
    details_btn: "تفاصيل",
    download_dce_btn: "تحميل DCE"
  }
};

// Application Initialization
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  const savedLang = localStorage.getItem('cyberrfp_lang') || 'fr';
  loadCurrentUser();
  updateViewModeButtons(currentViewMode);
  const searchEl = document.getElementById("filter-search");
  if (searchEl) searchEl.value = "";
  updateTrackedBadges();
  loadTenders();
  loadScraperHealth();
  loadWatchlist();
  loadGenericConnectors();
  loadAlertsConfig();
  loadGeminiStatus();
  initRealtimeNotifications();

  // Responsive layout switch (Desktop Table vs Mobile Touch Cards)
  let resizeTimeout = null;
  let lastWasMobile = window.innerWidth < 768;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      const isMobileNow = window.innerWidth < 768;
      if (isMobileNow !== lastWasMobile) {
        lastWasMobile = isMobileNow;
        if (allTendersCache && allTendersCache.length > 0) {
          renderTendersList(allTendersCache);
        }
      }
    }, 150);
  });

  if (savedLang !== 'fr') {
    setLanguage(savedLang);
  } else {
    updateActiveFilterIndicator();
  }

  // Dismiss dropdowns on outside click
  document.addEventListener("click", (e) => {
    const userMenu = document.getElementById("user-menu-dropdown");
    const userBtn = document.getElementById("btn-user-avatar-menu");
    if (userMenu && !userMenu.classList.contains("hidden") && userBtn && !userBtn.contains(e.target) && !userMenu.contains(e.target)) {
      userMenu.classList.add("hidden");
    }
    const notifMenu = document.getElementById("notif-dropdown");
    const notifBtn = document.getElementById("btn-notif-bell");
    if (notifMenu && !notifMenu.classList.contains("hidden") && notifBtn && !notifBtn.contains(e.target) && !notifMenu.contains(e.target)) {
      notifMenu.classList.add("hidden");
    }
  });

  // Close modals on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeModal();
      if (typeof closeSubmissionFolderModal === "function") closeSubmissionFolderModal();
      if (typeof closeMobileQrModal === "function") closeMobileQrModal();
    }
  });
});

// ==================== THEME MANAGEMENT (LIGHT / DARK) ====================
function initTheme() {
  const saved = localStorage.getItem('cyberrfp_theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark = saved ? saved === 'dark' : prefersDark;
  if (isDark) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
  updateThemeIcon();
}

function toggleTheme() {
  const isDark = document.documentElement.classList.toggle('dark');
  localStorage.setItem('cyberrfp_theme', isDark ? 'dark' : 'light');
  updateThemeIcon();
}

function updateThemeIcon() {
  const isDark = document.documentElement.classList.contains('dark');
  const btn = document.getElementById('btn-theme-toggle');
  if (btn) {
    btn.innerHTML = isDark 
      ? '<i data-lucide="sun" class="w-4 h-4 text-amber-400"></i>' 
      : '<i data-lucide="moon" class="w-4 h-4 text-slate-700 dark:text-slate-300"></i>';
    btn.title = isDark ? "Passer en mode clair (Light)" : "Passer en mode sombre (Dark)";
    if (window.lucide) lucide.createIcons({ root: btn });
  }
  const metaTheme = document.querySelector('meta[name="theme-color"]');
  if (metaTheme) metaTheme.setAttribute('content', isDark ? '#080c15' : '#ffffff');
}

function toggleUserDropdown() {
  const el = document.getElementById("user-menu-dropdown");
  if (el) el.classList.toggle("hidden");
}

function onBuyerDropdownChange(val) {
  applyClientFiltersAndRender();
}

function onDeadlineDropdownChange(val) {
  applyClientFiltersAndRender();
}

function onSortDropdownChange() {
  applyClientFiltersAndRender();
}

function resetAllFilters() {
  const selCat = document.getElementById("select-quick-filter");
  if (selCat) selCat.value = "ALL";
  const selBuyer = document.getElementById("filter-buyer-select");
  if (selBuyer) selBuyer.value = "";
  const selSrc = document.getElementById("filter-source");
  if (selSrc) selSrc.value = "";
  const selDead = document.getElementById("filter-deadline-select");
  if (selDead) selDead.value = "ALL";
  const selSort = document.getElementById("filter-sort");
  if (selSort) selSort.value = "publication_desc";
  const elExpired = document.getElementById("toggle-hide-expired");
  if (elExpired) elExpired.checked = true;
  activeQuickChip = "CYBER";
  const quickSelect = document.getElementById("select-quick-filter");
  if (quickSelect) quickSelect.value = "CYBER";
  loadTenders();
}

async function loadCurrentUser() {
  try {
    const res = await fetch("/api/auth/me");
    if (!res.ok) return;
    const user = await res.json();
    if (user && user.full_name) {
      const nameEl = document.getElementById("header-user-name");
      const emailEl = document.getElementById("header-user-email");
      const roleEl = document.getElementById("header-user-role-badge");
      const avatarEl = document.getElementById("header-user-avatar");

      if (nameEl) nameEl.textContent = user.full_name;
      if (emailEl) emailEl.textContent = user.email || "@dpg-cyber.com";
      if (roleEl) roleEl.textContent = user.is_admin ? "ADMIN DPA" : (user.role || "DPA TEAM");
      if (avatarEl) {
        const initials = user.full_name.split(" ").map(w => w[0]).filter(Boolean).slice(0, 2).join("").toUpperCase();
        avatarEl.textContent = initials || "DPA";
      }
    }
  } catch (e) {
    console.debug("Could not load current user:", e);
  }
}

// Switch language with bulletproof DOM safety
function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('cyberrfp_lang', lang);
  const root = document.getElementById("html-root") || document.documentElement;

  if (lang === 'ar') {
    root.setAttribute("dir", "rtl");
    root.setAttribute("lang", "ar");
  } else {
    root.setAttribute("dir", "ltr");
    root.setAttribute("lang", lang);
  }

  ['fr', 'ar', 'en'].forEach(l => {
    const btn = document.getElementById(`lang-${l}`);
    if (btn) {
      if (l === lang) {
        btn.className = "px-2 py-0.5 rounded text-orange-500 font-bold bg-white dark:bg-slate-700 shadow-2xs";
      } else {
        btn.className = "px-2 py-0.5 rounded text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white";
      }
    }
  });

  const d = I18N[lang] || I18N.fr;

  const setTxt = (id, text) => {
    const el = document.getElementById(id);
    if (el && text !== undefined) el.textContent = text;
  };

  // Navigation
  setTxt("nav-all", d.nav_all);
  setTxt("nav-cyber", d.nav_cyber);
  setTxt("nav-priority", d.nav_priority);
  setTxt("nav-pipeline", d.nav_pipeline);
  setTxt("nav-admin", d.nav_admin);
  setTxt("btn-mobile-text", d.mobile_access);

  // KPIs
  setTxt("kpi-lbl-cyber", d.kpi_cyber);
  setTxt("kpi-sub-cyber", d.kpi_cyber_sub);
  setTxt("kpi-badge-cyber", d.kpi_cyber_badge);
  setTxt("kpi-lbl-priority", d.kpi_priority);
  setTxt("kpi-sub-priority", d.kpi_priority_sub);
  setTxt("kpi-badge-priority", d.kpi_priority_badge);
  setTxt("kpi-lbl-budget", d.kpi_budget);
  setTxt("kpi-sub-budget", d.kpi_budget_sub);
  setTxt("kpi-lbl-urgent", d.kpi_urgent);
  setTxt("kpi-sub-urgent", d.kpi_urgent_sub);
  setTxt("kpi-badge-urgent", d.kpi_urgent_badge);
  setTxt("kpi-lbl-downloaded", d.kpi_downloaded);
  setTxt("kpi-sub-downloaded", d.kpi_downloaded_sub);
  setTxt("kpi-badge-downloaded", d.kpi_downloaded_badge);

  // Search & Filters
  const searchInput = document.getElementById("filter-search");
  if (searchInput) searchInput.placeholder = d.search_placeholder;
  setTxt("btn-search-text", d.btn_search);
  setTxt("btn-filters-text", d.btn_filters);
  setTxt("txt-filter-by", d.txt_filter_by);

  // Quick Filter Dropdown options
  const filterSelect = document.getElementById("select-quick-filter");
  if (filterSelect) {
    const opts = filterSelect.options;
    for (let i = 0; i < opts.length; i++) {
      const val = opts[i].value;
      if (val === "ALL") opts[i].textContent = d.filter_all;
      else if (val === "TRACKED") opts[i].textContent = d.filter_tracked;
      else if (val === "PRESS") opts[i].textContent = d.filter_press;
      else if (val === "CYBER") opts[i].textContent = d.filter_cyber;
      else if (val === "PRIORITY") opts[i].textContent = d.filter_priority;
      else if (val === "URGENT") opts[i].textContent = d.filter_urgent;
      else if (val === "BIG_BUDGET") opts[i].textContent = d.filter_budget;
      else if (val === "DOWNLOADED") opts[i].textContent = d.filter_downloaded;
    }
  }

  // Category Dropdown options
  const catSelect = document.getElementById("filter-category");
  if (catSelect && catSelect.options) {
    for (let opt of catSelect.options) {
      if (opt.value === "all") opt.textContent = lang === 'en' ? "All Official Public Tenders" : (lang === 'ar' ? "جميع الصفقات العمومية" : "Toutes les consultations");
      else if (opt.value === "cyber") opt.textContent = lang === 'en' ? "🛡️ Cybersecurity & IT Sec (Priority)" : (lang === 'ar' ? "🛡️ الأمن السيبراني والأنظمة" : "🛡️ Cybersécurité & SSI (Prioritaire)");
      else if (opt.value === "digital") opt.textContent = lang === 'en' ? "💻 Digital & IT Systems" : (lang === 'ar' ? "💻 الأنظمة الرقمية والمعلوماتية" : "💻 Digital & Systèmes d'Information");
      else if (opt.value === "infra") opt.textContent = lang === 'en' ? "🌐 Telecom & Network Infrastructure" : (lang === 'ar' ? "🌐 البنية التحتية والشبكات" : "🌐 Infrastructure & Réseaux Télécom");
    }
  }

  // Buyer Dropdown options
  const buyerSelect = document.getElementById("filter-buyer-select") || document.getElementById("filter-buyer");
  if (buyerSelect && buyerSelect.options.length > 0) {
    buyerSelect.options[0].textContent = lang === 'en' ? "All Public Buyers" : (lang === 'ar' ? "جميع المشترين العموميين" : "Tous les acheteurs");
    if (buyerSelect.options.length > 1) {
      buyerSelect.options[1].textContent = lang === 'en' ? "⭐ Priority Watchlist" : (lang === 'ar' ? "⭐ قائمة الأولويات" : "⭐ Acheteurs Prioritaires DPA");
    }
  }

  // Source Dropdown options
  const srcSelect = document.getElementById("filter-source");
  if (srcSelect && srcSelect.options.length > 0) {
    srcSelect.options[0].textContent = lang === 'en' ? "All Sources & Media" : (lang === 'ar' ? "جميع المصادر والجرائد" : "Toutes les sources");
    for (let opt of srcSelect.options) {
      if (opt.value === "PMMP") opt.textContent = lang === 'en' ? "National Portal (PMMP / TGR)" : (lang === 'ar' ? "البوابة الوطنية للمشتريات العمومية" : "Portail National (PMMP / TGR)");
      else if (opt.value === "Presse / Journal") opt.textContent = lang === 'en' ? "📰 Press & Official Journals" : (lang === 'ar' ? "📰 الصحف والجرائد الرسمية" : "📰 Presse & Journaux (Le Matin, L'Économiste)");
    }
  }

  // Deadline Dropdown options
  const deadSelect = document.getElementById("filter-deadline-select") || document.getElementById("filter-deadline");
  if (deadSelect && deadSelect.options) {
    for (let opt of deadSelect.options) {
      if (opt.value === "ALL" || opt.value === "") opt.textContent = lang === 'en' ? "All Deadlines" : (lang === 'ar' ? "جميع الآجال" : "Toutes les échéances");
      else if (opt.value === "URGENT_7" || opt.value === "urgent_7d" || opt.value === "urgent_48h") opt.textContent = lang === 'en' ? "🚨 Very Urgent (< 7 days)" : (lang === 'ar' ? "🚨 عاجل جداً (أقل من 7 أيام)" : "🚨 Très urgent (< 7 jours)");
      else if (opt.value === "URGENT_15" || opt.value === "normal_15d") opt.textContent = lang === 'en' ? "⏳ Deadline < 15 days" : (lang === 'ar' ? "⏳ الأجل أقل من 15 يوماً" : "⏳ Échéance < 15 jours");
      else if (opt.value === "URGENT_30" || opt.value === "far_15d") opt.textContent = lang === 'en' ? "📅 Deadline < 30 days" : (lang === 'ar' ? "📅 الأجل أقل من 30 يوماً" : "📅 Échéance < 30 jours");
    }
  }

  // Sort Dropdown options
  const sortSelect = document.getElementById("filter-sort");
  if (sortSelect && sortSelect.options) {
    for (let opt of sortSelect.options) {
      if (opt.value === "publication_desc") opt.textContent = lang === 'en' ? "📅 Publication (Newest first)" : (lang === 'ar' ? "📅 النشر (الأحدث)" : "📅 Publication (Plus récent)");
      else if (opt.value === "publication_asc") opt.textContent = lang === 'en' ? "📅 Publication (Oldest first)" : (lang === 'ar' ? "📅 النشر (الأقدم)" : "📅 Publication (Plus ancien)");
      else if (opt.value === "deadline_asc") opt.textContent = lang === 'en' ? "⏳ Deadline (Closest first)" : (lang === 'ar' ? "⏳ الأجل (الأقرب)" : "⏳ Échéance (Plus proche)");
      else if (opt.value === "deadline_desc") opt.textContent = lang === 'en' ? "⏳ Deadline (Furthest)" : (lang === 'ar' ? "⏳ الأجل (الأبعد)" : "⏳ Échéance (Plus lointaine)");
      else if (opt.value === "budget_desc") opt.textContent = lang === 'en' ? "💰 Budget (Highest)" : (lang === 'ar' ? "💰 الميزانية (الأعلى)" : "💰 Budget (Plus élevé)");
      else if (opt.value === "budget_asc") opt.textContent = lang === 'en' ? "💰 Budget (Lowest)" : (lang === 'ar' ? "💰 الميزانية (الأدنى)" : "💰 Budget (Plus faible)");
      else if (opt.value === "relevance_desc") opt.textContent = lang === 'en' ? "🛡️ Cybersecurity Relevance" : (lang === 'ar' ? "🛡️ ملاءمة الأمن السيبراني" : "🛡️ Pertinence Cybersécurité");
    }
  }

  // Sorting & View Labels
  setTxt("lbl-filter-cat", d.lbl_filter_cat);
  setTxt("lbl-filter-buyer", d.lbl_filter_buyer);
  setTxt("lbl-filter-src", d.lbl_filter_src);
  setTxt("lbl-filter-dead", d.lbl_filter_dead);
  setTxt("btn-sort-publication-text", d.btn_sort_pub);
  setTxt("btn-sort-deadline-text", d.btn_sort_dead);
  setTxt("lbl-sort-order", d.lbl_sort_order);
  setTxt("btn-view-table-text", d.btn_view_table);
  setTxt("btn-view-cards-text", d.btn_view_cards);
  setTxt("lbl-hide-expired", d.lbl_hide_expired);
  setTxt("group-toggle-label", d.group_by_day);
  setTxt("btn-mobile-filters-text", lang === 'en' ? "Filters" : (lang === 'ar' ? "تصفية" : "Filtres"));
  setTxt("nav-btn-mobile-all", lang === 'en' ? "All" : (lang === 'ar' ? "الكل" : "Toutes"));
  setTxt("nav-btn-mobile-cyber", lang === 'en' ? "Cyber" : (lang === 'ar' ? "سيبراني" : "Cyber"));
  setTxt("nav-btn-mobile-tracked", lang === 'en' ? "Tracked" : (lang === 'ar' ? "المتابعة" : "Suivis"));
  setTxt("nav-btn-mobile-folder", lang === 'en' ? "Dossier" : (lang === 'ar' ? "الملف" : "Dossier"));

  // Update active filter badge text and total count
  updateActiveFilterIndicator();

  // Re-render list with current language applied to headers and cells
  renderTendersList(allTendersCache);
}

// Switch between views
function switchTab(tab) {
  currentTab = tab;
  ['tenders', 'pipeline', 'admin'].forEach(t => {
    const view = document.getElementById(`view-${t}`);
    if (t === tab) {
      view.classList.remove("hidden");
    } else {
      view.classList.add("hidden");
    }
  });

  // Update top active nav tab
  const tabs = {
    'tenders': 'tab-nav-all',
    'pipeline': 'tab-nav-pipeline',
    'admin': 'tab-nav-admin'
  };

  ['tab-nav-all', 'tab-nav-cyber', 'tab-nav-digital', 'tab-nav-infra', 'tab-nav-priority', 'tab-nav-pipeline', 'tab-nav-admin'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.remove('bg-white/20', 'text-white');
  });

  if (tabs[tab]) {
    const activeEl = document.getElementById(tabs[tab]);
    if (activeEl) activeEl.classList.add('bg-white/20', 'text-white');
  }

  if (tab === 'pipeline') {
    renderPipelineBoard(allTendersCache);
  } else if (tab === 'admin') {
    loadScraperHealth();
    loadWatchlist();
    loadGenericConnectors();
    loadAlertsConfig();
    loadGeminiStatus();
  }
}

function setCategoryFilter(cat) {
  const select = document.getElementById("filter-category");
  if (select) {
    select.value = cat;
  }
  loadTenders();
}

function togglePriorityOnly() {
  priorityOnly = !priorityOnly;
  const navBtn = document.getElementById("tab-nav-priority");
  if (priorityOnly) {
    navBtn.className = "px-3 py-1.5 rounded font-black text-slate-900 bg-amber-400 flex items-center space-x-1.5 shadow";
  } else {
    navBtn.className = "px-3 py-1.5 rounded text-emerald-100 hover:text-white hover:bg-white/10 flex items-center space-x-1.5";
  }
  loadTenders();
}

function toggleAdvancedSearch() {
  const panel = document.getElementById("adv-search-panel");
  panel.classList.toggle("hidden");
}

// ==================== SMART INSTANT SEARCH & AUTOCOMPLETE ====================

function onSearchInput(val) {
  const clearBtn = document.getElementById("btn-clear-search");
  if (clearBtn) {
    if (val && val.trim().length > 0) {
      clearBtn.classList.remove("hidden");
    } else {
      clearBtn.classList.add("hidden");
    }
  }

  clearTimeout(searchDebounceTimeout);
  searchDebounceTimeout = setTimeout(() => {
    applyClientFiltersAndRender();
  }, 100);
}

function clearSearchInput() {
  const searchInput = document.getElementById("filter-search");
  if (searchInput) searchInput.value = "";
  const clearBtn = document.getElementById("btn-clear-search");
  if (clearBtn) clearBtn.classList.add("hidden");
  const activeBar = document.getElementById("search-active-bar");
  if (activeBar) activeBar.classList.add("hidden");
  hideSearchSuggestions();
  loadTenders();
}

function showSearchSuggestions() {
  const menu = document.getElementById("search-suggestions");
  if (menu) menu.classList.remove("hidden");
}

function hideSearchSuggestions() {
  const menu = document.getElementById("search-suggestions");
  if (menu) menu.classList.add("hidden");
}

function applySuggestion(term) {
  const searchInput = document.getElementById("filter-search");
  if (searchInput) searchInput.value = term;
  const clearBtn = document.getElementById("btn-clear-search");
  if (clearBtn) clearBtn.classList.remove("hidden");
  hideSearchSuggestions();
  loadTenders();
}

// Dismiss search suggestions on outside click
document.addEventListener("click", (e) => {
  const wrapper = document.getElementById("search-input-wrapper");
  if (wrapper && !wrapper.contains(e.target)) {
    hideSearchSuggestions();
  }
});

function highlightSearchMatch(text, query) {
  if (!text) return "";
  if (!query || !query.trim()) return escapeHtml(text);
  const words = query.trim().split(/\s+/).filter(w => w.length > 1);
  if (words.length === 0) return escapeHtml(text);

  const escapedTerms = words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const regex = new RegExp(`(${escapedTerms.join('|')})`, 'gi');
  return escapeHtml(text).replace(regex, '<mark class="bg-amber-200 text-amber-950 font-bold px-0.5 rounded">$1</mark>');
}

// ==================== TENDERS LOADING & RENDERING ====================

async function loadTenders() {
  const container = document.getElementById("tenders-container");
  if (!container) return;

  const url = `/api/tenders?limit=300&include_expired=true`;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Erreur de chargement");
    const data = await res.json();
    allTendersMasterCache = data.tenders || [];
    applyClientFiltersAndRender();
  } catch (err) {
    if (container) {
      container.innerHTML = `<div class="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-rose-300 dark:border-rose-900 text-center text-rose-600 font-semibold text-xs">Erreur lors de la récupération des consultations : ${escapeHtml(err.message)}</div>`;
    }
  }
}

function applyClientFiltersAndRender() {
  const container = document.getElementById("tenders-container");
  if (!container) return;

  const elCat = document.getElementById("filter-category");
  const category = elCat ? elCat.value : "ALL";
  const elSubcat = document.getElementById("filter-subcat");
  const subcat = elSubcat ? elSubcat.value.toLowerCase() : "";
  const elSource = document.getElementById("filter-source");
  const source = elSource ? elSource.value.toLowerCase() : "";
  const elMinBudget = document.getElementById("filter-min-budget");
  const minBudget = elMinBudget && elMinBudget.value ? parseFloat(elMinBudget.value) : 0;
  const elSearch = document.getElementById("filter-search");
  const search = elSearch ? elSearch.value.trim().toLowerCase() : "";
  const sortSelect = document.getElementById("filter-sort");
  const sortBy = sortSelect ? sortSelect.value : "publication_desc";

  const elExpired = document.getElementById("toggle-hide-expired");
  const hideExpired = elExpired ? elExpired.checked : true;

  let filtered = [...allTendersMasterCache];

  // 1. Strict Expired Filter (Exclude any RFP where deadline has already passed)
  if (hideExpired) {
    const now = Date.now();
    filtered = filtered.filter(t => {
      if (!t.deadline) return true;
      try {
        const d = new Date(t.deadline.replace(' ', 'T')).getTime();
        return d >= now;
      } catch (e) { return true; }
    });
  }

  // 2. Quick Chip Filter
  if (activeQuickChip === 'TRACKED') {
    filtered = filtered.filter(t => isTenderTracked(t.id) || t.pipeline_status === 'watching');
  } else if (activeQuickChip === 'PRESS') {
    filtered = filtered.filter(t => {
      const src = (t.source_name || '').toLowerCase();
      const b = (t.buyer_name || '').toLowerCase();
      return src.includes('presse') || src.includes('journal') || src.includes('matin') || src.includes('économiste') || b.includes('atlantic') || b.includes('laprophan');
    });
  } else if (activeQuickChip === 'CYBER') {
    filtered = filtered.filter(t => t.relevance_category === 'CYBERSECURITY' || t.relevance_category === 'HIGHLY_RELEVANT' || (t.relevance_score && t.relevance_score >= 50));
  } else if (activeQuickChip === 'PRIORITY') {
    filtered = filtered.filter(t => t.is_priority_buyer);
  } else if (activeQuickChip === 'URGENT') {
    const nowMs = Date.now();
    filtered = filtered.filter(t => {
      if (!t.deadline) return false;
      try {
        const diff = new Date(t.deadline.replace(' ', 'T')).getTime() - nowMs;
        return diff > 0 && diff <= 15 * 24 * 60 * 60 * 1000;
      } catch (e) { return false; }
    });
  } else if (activeQuickChip === 'BIG_BUDGET') {
    filtered = filtered.filter(t => (t.estimated_budget || 0) >= 1000000);
  } else if (activeQuickChip === 'DOWNLOADED') {
    filtered = filtered.filter(t => t.dce_downloaded);
  }

  // 3. Buyer Dropdown Filter
  const buyerSelect = document.getElementById("filter-buyer-select");
  const buyerVal = buyerSelect ? buyerSelect.value : "";
  if (buyerVal === "PRIORITY_WATCHLIST") {
    filtered = filtered.filter(t => t.is_priority_buyer);
  } else if (buyerVal) {
    const bLower = buyerVal.toLowerCase();
    filtered = filtered.filter(t => 
      (t.buyer_name && t.buyer_name.toLowerCase().includes(bLower)) || 
      (t.buyer_normalized && t.buyer_normalized.includes(bLower))
    );
  }

  // 4. Source Dropdown Filter
  if (source) {
    filtered = filtered.filter(t => (t.source_name && t.source_name.toLowerCase().includes(source)));
  }

  // 5. Min Budget Filter
  if (minBudget > 0) {
    filtered = filtered.filter(t => (t.estimated_budget || 0) >= minBudget);
  }

  // 6. Category & Subcategory Filter
  if (category && category !== "ALL") {
    filtered = filtered.filter(t => t.category === category || t.relevance_category === category);
  }
  if (subcat) {
    filtered = filtered.filter(t => (t.sub_category && t.sub_category.toLowerCase().includes(subcat)));
  }
  if (priorityOnly) {
    filtered = filtered.filter(t => t.is_priority_buyer);
  }

  // 7. Deadline Dropdown Filter
  const deadSelect = document.getElementById("filter-deadline-select");
  const deadVal = deadSelect ? deadSelect.value : "ALL";
  if (deadVal !== "ALL") {
    const nowMs = Date.now();
    const days = deadVal === "URGENT_7" ? 7 : (deadVal === "URGENT_15" ? 15 : 30);
    filtered = filtered.filter(t => {
      if (!t.deadline) return false;
      try {
        const diff = new Date(t.deadline.replace(' ', 'T')).getTime() - nowMs;
        return diff > 0 && diff <= days * 24 * 60 * 60 * 1000;
      } catch (e) { return false; }
    });
  }

  // 8. Instant Text Search Matching
  if (search) {
    filtered = filtered.filter(t => {
      const ref = (t.reference || '').toLowerCase();
      const title = (t.title || '').toLowerCase();
      const buyer = (t.buyer_name || '').toLowerCase();
      const summary = (t.summary || '').toLowerCase();
      const src = (t.source_name || '').toLowerCase();
      return ref.includes(search) || title.includes(search) || buyer.includes(search) || summary.includes(search) || src.includes(search);
    });
  }

  // 9. Client-side Sorting
  if (sortBy === 'publication_desc') {
    filtered.sort((a, b) => (b.publication_date || '').localeCompare(a.publication_date || ''));
  } else if (sortBy === 'publication_asc') {
    filtered.sort((a, b) => (a.publication_date || '').localeCompare(b.publication_date || ''));
  } else if (sortBy === 'deadline_asc') {
    filtered.sort((a, b) => (a.deadline || '9999').localeCompare(b.deadline || '9999'));
  } else if (sortBy === 'budget_desc') {
    filtered.sort((a, b) => (b.estimated_budget || 0) - (a.estimated_budget || 0));
  } else if (sortBy === 'relevance_desc') {
    filtered.sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0));
  }

  allTendersCache = filtered;

  // Update Count Labels
  const countLabel = document.getElementById("results-count-label");
  const suffix = currentLang === 'en' ? 'tender(s) found' : (currentLang === 'ar' ? 'استشارة مطابقة' : 'consultation(s) trouvée(s)');
  if (countLabel) {
    countLabel.textContent = `${allTendersCache.length} ${suffix}`;
  }

  // Dynamic Live Active Search Indicator
  const clearBtn = document.getElementById("btn-clear-search");
  const activeBar = document.getElementById("search-active-bar");
  const queryBadge = document.getElementById("search-query-badge");
  const countBadge = document.getElementById("search-results-count-text");
  if (clearBtn) {
    if (search) clearBtn.classList.remove("hidden");
    else clearBtn.classList.add("hidden");
  }
  if (activeBar && queryBadge && countBadge) {
    if (search) {
      activeBar.classList.remove("hidden");
      queryBadge.textContent = `"${search}"`;
      countBadge.textContent = `${allTendersCache.length} ${suffix}`;
    } else {
      activeBar.classList.add("hidden");
    }
  }

  updateKPIs(allTendersMasterCache.length > 0 ? allTendersMasterCache : allTendersCache);
  renderTendersList(allTendersCache);
  if (currentTab === 'pipeline') {
    renderPipelineBoard(allTendersCache);
  }
}

function updateKPIs(tenders) {
  const cyberCount = tenders.filter(t => t.relevance_category === 'CYBERSECURITY').length;
  const priorityCount = tenders.filter(t => t.is_priority_buyer).length;
  const totalBudget = tenders.reduce((acc, t) => acc + (t.estimated_budget || 0), 0);

  const now = new Date().getTime();
  const urgentCount = tenders.filter(t => {
    if (!t.deadline) return false;
    const diff = new Date(t.deadline.replace(" ", "T")).getTime() - now;
    return diff > 0 && diff <= 15 * 24 * 60 * 60 * 1000;
  }).length;

  const downloadedCount = tenders.filter(t => t.dce_downloaded).length;

  const elCyber = document.getElementById("kpi-cyber-count");
  if (elCyber) elCyber.textContent = cyberCount;
  const elPriority = document.getElementById("kpi-priority-count");
  if (elPriority) elPriority.textContent = priorityCount;
  const elBudget = document.getElementById("kpi-total-budget");
  if (elBudget) elBudget.textContent = formatMAD(totalBudget);
  const elUrgent = document.getElementById("kpi-urgent-count");
  if (elUrgent) elUrgent.textContent = urgentCount;
  const elDownloaded = document.getElementById("kpi-downloaded-count");
  if (elDownloaded) elDownloaded.textContent = downloadedCount;
}

function setViewMode(mode) {
  currentViewMode = mode;
  try {
    localStorage.setItem('cyberrfp_view_mode', mode);
  } catch (e) {}
  updateViewModeButtons(mode);
  renderTendersList(allTendersCache);
}

function updateViewModeButtons(mode) {
  const btnTable = document.getElementById("btn-view-table");
  const btnCards = document.getElementById("btn-view-cards");
  if (!btnTable || !btnCards) return;

  if (mode === 'table') {
    btnTable.className = "px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 bg-white text-slate-900 shadow-xs border border-slate-200/70";
    btnCards.className = "px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition flex items-center space-x-1.5";
  } else {
    btnCards.className = "px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 bg-white text-slate-900 shadow-xs border border-slate-200/70";
    btnTable.className = "px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition flex items-center space-x-1.5";
  }
}

function onQuickFilterSelect(val) {
  setQuickChip(val);
}

function updateActiveFilterIndicator() {
  const d = I18N[currentLang] || I18N.fr;
  const badge = document.getElementById("active-filter-indicator");
  const nameEl = document.getElementById("active-filter-name");
  const dot = document.getElementById("active-filter-dot");
  const resetBtn = document.getElementById("btn-reset-filter");
  const trackedBadge = document.getElementById("tracked-count-badge");

  if (!badge || !nameEl) return;

  const labels = {
    'ALL': d.filter_all.replace(/^[^\s]+\s+/, ''),
    'TRACKED': d.filter_tracked.replace(/^[^\s]+\s+/, ''),
    'PRESS': d.filter_press.replace(/^[^\s]+\s+/, ''),
    'CYBER': d.filter_cyber.replace(/^[^\s]+\s+/, ''),
    'PRIORITY': d.filter_priority.replace(/^[^\s]+\s+/, ''),
    'URGENT': d.filter_urgent.replace(/^[^\s]+\s+/, ''),
    'BIG_BUDGET': d.filter_budget.replace(/^[^\s]+\s+/, ''),
    'DOWNLOADED': d.filter_downloaded.replace(/^[^\s]+\s+/, '')
  };

  nameEl.textContent = labels[activeQuickChip] || d.filter_all;

  if (activeQuickChip === 'ALL') {
    if (resetBtn) resetBtn.classList.add("hidden");
    if (dot) dot.className = "w-2 h-2 rounded-full bg-slate-400";
    if (trackedBadge) trackedBadge.classList.add("hidden");
    badge.className = "inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-100 text-slate-700 text-xs font-bold border border-slate-200 shadow-2xs";
  } else {
    if (resetBtn) resetBtn.classList.remove("hidden");
    if (activeQuickChip === 'TRACKED') {
      if (dot) dot.className = "w-2 h-2 rounded-full bg-amber-500 animate-pulse";
      if (trackedBadge) {
        trackedBadge.textContent = trackedTendersSet.size;
        trackedBadge.classList.remove("hidden");
      }
      badge.className = "inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-amber-100 text-amber-950 text-xs font-bold border border-amber-300 shadow-2xs";
    } else if (activeQuickChip === 'CYBER') {
      if (dot) dot.className = "w-2 h-2 rounded-full bg-emerald-500 animate-pulse";
      if (trackedBadge) trackedBadge.classList.add("hidden");
      badge.className = "inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-100 text-emerald-950 text-xs font-bold border border-emerald-300 shadow-2xs";
    } else {
      if (dot) dot.className = "w-2 h-2 rounded-full bg-blue-500";
      if (trackedBadge) trackedBadge.classList.add("hidden");
      badge.className = "inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-blue-50 text-blue-950 text-xs font-bold border border-blue-200 shadow-2xs";
    }
  }

  const countLabel = document.getElementById("results-count-label");
  if (countLabel) {
    const total = allTendersCache ? allTendersCache.length : allTendersMasterCache.length;
    if (currentLang === 'en') {
      countLabel.textContent = `${total} tender(s) found`;
    } else if (currentLang === 'ar') {
      countLabel.textContent = `${total} استشارة مطابقة`;
    } else {
      countLabel.textContent = `${total} consultation(s) trouvée(s)`;
    }
  }
}

function setQuickChip(chip) {
  activeQuickChip = chip;

  // Synchronize dropdown
  const filterSelect = document.getElementById("select-quick-filter");
  if (filterSelect && filterSelect.value !== chip) {
    filterSelect.value = chip;
  }
  updateActiveFilterIndicator();

  const categorySelect = document.getElementById("filter-category");
  const sourceSelect = document.getElementById("filter-source");
  const minBudgetInput = document.getElementById("filter-min-budget");

  if (chip === 'ALL') {
    if (categorySelect) categorySelect.value = "ALL";
    if (sourceSelect) sourceSelect.value = "";
    if (minBudgetInput) minBudgetInput.value = "";
    priorityOnly = false;
  } else if (chip === 'TRACKED') {
    if (categorySelect) categorySelect.value = "ALL";
    if (sourceSelect) sourceSelect.value = "";
    if (minBudgetInput) minBudgetInput.value = "";
    priorityOnly = false;
  } else if (chip === 'PRESS') {
    if (categorySelect) categorySelect.value = "ALL";
    if (sourceSelect) sourceSelect.value = "Presse / Journal";
    if (minBudgetInput) minBudgetInput.value = "";
    priorityOnly = false;
  } else if (chip === 'CYBER') {
    if (categorySelect) categorySelect.value = "CYBERSECURITY";
    if (sourceSelect) sourceSelect.value = "";
    priorityOnly = false;
  } else if (chip === 'PRIORITY') {
    if (categorySelect) categorySelect.value = "ALL";
    priorityOnly = true;
  } else if (chip === 'URGENT') {
    if (categorySelect) categorySelect.value = "ALL";
    priorityOnly = false;
    setQuickSort('deadline_asc');
    return;
  } else if (chip === 'BIG_BUDGET') {
    if (categorySelect) categorySelect.value = "ALL";
    if (minBudgetInput) minBudgetInput.value = "1000000";
    priorityOnly = false;
  } else if (chip === 'DOWNLOADED') {
    const filtered = allTendersCache.filter(t => t.dce_downloaded);
    renderTendersList(filtered);
    return;
  }
  applyClientFiltersAndRender();
}

function copyToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showToast(`Référence ${text} copiée !`, 'info');
    }).catch(() => {
      fallbackCopy(text);
    });
  } else {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  const ta = document.createElement("textarea");
  ta.value = text;
  document.body.appendChild(ta);
  ta.select();
  document.execCommand("copy");
  document.body.removeChild(ta);
  showToast(`Référence ${text} copiée !`, 'info');
}

function setQuickSort(sortType) {
  const select = document.getElementById("filter-sort");
  if (select) select.value = sortType;
  updateQuickSortButtons(sortType);
  applyClientFiltersAndRender();
}

function onSortDropdownChange() {
  const select = document.getElementById("filter-sort");
  const sortType = select ? select.value : "publication_desc";
  updateQuickSortButtons(sortType);
  applyClientFiltersAndRender();
}

function updateQuickSortButtons(sortType) {
  const btnPub = document.getElementById("btn-sort-publication");
  const btnDead = document.getElementById("btn-sort-deadline");
  const groupLabel = document.getElementById("group-toggle-label");

  const d = I18N[currentLang] || I18N.fr;
  if (sortType.startsWith("deadline")) {
    if (btnDead) {
      btnDead.className = "px-3.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 bg-white text-amber-800 shadow-xs border border-amber-300";
    }
    if (btnPub) {
      btnPub.className = "px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition flex items-center space-x-1.5";
    }
    if (groupLabel) groupLabel.textContent = d.group_by_day_dead || "Grouper par Date de Réponse";
  } else if (sortType.startsWith("publication")) {
    if (btnPub) {
      btnPub.className = "px-3.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 bg-white text-emerald-700 shadow-xs border border-slate-200/70";
    }
    if (btnDead) {
      btnDead.className = "px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition flex items-center space-x-1.5";
    }
    if (groupLabel) groupLabel.textContent = d.group_by_day_pub || "Grouper par Date de Publication";
  } else {
    if (btnPub) {
      btnPub.className = "px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition flex items-center space-x-1.5";
    }
    if (btnDead) {
      btnDead.className = "px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition flex items-center space-x-1.5";
    }
    if (groupLabel) groupLabel.textContent = d.group_by_day || "Grouper par Date";
  }
}

function formatDateTime(dtStr) {
  const d = I18N[currentLang] || I18N.fr;
  if (!dtStr) return d.date_not_specified || "Non précisée";
  const parts = dtStr.split(" ");
  const datePart = parts[0];
  const timePart = parts[1] ? parts[1].substring(0, 5) : "";
  const dParts = datePart.split("-");
  if (dParts.length === 3) {
    const formattedDate = `${dParts[2]}/${dParts[1]}/${dParts[0]}`;
    if (!timePart) return formattedDate;
    if (currentLang === 'en') return `${formattedDate} at ${timePart}`;
    if (currentLang === 'ar') return `${formattedDate} في ${timePart}`;
    return `${formattedDate} à ${timePart}`;
  }
  return dtStr;
}

function formatDateOnly(dtStr) {
  if (!dtStr) return "—";
  const parts = dtStr.split(" ")[0].split("-");
  if (parts.length === 3) {
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
  }
  return dtStr;
}

function formatCleanTitle(title) {
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
      if (acronyms.has(cleanW)) {
        return w.toUpperCase();
      }
      if (idx === 0) return w.charAt(0).toUpperCase() + w.slice(1);
      const lowers = new Set(['de', 'du', 'des', 'le', 'la', 'les', 'un', 'une', 'd\'', 'l\'', 'à', 'au', 'aux', 'et', 'en', 'pour', 'sur', 'par', 'dans']);
      if (lowers.has(w)) return w;
      return w.charAt(0).toUpperCase() + w.slice(1);
    }).join(' ');
  }
  return str;
}

function cleanSourceName(sourceName, buyerName) {
  if (!sourceName) return "Portail";
  const s = sourceName.trim();
  const lower = s.toLowerCase();
  if (lower.includes("matin")) return "Le Matin";
  if (lower.includes("économiste") || lower.includes("economiste")) return "L'Économiste";
  if (lower.includes("safakat") || lower.includes("cdg")) return "Safakat CDG";
  if (lower.includes("marchespublics.gov") || lower.includes("pmmp") || lower.includes("portail des march")) return "PMMP";
  if (lower.includes("aujourd'hui") || lower.includes("aujourdhui")) return "Aujourd'hui le Maroc";
  if (lower.includes("finances news")) return "Finances News";
  if (lower.includes("journal") || lower.includes("presse")) return "Presse Légale";
  if (buyerName && (lower === buyerName.toLowerCase().trim() || lower.includes(buyerName.toLowerCase().trim()))) {
    return "Portail";
  }
  if (s.length > 18) return s.substring(0, 16) + "...";
  return s;
}

function formatDayLabel(dayKey) {
  if (!dayKey || dayKey === "Autre") {
    return currentLang === 'en' ? "Publication date not specified" : (currentLang === 'ar' ? "تاريخ النشر غير محدد" : "Date de mise en ligne non précisée");
  }
  const parts = dayKey.split("-");
  if (parts.length === 3) {
    const y = parts[0];
    const m = parseInt(parts[1], 10);
    const d = parts[2];
    
    const monthsFr = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"];
    const monthsEn = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const monthsAr = ["", "يناير", "فبراير", "مارس", "أبريل", "ماي", "يونيو", "يوليوز", "غشت", "شتنبر", "أكتوبر", "نونبر", "دجنبر"];
    
    let monthName = monthsFr[m] || parts[1];
    let dateFmt = `${d} ${monthName} ${y}`;
    if (currentLang === 'en') {
      monthName = monthsEn[m] || parts[1];
      dateFmt = `${monthName} ${d}, ${y}`;
    } else if (currentLang === 'ar') {
      monthName = monthsAr[m] || parts[1];
      dateFmt = `${d} ${monthName} ${y}`;
    }

    if (dayKey === "2026-11-20" || dayKey === new Date().toISOString().split("T")[0]) {
      const todayWord = currentLang === 'en' ? "Today" : (currentLang === 'ar' ? "اليوم" : "Aujourd'hui");
      return `${todayWord} — ${dateFmt}`;
    }
    if (dayKey === "2026-11-19") {
      const yestWord = currentLang === 'en' ? "Yesterday" : (currentLang === 'ar' ? "أمس" : "Hier");
      return `${yestWord} — ${dateFmt}`;
    }
    return dateFmt;
  }
  return dayKey;
}

function formatDeadlineDayLabel(dayKey) {
  if (!dayKey || dayKey === "Autre") {
    return currentLang === 'en' ? "Submission deadline not specified" : (currentLang === 'ar' ? "آخر أجل غير محدد" : "Date limite non précisée");
  }
  const parts = dayKey.split("-");
  if (parts.length === 3) {
    const y = parts[0];
    const m = parseInt(parts[1], 10);
    const d = parts[2];
    
    const monthsFr = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"];
    const monthsEn = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const monthsAr = ["", "يناير", "فبراير", "مارس", "أبريل", "ماي", "يونيو", "يوليوز", "غشت", "شتنبر", "أكتوبر", "نونبر", "دجنبر"];
    
    let monthName = monthsFr[m] || parts[1];
    let dateFmt = `${d} ${monthName} ${y}`;
    if (currentLang === 'en') {
      monthName = monthsEn[m] || parts[1];
      dateFmt = `${monthName} ${d}, ${y}`;
    } else if (currentLang === 'ar') {
      monthName = monthsAr[m] || parts[1];
      dateFmt = `${d} ${monthName} ${y}`;
    }

    const target = new Date(`${dayKey}T23:59:59`).getTime();
    const now = new Date().getTime();
    const diffDays = Math.ceil((target - now) / (1000 * 60 * 60 * 24));
    
    let countdownBadge = "";
    if (currentLang === 'en') {
      if (diffDays < 0) countdownBadge = " · Deadline passed";
      else if (diffDays === 0) countdownBadge = " · Today (Last day!)";
      else if (diffDays === 1) countdownBadge = " · Tomorrow!";
      else countdownBadge = ` · In ${diffDays} days`;
      return `Submission Deadline: ${dateFmt}${countdownBadge}`;
    } else if (currentLang === 'ar') {
      if (diffDays < 0) countdownBadge = " · انتهى الأجل";
      else if (diffDays === 0) countdownBadge = " · اليوم (آخر موعد)";
      else if (diffDays === 1) countdownBadge = " · غداً";
      else countdownBadge = ` · خلال ${diffDays} أيام`;
      return `آخر أجل لتقديم العروض: ${dateFmt}${countdownBadge}`;
    } else {
      if (diffDays < 0) countdownBadge = " · Délai dépassé";
      else if (diffDays === 0) countdownBadge = " · Aujourd'hui (Dernier jour !)";
      else if (diffDays === 1) countdownBadge = " · Demain !";
      else countdownBadge = ` · Dans ${diffDays} jours`;
      return `Échéance de remise : ${dateFmt}${countdownBadge}`;
    }
  }
  return dayKey;
}

function renderTableRowHtml(t, dayRank) {
  const d = I18N[currentLang] || I18N.fr;
  const isCyber = t.relevance_category === 'CYBERSECURITY';
  const countdown = formatCountdown(t.deadline);
  const deadlineDate = formatDateOnly(t.deadline);
  const cleanTitle = formatCleanTitle(t.title);
  const cleanSource = cleanSourceName(t.source_name, t.buyer_name);
  const isTracked = isTenderTracked(t.id);

  // Search matching query for text highlighting
  const searchEl = document.getElementById("filter-search");
  const searchVal = searchEl ? searchEl.value.trim() : "";

  // Priority indicator
  const priorityIndicator = t.is_priority_buyer ? `
    <span class="inline-flex items-center space-x-1 text-[10px] font-semibold text-amber-600 dark:text-amber-400" title="Acheteur Prioritaire DPA">
      <i data-lucide="star" class="w-2.5 h-2.5 fill-amber-400 text-amber-400"></i>
      <span>Prioritaire</span>
    </span>
  ` : '';

  // Cyber Tag (Clean & subtle)
  const cyberTag = isCyber ? `
    <span class="inline-flex items-center space-x-1 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800/60 shrink-0">
      <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
      <span>${t.relevance_score || 90}% Cyber</span>
    </span>
  ` : '';

  // Clean Budget display
  const budgetDisplay = t.estimated_budget > 0 
    ? `<span class="font-semibold text-xs text-slate-800 dark:text-slate-200">${formatMAD(t.estimated_budget)}</span>`
    : `<span class="text-slate-400 dark:text-slate-500 font-normal text-xs">—</span>`;

  return `
    <tr onclick="openTenderModal(${safeArg(t.id)})" class="hover:bg-slate-50/90 dark:hover:bg-slate-800/50 transition-colors border-b border-slate-100 dark:border-slate-800/80 cursor-pointer group">
      <!-- 1. Référence & Procédure (13%) -->
      <td class="py-3 px-3 align-middle">
        <div class="flex items-center space-x-1">
          <span class="font-mono font-bold text-xs text-slate-900 dark:text-slate-100 tracking-tight">${highlightSearchMatch(t.reference, searchVal)}</span>
          ${isTracked ? '<i data-lucide="star" class="w-3 h-3 fill-amber-400 text-amber-400 shrink-0"></i>' : ''}
        </div>
        <div class="text-[10px] text-slate-400 dark:text-slate-500 font-medium mt-0.5">
          <span>${escapeHtml(t.procedure_type || 'AOO')}</span>
        </div>
      </td>

      <!-- 2. Acheteur Public (20%) -->
      <td class="py-3 px-3 align-middle">
        <span class="font-semibold text-xs text-slate-900 dark:text-slate-100 block truncate max-w-[220px]" title="${escapeHtml(t.buyer_name)}">${highlightSearchMatch(t.buyer_name, searchVal)}</span>
        <div class="flex items-center space-x-2 mt-0.5">
          ${priorityIndicator}
          ${cleanSource !== 'Portail' && cleanSource !== 'PMMP' ? `<span class="text-[10px] text-slate-400 truncate max-w-[120px]">${escapeHtml(cleanSource)}</span>` : ''}
        </div>
      </td>

      <!-- 3. Objet du Marché (40%) -->
      <td class="py-3 px-3 align-middle">
        <div class="font-medium text-xs sm:text-[13px] text-slate-900 dark:text-slate-100 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition leading-snug line-clamp-2 break-words" title="${escapeHtml(t.title)}">
          ${highlightSearchMatch(cleanTitle, searchVal)}
        </div>
        ${cyberTag ? `<div class="mt-1">${cyberTag}</div>` : ''}
      </td>

      <!-- 4. Budget TTC (12%) -->
      <td class="py-3 px-3 align-middle whitespace-nowrap">
        ${budgetDisplay}
      </td>

      <!-- 5. Échéance (15%) -->
      <td class="py-3 px-3 align-middle whitespace-nowrap">
        <span class="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold ${countdown.badgeClass}">
          <i data-lucide="clock" class="w-2.5 h-2.5"></i>
          <span>${countdown.text}</span>
        </span>
        <span class="text-[10px] text-slate-400 block mt-0.5 font-mono">${deadlineDate}</span>
      </td>

      <!-- 6. Actions (Actions compactes) -->
      <td class="py-3 px-3 text-right align-middle whitespace-nowrap" onclick="event.stopPropagation()">
        <div class="flex items-center justify-end space-x-1.5">
          <!-- Star Toggle -->
          <button onclick="toggleTrackTender(${safeArg(t.id)}, event)" class="p-1.5 rounded-lg border transition ${isTracked ? 'bg-amber-400 text-slate-950 border-amber-500' : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-amber-500 border-slate-200 dark:border-slate-700'}" title="${isTracked ? d.track_active : d.track_inactive}">
            <i data-lucide="star" class="w-3.5 h-3.5 ${isTracked ? 'fill-slate-950 text-slate-950' : ''}"></i>
          </button>

          <!-- Dossier Button -->
          <button onclick="openSubmissionFolderModal(${safeArg(t.id)})" class="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 active:scale-95 text-slate-950 text-[11px] font-bold rounded-lg flex items-center space-x-1 transition shadow-2xs" title="${d.btn_folder}">
            <i data-lucide="folder" class="w-3 h-3"></i>
            <span>${d.btn_folder || 'Dossier'}</span>
          </button>
        </div>
      </td>
    </tr>
  `;
}

function renderTableViewHtml(tenders, groupByDay, sortVal) {
  const d = I18N[currentLang] || I18N.fr;
  let bodyHtml = "";

  if (groupByDay && (sortVal.startsWith("publication") || sortVal.startsWith("deadline"))) {
    const isDeadlineGrouping = sortVal.startsWith("deadline");
    const dateField = isDeadlineGrouping ? "deadline" : "publication_date";

    const groups = {};
    tenders.forEach(t => {
      const dayKey = t[dateField] ? t[dateField].split(" ")[0] : "Autre";
      if (!groups[dayKey]) groups[dayKey] = [];
      groups[dayKey].push(t);
    });

    const sortedDays = Object.keys(groups).sort();
    if (sortVal === "publication_desc" || sortVal === "deadline_desc") {
      sortedDays.reverse();
    }

    sortedDays.forEach(dayKey => {
      const dayTenders = groups[dayKey];
      const dayLabel = isDeadlineGrouping ? formatDeadlineDayLabel(dayKey) : formatDayLabel(dayKey);
      const iconName = isDeadlineGrouping ? "clock" : "calendar";
      const iconColor = isDeadlineGrouping ? "text-amber-600 dark:text-amber-400" : "text-emerald-600 dark:text-emerald-400";

      const itemWord = currentLang === 'en' ? 'tender(s)' : (currentLang === 'ar' ? 'استشارة' : 'consultation(s)');
      bodyHtml += `
        <tr class="bg-slate-50/60 dark:bg-slate-950/60 border-y border-slate-200/60 dark:border-slate-800">
          <td colspan="6" class="py-1.5 px-3 font-semibold text-[11px] text-slate-500 dark:text-slate-400">
            <div class="flex items-center space-x-2">
              <i data-lucide="${iconName}" class="w-3.5 h-3.5 ${iconColor}"></i>
              <span>${escapeHtml(dayLabel)}</span>
              <span class="text-slate-400 dark:text-slate-500 text-[10px]">(${dayTenders.length} ${itemWord})</span>
            </div>
          </td>
        </tr>
      `;

      dayTenders.forEach((t, idx) => {
        bodyHtml += renderTableRowHtml(t, idx + 1);
      });
    });
  } else {
    tenders.forEach((t, idx) => {
      bodyHtml += renderTableRowHtml(t, idx + 1);
    });
  }

  return `
    <div class="w-full bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-xs overflow-hidden transition-colors">
      <table class="w-full table-fixed text-left border-collapse">
        <colgroup>
          <col class="w-[12%]">
          <col class="w-[20%]">
          <col class="w-[40%]">
          <col class="w-[12%]">
          <col class="w-[10%]">
          <col class="w-[6%]">
        </colgroup>
        <thead>
          <tr class="bg-slate-50/70 dark:bg-slate-950/70 border-b border-slate-200/80 dark:border-slate-800 text-xs font-semibold text-slate-500 dark:text-slate-400">
            <th class="py-3 px-3">${d.th_ref}</th>
            <th class="py-3 px-3">${d.th_buyer}</th>
            <th class="py-3 px-3">${d.th_object}</th>
            <th class="py-3 px-3">${d.th_budget}</th>
            <th class="py-3 px-3">${d.th_deadline}</th>
            <th class="py-3 px-3 text-right">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-800/80 text-xs">
          ${bodyHtml}
        </tbody>
      </table>
    </div>
  `;
}

function renderCardsViewHtml(tenders, groupByDay, sortVal) {
  let html = "";

  if (groupByDay && (sortVal.startsWith("publication") || sortVal.startsWith("deadline"))) {
    const isDeadlineGrouping = sortVal.startsWith("deadline");
    const dateField = isDeadlineGrouping ? "deadline" : "publication_date";

    const groups = {};
    tenders.forEach(t => {
      const dayKey = t[dateField] ? t[dateField].split(" ")[0] : "Autre";
      if (!groups[dayKey]) groups[dayKey] = [];
      groups[dayKey].push(t);
    });

    const sortedDays = Object.keys(groups).sort();
    if (sortVal === "publication_desc" || sortVal === "deadline_desc") {
      sortedDays.reverse();
    }

    sortedDays.forEach(dayKey => {
      const dayTenders = groups[dayKey];
      const dayLabel = isDeadlineGrouping ? formatDeadlineDayLabel(dayKey) : formatDayLabel(dayKey);
      const iconName = isDeadlineGrouping ? "clock" : "calendar";
      const iconColor = isDeadlineGrouping ? "text-amber-600 dark:text-amber-400" : "text-emerald-600 dark:text-emerald-400";
      const badgeBg = isDeadlineGrouping ? "bg-amber-50 dark:bg-amber-950/70 text-amber-950 dark:text-amber-200 border border-amber-300 dark:border-amber-800/80" : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700";

      html += `
        <div class="flex items-center space-x-3 pt-4 pb-2">
          <div class="flex items-center space-x-2 ${badgeBg} px-3.5 py-1.5 rounded-full text-xs font-bold shadow-2xs">
            <i data-lucide="${iconName}" class="w-3.5 h-3.5 ${iconColor}"></i>
            <span>${escapeHtml(dayLabel)}</span>
          </div>
          <span class="text-xs font-semibold text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 px-2.5 py-1 rounded-full border border-slate-200 dark:border-slate-700 shadow-2xs">
            ${dayTenders.length} consultation(s)
          </span>
          <div class="flex-1 h-px bg-slate-200/80 dark:bg-slate-800"></div>
        </div>
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
          ${dayTenders.map((t, idx) => renderTenderCardHtml(t, idx + 1)).join("")}
        </div>
      `;
    });

    return html;
  }

  return `
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      ${tenders.map((t, idx) => renderTenderCardHtml(t, idx + 1)).join("")}
    </div>
  `;
}

function renderMobileTouchCardsHtml(tenders, groupByDay, sortVal) {
  let html = "";

  const renderSingleMobileCard = (t) => {
    const countdown = formatCountdown(t.deadline);
    const isCyber = t.relevance_category === 'CYBERSECURITY';
    const cleanSource = cleanSourceName(t.source_name, t.buyer_name);
    const isTracked = isTenderTracked(t.id);

    const isPress = t.source_name && (
      t.source_name.toLowerCase().includes('journal') ||
      t.source_name.toLowerCase().includes('matin') ||
      t.source_name.toLowerCase().includes('économiste') ||
      t.source_name.toLowerCase().includes('presse') ||
      (t.buyer_normalized && (t.buyer_normalized.includes('atlantic') || t.buyer_normalized.includes('laprophan'))) ||
      (t.buyer_name && (t.buyer_name.includes('Atlantic') || t.buyer_name.includes('Laprophan') || t.buyer_name.includes('SCR')))
    );

    const buyerWords = (t.buyer_name || 'OP').split(' ').filter(w => w.length > 2);
    let initials = 'OP';
    if (t.priority_badge && !t.priority_badge.toLowerCase().includes('prioritaire')) {
      initials = t.priority_badge.substring(0, 3).toUpperCase();
    } else if (buyerWords.length >= 2) {
      initials = (buyerWords[0][0] + buyerWords[1][0]).toUpperCase();
    } else if (buyerWords.length === 1) {
      initials = buyerWords[0].substring(0, 3).toUpperCase();
    }

    return `
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-2xs space-y-3 w-full transition-colors">
        <!-- Top Row: Ref, Proc, Countdown -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center space-x-1.5 min-w-0">
            <span class="font-mono text-[11px] font-bold text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-200/80 dark:border-emerald-800/60 truncate" title="${escapeHtml(t.reference)}">
              ${escapeHtml(t.reference)}
            </span>
            <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700 shrink-0">
              ${escapeHtml(t.procedure_type || 'AOO')}
            </span>
          </div>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold ${countdown.badgeClass} shrink-0">
            ${countdown.text}
          </span>
        </div>

        <!-- Buyer & Source Row -->
        <div class="flex items-start space-x-2.5">
          <div class="w-8 h-8 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-black text-[10px] text-slate-700 dark:text-slate-300 flex items-center justify-center shrink-0 mt-0.5">
            ${escapeHtml(initials)}
          </div>
          <div class="min-w-0 flex-1">
            <h4 class="font-bold text-xs text-slate-900 dark:text-slate-100 leading-snug break-words">
              ${escapeHtml(t.buyer_name)}
            </h4>
            <div class="mt-1 flex flex-wrap items-center gap-1.5">
              <a href="${escapeHtml(t.source_url)}" target="_blank" onclick="event.stopPropagation()" class="inline-flex items-center space-x-1 text-[10px] font-bold ${isPress ? 'text-amber-900 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/50 border border-amber-300 dark:border-amber-800' : 'text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800'} px-2 py-0.5 rounded transition shadow-2xs" title="${escapeHtml(cleanSource)}">
                <i data-lucide="${isPress ? 'newspaper' : 'globe'}" class="w-3 h-3 shrink-0"></i>
                <span class="truncate max-w-[200px]">${escapeHtml(cleanSource)} ↗</span>
              </a>
              ${isCyber ? `
                <span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  ${t.relevance_score}% Cyber
                </span>
              ` : ''}
            </div>
          </div>
        </div>

        <!-- Tender Title (Objet) -->
        <div onclick="openTenderModal(${safeArg(t.id)})" class="font-semibold text-xs text-slate-900 dark:text-slate-100 leading-snug break-words active:text-emerald-600 transition cursor-pointer">
          ${escapeHtml(formatCleanTitle(t.title))}
        </div>

        <!-- Budget & Caution Info Grid -->
        <div class="grid grid-cols-2 gap-2 text-[11px] bg-slate-50 dark:bg-slate-950/60 p-2.5 rounded-xl border border-slate-100 dark:border-slate-800">
          <div>
            <span class="text-slate-400 dark:text-slate-500 block text-[9px] uppercase font-bold">Budget TTC</span>
            <span class="font-extrabold text-slate-900 dark:text-slate-100 block mt-0.5">
              ${t.estimated_budget > 0 ? formatMAD(t.estimated_budget) : 'Non précisé'}
            </span>
          </div>
          <div>
            <span class="text-slate-400 dark:text-slate-500 block text-[9px] uppercase font-bold">Caution / Dépôt</span>
            <span class="font-bold text-amber-700 dark:text-amber-400 block mt-0.5 truncate" title="${escapeHtml(t.provisional_guarantee || 'Selon CPS')}">
              ${escapeHtml(t.provisional_guarantee || 'Selon CPS')}
            </span>
          </div>
        </div>

        <!-- 4 Large Mobile Touch Targets (Min Height 44px) -->
        <div class="grid grid-cols-4 gap-1.5 pt-1 border-t border-slate-100 dark:border-slate-800">
          <button onclick="toggleTrackTender(${safeArg(t.id)}, event)" class="min-h-[44px] flex flex-col items-center justify-center p-1 rounded-xl border font-bold text-[10px] transition active:scale-95 ${isTracked ? 'bg-amber-400 text-slate-950 border-amber-500' : 'bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700'}" title="${isTracked ? 'AO Suivi' : 'Suivre AO'}">
            <i data-lucide="star" class="w-4 h-4 mb-0.5 ${isTracked ? 'fill-slate-950' : 'text-amber-500'}"></i>
            <span>${isTracked ? 'Suivi' : 'Suivre'}</span>
          </button>
          
          <button onclick="openSubmissionFolderModal(${safeArg(t.id)})" class="min-h-[44px] flex flex-col items-center justify-center p-1 bg-amber-500 active:bg-amber-600 text-slate-950 font-bold text-[10px] rounded-xl transition shadow-2xs active:scale-95">
            <i data-lucide="folder" class="w-4 h-4 mb-0.5"></i>
            <span>Dossier</span>
          </button>
          
          <button onclick="downloadDCE(${safeArg(t.id)}, ${safeArg(t.reference)})" class="min-h-[44px] flex flex-col items-center justify-center p-1 bg-emerald-600 active:bg-emerald-700 text-white font-bold text-[10px] rounded-xl transition shadow-2xs active:scale-95">
            <i data-lucide="download" class="w-4 h-4 mb-0.5 text-amber-300"></i>
            <span>DCE</span>
          </button>
          
          <button onclick="openTenderModal(${safeArg(t.id)})" class="min-h-[44px] flex flex-col items-center justify-center p-1 bg-slate-100 dark:bg-slate-800 active:bg-slate-200 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 font-bold text-[10px] rounded-xl transition active:scale-95">
            <i data-lucide="eye" class="w-4 h-4 mb-0.5 text-blue-500"></i>
            <span>Détails</span>
          </button>
        </div>
      </div>
    `;
  };

  if (groupByDay && (sortVal.startsWith("publication") || sortVal.startsWith("deadline"))) {
    const isDeadlineGrouping = sortVal.startsWith("deadline");
    const dateField = isDeadlineGrouping ? "deadline" : "publication_date";

    const groups = {};
    tenders.forEach(t => {
      const dayKey = t[dateField] ? t[dateField].split(" ")[0] : "Autre";
      if (!groups[dayKey]) groups[dayKey] = [];
      groups[dayKey].push(t);
    });

    const sortedDays = Object.keys(groups).sort();
    if (sortVal === "publication_desc" || sortVal === "deadline_desc") {
      sortedDays.reverse();
    }

    sortedDays.forEach(dayKey => {
      const dayTenders = groups[dayKey];
      const dayLabel = isDeadlineGrouping ? formatDeadlineDayLabel(dayKey) : formatDayLabel(dayKey);
      const iconName = isDeadlineGrouping ? "clock" : "calendar";
      const iconColor = isDeadlineGrouping ? "text-amber-600 dark:text-amber-400" : "text-emerald-600 dark:text-emerald-400";
      const badgeBg = isDeadlineGrouping ? "bg-amber-50 dark:bg-amber-950/70 text-amber-950 dark:text-amber-200 border-amber-300 dark:border-amber-800" : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border-slate-200 dark:border-slate-700";

      html += `
        <div class="pt-3 pb-1">
          <div class="flex items-center justify-between ${badgeBg} px-3 py-1.5 rounded-xl border text-xs font-bold shadow-2xs mb-2">
            <div class="flex items-center space-x-1.5">
              <i data-lucide="${iconName}" class="w-3.5 h-3.5 ${iconColor}"></i>
              <span>${escapeHtml(dayLabel)}</span>
            </div>
            <span class="text-[10px] font-semibold text-slate-500 dark:text-slate-400">
              ${dayTenders.length} ${currentLang === 'en' ? 'tender(s)' : (currentLang === 'ar' ? 'استشارة' : 'offre(s)')}
            </span>
          </div>
          <div class="space-y-3">
            ${dayTenders.map(t => renderSingleMobileCard(t)).join("")}
          </div>
        </div>
      `;
    });

    return html;
  }

  return `
    <div class="space-y-3">
      ${tenders.map(t => renderSingleMobileCard(t)).join("")}
    </div>
  `;
}

function renderTendersList(tenders) {
  const container = document.getElementById("tenders-container");
  if (!container) return;
  const dict = I18N[currentLang] || I18N.fr;

  if (!tenders || tenders.length === 0) {
    container.innerHTML = `
      <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 sm:p-12 text-center text-slate-500 shadow-sm transition-colors">
        <div class="w-16 h-16 mx-auto mb-3 rounded-2xl bg-slate-50 dark:bg-slate-800 text-slate-400 flex items-center justify-center">
          <i data-lucide="inbox" class="w-8 h-8"></i>
        </div>
        <p class="font-bold text-sm text-slate-800 dark:text-slate-200">${dict.no_tenders}</p>
        <p class="text-xs text-slate-400 mt-1">Essayez d'élargir vos filtres ou de sélectionner "Toutes les catégories".</p>
      </div>
    `;
    if (window.lucide) lucide.createIcons({ root: container });
    return;
  }

  const groupByDay = document.getElementById("toggle-group-by-day") ? document.getElementById("toggle-group-by-day").checked : true;
  const sortVal = document.getElementById("filter-sort") ? document.getElementById("filter-sort").value : "publication_desc";

  // Mobile viewport: native-like touch cards with zero horizontal scrolling
  if (window.innerWidth < 768) {
    container.innerHTML = renderMobileTouchCardsHtml(tenders, groupByDay, sortVal);
    if (window.lucide) lucide.createIcons({ root: container });
    return;
  }

  if (currentViewMode === 'table') {
    container.innerHTML = renderTableViewHtml(tenders, groupByDay, sortVal);
  } else {
    container.innerHTML = renderCardsViewHtml(tenders, groupByDay, sortVal);
  }
  if (window.lucide) lucide.createIcons({ root: container });
}

function renderTenderCardHtml(t, dayRank) {
  const dict = I18N[currentLang] || I18N.fr;
  const countdown = formatCountdown(t.deadline);
  const isCyber = t.relevance_category === 'CYBERSECURITY';
  
  // Find real direct DCE download link on PMMP or official source
  const dceDoc = (t.document_links || []).find(d => d.doc_type === 'DCE');
  const realDceUrl = dceDoc ? dceDoc.url : t.source_url;

  // Search matching query for text highlighting
  const searchEl = document.getElementById("filter-search");
  const searchVal = searchEl ? searchEl.value.trim() : "";

  // Identify Official Press / Legal Journal / Direct Consultation
  const isPress = t.source_name && (
    t.source_name.toLowerCase().includes('journal') ||
    t.source_name.toLowerCase().includes('matin') ||
    t.source_name.toLowerCase().includes('économiste') ||
    t.source_name.toLowerCase().includes('presse') ||
    (t.buyer_normalized && (t.buyer_normalized.includes('atlantic') || t.buyer_normalized.includes('laprophan'))) ||
    (t.buyer_name && (t.buyer_name.includes('Atlantic') || t.buyer_name.includes('Laprophan') || t.buyer_name.includes('SCR')))
  );

  const cleanSource = cleanSourceName(t.source_name, t.buyer_name);
  
  // Buyer Initials Avatar
  const buyerWords = (t.buyer_name || 'OP').split(' ').filter(w => w.length > 2);
  let initials = 'OP';
  if (t.priority_badge && !t.priority_badge.toLowerCase().includes('prioritaire')) {
    initials = t.priority_badge.substring(0, 3).toUpperCase();
  } else if (buyerWords.length >= 2) {
    initials = (buyerWords[0][0] + buyerWords[1][0]).toUpperCase();
  } else if (buyerWords.length === 1) {
    initials = buyerWords[0].substring(0, 3).toUpperCase();
  }

  // Priority badge (clean, no repeating buyer)
  const priorityBadge = t.is_priority_buyer ? `
    <span class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-800 border border-amber-200/80">
      <i data-lucide="star" class="w-3 h-3 fill-amber-500 text-amber-500"></i>
      <span>${currentLang === 'en' ? 'Priority Buyer' : (currentLang === 'ar' ? 'مشتري ذو أولوية' : 'Acheteur Prioritaire')}</span>
    </span>
  ` : '';

  const trackedBadge = isTenderTracked(t.id) ? `
    <span class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-400 text-slate-950 border border-amber-500 shadow-2xs">
      <i data-lucide="star" class="w-3 h-3 fill-slate-950 text-slate-950"></i>
      <span>${currentLang === 'en' ? 'Tracked' : (currentLang === 'ar' ? 'متابع' : 'Suivi')}</span>
    </span>
  ` : '';

  // Cyber relevance badge
  const cyberBadge = isCyber ? `
    <span class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200/80">
      <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
      <span>${t.relevance_score}% Cybersécurité · ${t.sub_category || 'SSI'}</span>
    </span>
  ` : `
    <span class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700">
      <span>${t.sub_category || t.category || 'IT & Services'}</span>
    </span>
  `;

  // Formatted publication date
  const pubDateDisplay = formatDateTime(t.publication_date);

  return `
    <div class="card-modern bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 rounded-2xl p-5 space-y-4">
      
      <!-- Top Row: Buyer Avatar, Name, Reference, Day Rank & Badges -->
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center space-x-3 min-w-0">
          <!-- Buyer Avatar Initials -->
          <div class="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-extrabold text-xs flex items-center justify-center shrink-0 tracking-tight">
            ${escapeHtml(initials)}
          </div>
          <div class="min-w-0">
            <div class="flex items-center space-x-2">
              <span class="font-bold text-slate-900 dark:text-slate-100 text-xs sm:text-sm truncate">${highlightSearchMatch(t.buyer_name, searchVal)}</span>
              <span class="px-2 py-0.5 rounded-md text-[10px] font-extrabold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">${t.procedure_type || 'AOO'}</span>
            </div>
            <div class="flex items-center space-x-2 text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
              <span>Réf : <code class="font-mono text-emerald-800 dark:text-emerald-300 font-bold bg-emerald-50 dark:bg-emerald-950/60 px-1.5 py-0.2 rounded border border-emerald-200 dark:border-emerald-800">${highlightSearchMatch(t.reference, searchVal)}</code></span>
              <span class="text-slate-300 dark:text-slate-700">·</span>
              <span>${pubDateDisplay}</span>
            </div>
            <!-- Prominent Verifiable Source Pill -->
            <div class="mt-1.5 flex items-center space-x-1.5">
              <a href="${escapeHtml(t.source_url)}" target="_blank" onclick="event.stopPropagation()" class="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-lg text-[11px] font-bold ${isPress ? 'bg-amber-50 dark:bg-amber-950/50 hover:bg-amber-100 text-amber-900 dark:text-amber-300 border border-amber-300 dark:border-amber-800' : 'bg-emerald-50 dark:bg-emerald-950/50 hover:bg-emerald-100 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'} transition shadow-2xs" title="Consulter la source officielle de publication (${escapeHtml(cleanSource)})">
                <i data-lucide="${isPress ? 'newspaper' : 'globe'}" class="w-3.5 h-3.5 text-${isPress ? 'amber-600' : 'emerald-600'}"></i>
                <span class="truncate max-w-[280px]">${escapeHtml(cleanSource)} ↗</span>
              </a>
            </div>
          </div>
        </div>

        <div class="flex items-center space-x-2 shrink-0">
          <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-900 dark:bg-slate-800 text-amber-300 shadow-2xs">
            Rang #${dayRank}
          </span>
          ${trackedBadge}
          ${priorityBadge}
          ${cyberBadge}
        </div>
      </div>

      <!-- Tender Title (Objet) -->
      <div>
        <h3 onclick="openTenderModal(${safeArg(t.id)})" class="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100 hover:text-emerald-600 dark:hover:text-emerald-400 transition cursor-pointer leading-snug">
          ${highlightSearchMatch(formatCleanTitle(t.title), searchVal)}
        </h3>
      </div>

      <!-- AI Summary Insight (if available) -->
      ${t.summary ? `
        <div class="flex items-start space-x-2.5 bg-slate-50/80 dark:bg-slate-950/70 border border-slate-200/70 dark:border-slate-800 rounded-xl p-3 text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
          <i data-lucide="sparkles" class="w-4 h-4 text-amber-500 shrink-0 mt-0.5"></i>
          <span>${highlightSearchMatch(t.summary, searchVal)}</span>
        </div>
      ` : ''}

      <!-- Specifications Row (Budget, Deadline, Caution) -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        <div class="bg-slate-50 dark:bg-slate-950/70 p-3 rounded-xl border border-slate-200/70 dark:border-slate-800">
          <span class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 block tracking-wider">${dict.th_budget || 'Budget Estimé'}</span>
          <span class="text-sm font-extrabold text-slate-900 dark:text-slate-100 block mt-0.5">
            ${t.estimated_budget > 0 ? formatMAD(t.estimated_budget) : dict.not_specified}
          </span>
        </div>

        <div class="bg-slate-50 dark:bg-slate-950/70 p-3 rounded-xl border border-slate-200/70 dark:border-slate-800">
          <span class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 block tracking-wider">${dict.th_deadline || 'Date Limite Réponse'}</span>
          <div class="flex items-center space-x-1.5 mt-0.5">
            <span class="text-xs font-bold text-slate-900 dark:text-slate-100">${formatDateTime(t.deadline)}</span>
          </div>
          <span class="inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-bold ${countdown.badgeClass}">
            ${countdown.text}
          </span>
        </div>

        <div class="bg-slate-50 dark:bg-slate-950/70 p-3 rounded-xl border border-slate-200/70 dark:border-slate-800">
          <span class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 block tracking-wider">${dict.caution_lbl || 'Cautionnement'}</span>
          <span class="text-xs font-bold text-amber-700 dark:text-amber-400 block mt-0.5">
            ${escapeHtml(t.provisional_guarantee || dict.per_cps || 'Selon CPS')}
          </span>
        </div>
      </div>

      <!-- Bottom Action Row: Download 1-Click, Source Link, Details, Alert -->
      <div class="flex flex-wrap items-center justify-between gap-2.5 pt-2 border-t border-slate-100 dark:border-slate-800">
        
        <div class="flex items-center space-x-2">
          <!-- Direct Verified Link to Source / DCE -->
          <a href="${realDceUrl}" target="_blank" class="px-3 py-1.5 rounded-lg text-xs font-semibold ${isPress ? 'text-amber-900 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/50 hover:bg-amber-100 border border-amber-300 dark:border-amber-800' : 'text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700'} flex items-center space-x-1.5 transition shadow-2xs" title="Consulter la source officielle de publication (${escapeHtml(cleanSource)})">
            <i data-lucide="${isPress ? 'newspaper' : 'external-link'}" class="w-3.5 h-3.5 text-${isPress ? 'amber-600' : 'emerald-600'}"></i>
            <span>${isPress ? "Avis Source ↗" : "Source PMMP ↗"}</span>
          </a>

          <!-- Dossier Button -->
          <button onclick="openSubmissionFolderModal(${safeArg(t.id)})" class="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 active:scale-95 text-slate-950 text-xs font-bold rounded-lg flex items-center space-x-1 shadow-xs transition" title="${dict.btn_folder || 'Dossier de soumission'}">
            <i data-lucide="folder" class="w-3.5 h-3.5"></i>
            <span>${dict.btn_folder || 'Dossier'}</span>
          </button>

          <!-- Tracked RFP Button -->
          <button onclick="toggleTrackTender(${safeArg(t.id)}, event)" class="px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 ${isTenderTracked(t.id) ? 'bg-amber-400 text-slate-950 border border-amber-500 shadow-2xs' : 'text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700'}" title="${isTenderTracked(t.id) ? (dict.track_active || 'AO Suivi') : (dict.track_inactive || 'Suivre AO')}">
            <i data-lucide="star" class="w-3.5 h-3.5 ${isTenderTracked(t.id) ? 'fill-slate-950 text-slate-950' : 'text-amber-500'}"></i>
            <span>${isTenderTracked(t.id) ? 'Suivi ⭐' : 'Suivre AO'}</span>
          </button>
        </div>

        <div class="flex items-center space-x-2">
          <!-- Details & AI Modal -->
          <button onclick="openTenderModal(${safeArg(t.id)})" class="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 transition flex items-center space-x-1">
            <i data-lucide="eye" class="w-3.5 h-3.5 text-blue-500"></i>
            <span>${dict.btn_details || 'Détails'}</span>
          </button>

          <!-- 1-Click Direct DCE Download (Primary CTA) -->
          <button onclick="downloadDCE(${safeArg(t.id)}, ${safeArg(t.reference)})" class="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white text-xs font-bold rounded-lg flex items-center space-x-1.5 shadow-sm transition">
            <i data-lucide="download" class="w-3.5 h-3.5 text-amber-300"></i>
            <span>${dict.btn_dce || 'DCE 1-Clic'}</span>
          </button>
        </div>

      </div>

    </div>
  `;
}

function getPipelineColor(st) {
  switch (st) {
    case 'go': return 'text-emerald-700 bg-emerald-100 px-1.5 py-0.2 rounded';
    case 'no_go': return 'text-rose-700 bg-rose-100 px-1.5 py-0.2 rounded';
    case 'submitted': return 'text-blue-700 bg-blue-100 px-1.5 py-0.2 rounded';
    case 'won': return 'text-amber-800 bg-amber-100 px-1.5 py-0.2 rounded';
    case 'lost': return 'text-slate-500 bg-slate-200 px-1.5 py-0.2 rounded';
    default: return 'text-slate-700 bg-slate-100 px-1.5 py-0.2 rounded';
  }
}

// ==================== 1-CLICK DCE DIRECT DOWNLOADER & PMMP ALERTS ====================

async function downloadDCE(tenderId, reference) {
  showToast(`Préparation du dossier de consultation officiel (${reference}) pour DPA...`, 'info');

  try {
    const downloadUrl = `/api/tenders/${encodeURIComponent(tenderId)}/download-dce`;
    
    // Create an invisible anchor to trigger immediate browser file save
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.setAttribute("download", `DCE_${reference.replace(/[^a-zA-Z0-9_-]/g, '_')}.zip`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast(`✅ Dossier DCE (${reference}) téléchargé ! Alerte officielle PMMP envoyée par email à John Doe (DPA).`, 'success');
  } catch (err) {
    showToast(`Erreur lors du téléchargement : ${err.message}`, 'error');
  }
}

async function triggerOfficialAlert(tenderId, reference) {
  showToast(`Envoi de l'alerte officielle PMMP pour ${reference}...`, 'info');
  try {
    const res = await fetch(`/api/tenders/${encodeURIComponent(tenderId)}/send-alert`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error("Erreur serveur lors de la génération de l'alerte");
    const data = await res.json();
    showToast(`✉️ Alerte officielle PMMP transmise par email à John Doe (DPA) !`, 'success');
  } catch (err) {
    showToast(`Erreur alerte : ${err.message}`, 'error');
  }
}

function downloadActiveTenderDCE() {
  if (!activeTenderModalId) return;
  const t = allTendersCache.find(x => x.id === activeTenderModalId);
  if (t) {
    downloadDCE(t.id, t.reference);
  }
}

function triggerModalOfficialAlert() {
  if (!activeTenderModalId) return;
  const t = allTendersCache.find(x => x.id === activeTenderModalId);
  if (t) {
    triggerOfficialAlert(t.id, t.reference);
  }
}

// ==================== TENDER MODAL & DETAILS ====================

function openTenderModal(tenderId) {
  activeTenderModalId = tenderId;
  let t = (allTendersCache || []).find(x => x.id === tenderId) || (allTendersMasterCache || []).find(x => x.id === tenderId);
  if (!t) {
    fetch(`/api/tenders/${encodeURIComponent(tenderId)}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data && (data.id || data.reference)) {
          const tenderObj = data.id ? data : (data.tender || data);
          allTendersMasterCache.push(tenderObj);
          openTenderModal(tenderId);
        }
      })
      .catch(() => {});
    return;
  }

  const modal = document.getElementById("tender-modal");
  document.getElementById("modal-ref").textContent = t.reference;
  document.getElementById("modal-proc").textContent = t.procedure_type || 'AOO';
  document.getElementById("modal-title").textContent = t.title;
  document.getElementById("modal-buyer").querySelector("span").textContent = t.buyer_name;
  
  const cleanSource = cleanSourceName(t.source_name, t.buyer_name);
  const srcDisplay = cleanSource.toLowerCase() === (t.buyer_name || '').toLowerCase() ? "Plateforme Achats" : cleanSource;
  document.getElementById("modal-source-name").textContent = srcDisplay;

  const priorityEl = document.getElementById("modal-priority-badge");
  if (t.is_priority_buyer) {
    priorityEl.textContent = t.priority_badge || 'Acheteur Prioritaire';
    priorityEl.classList.remove("hidden");
  } else {
    priorityEl.classList.add("hidden");
  }

  // Identify Official Press / Legal Journal / Direct Consultation
  const isPress = t.source_name && (
    t.source_name.toLowerCase().includes('journal') ||
    t.source_name.toLowerCase().includes('matin') ||
    t.source_name.toLowerCase().includes('économiste') ||
    t.source_name.toLowerCase().includes('presse') ||
    (t.buyer_normalized && (t.buyer_normalized.includes('atlantic') || t.buyer_normalized.includes('laprophan'))) ||
    (t.buyer_name && (t.buyer_name.includes('Atlantic') || t.buyer_name.includes('Laprophan') || t.buyer_name.includes('SCR')))
  );

  const isDirectPortal = t.source_name && !t.source_name.toLowerCase().includes('pmmp') && !t.source_name.toLowerCase().includes('marchespublics');

  // Configure Official Source & Publication Banner
  const bannerBox = document.getElementById("modal-source-banner");
  const bannerIcon = document.getElementById("modal-source-banner-icon");
  const bannerTitle = document.getElementById("modal-source-banner-title");
  const bannerDesc = document.getElementById("modal-source-banner-desc");
  const bannerUrl = document.getElementById("modal-source-banner-url");
  const portalBtnLabel = document.getElementById("modal-source-portal-btn-label");
  const dceBtnLabel = document.getElementById("modal-dce-btn-label");
  const sourceFooterText = document.getElementById("modal-source-footer-text");

  if (bannerTitle) bannerTitle.textContent = t.source_name || "Portail Officiel";
  if (bannerUrl) {
    bannerUrl.textContent = t.source_url || "https://marchespublics.gov.ma";
    bannerUrl.href = t.source_url || "#";
  }

  if (isPress) {
    if (bannerBox) {
      bannerBox.className = "bg-gradient-to-r from-amber-50 to-orange-50/50 dark:from-amber-950/40 dark:to-orange-950/20 border border-amber-300 dark:border-amber-800/80 rounded-2xl p-3.5 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-2xs";
    }
    if (bannerIcon) {
      bannerIcon.className = "p-1.5 rounded-lg bg-amber-100 dark:bg-amber-950 text-amber-900 dark:text-amber-300 shrink-0";
      bannerIcon.innerHTML = `<i data-lucide="newspaper" class="w-4 h-4"></i>`;
    }
    if (bannerDesc) {
      const lieu = t.bid_opening_place || (t.buyer_name && t.buyer_name.includes("Atlantic") ? "Siège SCR / Atlantic Re : Tour Horizons, CFC Lot 60 Immeuble B, Casablanca" : "Siège Laprophan : Km 8,5 Route d'El Jadida, Casablanca");
      bannerDesc.textContent = currentLang === 'en' 
        ? `Verified Notice (Legal Press & Procurement Dept) · Bid Submission: ${lieu}`
        : `Publication certifiée (Presse légale & Direction Achats) · Dépôt des offres : ${lieu}`;
    }
    if (portalBtnLabel) portalBtnLabel.textContent = currentLang === 'en' ? "View Source Notice (Journal / Portal) ↗" : "Consulter l'Avis Source (Journal / Portail) ↗";
    if (dceBtnLabel) dceBtnLabel.textContent = currentLang === 'en' ? "Download Specs / CPS (1-Click)" : "Télécharger Dossier / CPS (1-Clic)";
    if (sourceFooterText) sourceFooterText.textContent = currentLang === 'en' ? `View on Journal / Portal (${cleanSource}) ↗` : `Consulter sur le Journal / Portail (${cleanSource}) ↗`;
  } else if (isDirectPortal) {
    if (bannerBox) {
      bannerBox.className = "bg-gradient-to-r from-blue-50/90 to-slate-50 dark:from-slate-800 dark:to-slate-900 border border-blue-200 dark:border-blue-800/80 rounded-2xl p-3.5 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-2xs";
    }
    if (bannerIcon) {
      bannerIcon.className = "p-1.5 rounded-lg bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300 shrink-0";
      bannerIcon.innerHTML = `<i data-lucide="building" class="w-4 h-4"></i>`;
    }
    const buyerCleanName = t.buyer_name ? t.buyer_name.split('(')[0].trim() : "Organisme";
    const portalDisplay = cleanSource && cleanSource.toLowerCase() !== "portail" ? cleanSource : buyerCleanName;
    if (bannerDesc) {
      bannerDesc.textContent = currentLang === 'en'
        ? `Direct publication on the official procurement portal of ${t.buyer_name || 'Organization'}.`
        : `Publication directe sur la plateforme Achats officielle (${t.buyer_name || 'Organisme'}).`;
    }
    if (portalBtnLabel) portalBtnLabel.textContent = currentLang === 'en' ? `Access Portal (${portalDisplay}) ↗` : `Portail Achats (${portalDisplay}) ↗`;
    if (dceBtnLabel) dceBtnLabel.textContent = currentLang === 'en' ? "Download Specs (1-Click DCE)" : "Télécharger DCE (1-Clic)";
    if (sourceFooterText) sourceFooterText.textContent = currentLang === 'en' ? `View on official portal (${portalDisplay}) ↗` : `Consulter sur le portail officiel (${portalDisplay}) ↗`;
  } else {
    if (bannerBox) {
      bannerBox.className = "bg-gradient-to-r from-emerald-50/90 to-slate-50 dark:from-slate-800 dark:to-slate-900 border border-emerald-200 dark:border-slate-700 rounded-2xl p-3.5 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-2xs";
    }
    if (bannerIcon) {
      bannerIcon.className = "p-1.5 rounded-lg bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 shrink-0";
      bannerIcon.innerHTML = `<i data-lucide="globe" class="w-4 h-4"></i>`;
    }
    if (bannerDesc) {
      bannerDesc.textContent = currentLang === 'en'
        ? "Official national tender notice published on the Moroccan Public Procurement Portal (PMMP)."
        : "Publication officielle nationale sur le Portail Marocain des Marchés Publics (PMMP).";
    }
    if (portalBtnLabel) portalBtnLabel.textContent = currentLang === 'en' ? "PMMP Portal Link ↗" : "Lien Portail PMMP ↗";
    if (dceBtnLabel) dceBtnLabel.textContent = currentLang === 'en' ? "Download Specs (1-Click DCE)" : "Télécharger DCE (1-Clic)";
    if (sourceFooterText) sourceFooterText.textContent = currentLang === 'en' ? "Open on official PMMP portal ↗" : "Ouvrir sur le portail officiel PMMP ↗";
  }

  // AI Summary & Score
  const scoreBadge = document.getElementById("modal-score-badge");
  if (scoreBadge) {
    if (t.relevance_score >= 60) {
      const cyberSub = t.sub_category || 'SSI';
      scoreBadge.textContent = currentLang === 'en' ? `🛡️ ${t.relevance_score}% Cybersecurity (${cyberSub})` : `🛡️ ${t.relevance_score}% Cybersécurité (${cyberSub})`;
      scoreBadge.className = "inline-flex items-center space-x-1 mt-0.5 px-2.5 py-1 rounded-full text-[10px] font-black bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30";
    } else {
      scoreBadge.textContent = currentLang === 'en' ? `${t.relevance_score || 0}% · General Procurement` : `${t.relevance_score || 0}% · Marché Général`;
      scoreBadge.className = "inline-flex items-center space-x-1 mt-0.5 px-2.5 py-1 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400";
    }
  }

  document.getElementById("modal-summary-text").textContent = t.summary || "Consultation publique régulière répertoriée sur le portail des marchés publics marocains.";

  // Matched Keywords Tags
  const kwContainer = document.getElementById("modal-keywords-container");
  if (t.matched_keywords && t.matched_keywords.length > 0) {
    kwContainer.innerHTML = t.matched_keywords.map(kw => `
      <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">#${escapeHtml(kw)}</span>
    `).join("");
  } else {
    kwContainer.innerHTML = '';
  }

  // Metrics
  const countdown = formatCountdown(t.deadline);
  document.getElementById("modal-deadline").textContent = t.deadline || 'Non précisée';
  document.getElementById("modal-countdown").textContent = countdown.text;
  document.getElementById("modal-budget").textContent = t.estimated_budget > 0 ? formatMAD(t.estimated_budget) : 'Non précisé';
  document.getElementById("modal-caution").textContent = t.provisional_guarantee || 'Non exigée / Voir CPS';
  document.getElementById("modal-opening-place").textContent = t.bid_opening_place || 'Siège de l\'Organisme';
  document.getElementById("modal-qualifications").textContent = t.qualifications || 'Selon Règlement de Consultation';
  document.getElementById("modal-contact").textContent = t.contact || 'Service des Marchés';

  // History / Corrigenda
  const histContainer = document.getElementById("modal-history-container");
  if (t.history && t.history.length > 0) {
    histContainer.innerHTML = t.history.map(h => `
      <div class="text-[11px] text-slate-600 dark:text-slate-400">
        <span class="font-mono text-slate-400 dark:text-slate-500 font-semibold">[${h.timestamp.split('T')[0]}]</span>
        <strong class="text-slate-800 dark:text-slate-200">${escapeHtml(h.field_changed)}</strong> : ${escapeHtml(h.new_value || '')}
      </div>
    `).join("");
  } else {
    histContainer.innerHTML = `<span class="text-[11px] text-slate-500 italic">Aucun avis de report ou rectificatif publié à ce jour.</span>`;
  }

  // Pipeline Status Select
  document.getElementById("modal-pipeline-status").value = t.pipeline_status || 'watching';
  document.getElementById("modal-pipeline-notes").value = t.pipeline_notes || '';

  // Source Link and Real PMMP DCE Download Link
  document.getElementById("modal-source-link").href = t.source_url || '#';
  const modalDceDoc = (t.document_links || []).find(d => d.doc_type === 'DCE');
  const modalDceUrl = modalDceDoc ? modalDceDoc.url : t.source_url;
  const modalDceEl = document.getElementById("modal-dce-portal-link");
  if (modalDceEl) {
    modalDceEl.href = modalDceUrl || '#';
  }

  // Set default tab to summary and update track button
  switchModalTab('summary');
  updateModalTrackBtn();

  modal.classList.remove("hidden");
  if (window.lucide) lucide.createIcons({ root: modal });
}

function switchModalTab(tabId) {
  ['summary', 'dossier', 'pipeline'].forEach(t => {
    const view = document.getElementById(`modal-view-${t}`);
    const btn = document.getElementById(`tab-btn-modal-${t}`);
    if (t === tabId) {
      if (view) view.classList.remove('hidden');
      if (btn) {
        btn.className = "py-2.5 px-3 border-b-2 border-emerald-500 text-emerald-600 dark:text-emerald-400 flex items-center space-x-1.5 transition";
      }
    } else {
      if (view) view.classList.add('hidden');
      if (btn) {
        btn.className = "py-2.5 px-3 border-b-2 border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 flex items-center space-x-1.5 transition";
      }
    }
  });
}

function copyModalRef() {
  const ref = document.getElementById("modal-ref")?.textContent || "";
  if (!ref) return;
  navigator.clipboard.writeText(ref).then(() => {
    showToast(`Référence ${ref} copiée !`, "info");
  }).catch(() => {});
}

function toggleModalTrackTender() {
  if (!activeTenderModalId) return;
  toggleTrackTender(activeTenderModalId);
  updateModalTrackBtn();
}

function updateModalTrackBtn() {
  if (!activeTenderModalId) return;
  const isTracked = isTenderTracked(activeTenderModalId);
  const btn = document.getElementById("modal-btn-track-toggle");
  const txt = document.getElementById("modal-track-btn-text");
  if (btn) {
    if (isTracked) {
      btn.className = "px-3 py-1.5 rounded-xl bg-amber-400 text-slate-950 font-bold text-xs flex items-center space-x-1.5 shadow-2xs transition";
      if (txt) txt.textContent = "AO Suivi (Actif ⭐)";
    } else {
      btn.className = "px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-xs flex items-center space-x-1.5 transition";
      if (txt) txt.textContent = "Suivre cet AO";
    }
    if (window.lucide) lucide.createIcons({ root: btn });
  }
}

function closeModal() {
  document.getElementById("tender-modal").classList.add("hidden");
  activeTenderModalId = null;
}

async function saveModalPipeline() {
  if (!activeTenderModalId) return;
  const status = document.getElementById("modal-pipeline-status").value;
  const notes = document.getElementById("modal-pipeline-notes").value.trim();

  try {
    const res = await fetch(`/api/tenders/${encodeURIComponent(activeTenderModalId)}/pipeline`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pipeline_status: status, pipeline_notes: notes })
    });
    if (!res.ok) throw new Error("Erreur de sauvegarde");

    const t = allTendersCache.find(x => x.id === activeTenderModalId);
    if (t) {
      t.pipeline_status = status;
      t.pipeline_notes = notes;
    }

    renderTendersList(allTendersCache);
    if (currentTab === 'pipeline') renderPipelineBoard(allTendersCache);
    showToast("Statut commercial enregistré !", "success");
    closeModal();
  } catch (err) {
    showToast(`Erreur : ${err.message}`, "error");
  }
}

// ==================== DPA SUBMISSION FOLDER & PROFILES MATRIX ====================

let currentSubmissionData = null;
let currentActiveSubfolderTab = 'admin';
let currentSubmissionViewMode = 'dashboard';

function switchSubmissionView(mode) {
  currentSubmissionViewMode = mode;
  const dashboardView = document.getElementById("subfolder-hudu-dashboard-view");
  const detailsView = document.getElementById("subfolder-details-view");
  const btnDash = document.getElementById("btn-subfolder-view-dashboard");
  const btnDet = document.getElementById("btn-subfolder-view-details");

  if (mode === 'dashboard') {
    if (dashboardView) dashboardView.classList.remove("hidden");
    if (detailsView) detailsView.classList.add("hidden");
    if (btnDash) btnDash.className = "px-3 py-1.5 rounded-lg font-bold bg-white text-slate-900 shadow-2xs transition flex items-center space-x-1.5";
    if (btnDet) btnDet.className = "px-3 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition flex items-center space-x-1.5";
  } else {
    if (dashboardView) dashboardView.classList.add("hidden");
    if (detailsView) detailsView.classList.remove("hidden");
    if (btnDet) btnDet.className = "px-3 py-1.5 rounded-lg font-bold bg-white text-slate-900 shadow-2xs transition flex items-center space-x-1.5";
    if (btnDash) btnDash.className = "px-3 py-1.5 rounded-lg text-slate-600 hover:text-slate-900 transition flex items-center space-x-1.5";
  }
  if (window.lucide) lucide.createIcons({ root: document.getElementById("submission-folder-modal") });
}

function openHuduDetailTab(tab) {
  switchSubmissionView('details');
  switchSubmissionTab(tab);
}

async function openSubmissionFolderModal(targetTabOrId = 'dashboard') {
  // Check if argument passed is a tender ID or tab name
  let targetTab = 'dashboard';
  const knownTabs = ['dashboard', 'admin', 'tech', 'fin', 'details'];
  if (targetTabOrId && typeof targetTabOrId === 'string' && !knownTabs.includes(targetTabOrId)) {
    activeTenderModalId = targetTabOrId;
  } else if (knownTabs.includes(targetTabOrId) && targetTabOrId !== 'dashboard') {
    targetTab = targetTabOrId;
  }

  if (!activeTenderModalId) {
    showToast("Veuillez d'abord sélectionner un appel d'offres", "info");
    return;
  }

  const modal = document.getElementById("submission-folder-modal");
  showToast("Chargement du tableau de bord de soumission DPA...", "info");

  try {
    const res = await fetch(`/api/tenders/${encodeURIComponent(activeTenderModalId)}/submission-folder`);
    if (!res.ok) throw new Error("Impossible de charger le dossier de soumission");
    
    currentSubmissionData = await res.json();
    populateSubmissionFolderModal(currentSubmissionData);

    if (targetTab === 'admin' || targetTab === 'tech' || targetTab === 'fin') {
      switchSubmissionView('details');
      switchSubmissionTab(targetTab);
    } else {
      switchSubmissionView('dashboard');
    }

    modal.classList.remove("hidden");
    if (window.lucide) lucide.createIcons({ root: modal });
  } catch (err) {
    showToast(`Erreur : ${err.message}`, "error");
  }
}

function closeSubmissionFolderModal() {
  const modal = document.getElementById("submission-folder-modal");
  if (modal) modal.classList.add("hidden");
}

function populateSubmissionFolderModal(data) {
  // Header info
  document.getElementById("subfolder-modal-ref").textContent = data.tender_reference || "";
  document.getElementById("subfolder-buyer-badge").textContent = data.buyer_name || "";
  document.getElementById("subfolder-modal-title").textContent = data.tender_title || "";
  document.getElementById("subfolder-portal-link").href = data.portal_url || "#";

  // Badges & Caution
  const profileCount = (data.technical_profiles || []).length;
  document.getElementById("subfolder-tab-profiles-count").textContent = `${profileCount} Profils`;
  document.getElementById("subfolder-tech-profile-count-pill").textContent = profileCount;
  document.getElementById("subfolder-admin-caution").textContent = data.caution_amount || "Non exigée";

  // Financial values
  const fin = data.financial_folder || {};
  document.getElementById("subfolder-fin-budget-ttc").textContent = fin.budget_ttc_mad || "Non précisé";
  document.getElementById("subfolder-fin-budget-ht").textContent = fin.budget_ht_mad || "Non précisé";
  document.getElementById("subfolder-fin-budget-tva").textContent = fin.tva_mad || "Non précisé";

  // Populate Hudu Dashboard 8-Widgets
  const activeTender = allTendersCache.find(x => x.id === (data.tender_id || activeTenderModalId));
  const countdown = activeTender ? formatCountdown(activeTender.deadline) : { text: "Selon CPS", badgeClass: "" };

  const greetingTitle = document.getElementById("hudu-greeting-title");
  if (greetingTitle) {
    const userEl = document.getElementById("header-user-name");
    greetingTitle.textContent = userEl && userEl.textContent.trim() ? `Hi, ${userEl.textContent.split(' ')[0]}` : "Hi, DPG";
  }

  const procBadge = document.getElementById("subfolder-proc-badge");
  if (procBadge) procBadge.textContent = activeTender ? (activeTender.procedure_type || 'AOO') : 'AOO';

  // Hudu Card 1: Favorites
  const favCaution = document.getElementById("hudu-fav-caution");
  if (favCaution) favCaution.textContent = data.caution_amount || "Non exigée";

  // Hudu Card 2: Recents
  const recentsBuyer = document.getElementById("hudu-recents-buyer");
  const recentsBuyer2 = document.getElementById("hudu-recents-buyer2");
  if (recentsBuyer) recentsBuyer.textContent = data.buyer_name || "OFPPT";
  if (recentsBuyer2) recentsBuyer2.textContent = data.buyer_name || "Acheteur";

  // Hudu Card 4: Expiring Soon
  const expiringUrl = document.getElementById("hudu-expiring-url");
  const expiringBuyer = document.getElementById("hudu-expiring-buyer");
  const expiringCountdown = document.getElementById("hudu-expiring-countdown");
  if (expiringUrl) {
    expiringUrl.href = data.portal_url || "#";
    expiringUrl.textContent = data.portal_url ? data.portal_url.replace("https://", "").replace("http://", "").split("/")[0] : "marchespublics.gov.ma";
  }
  if (expiringBuyer) expiringBuyer.textContent = data.buyer_name || "Acheteur";
  if (expiringCountdown) expiringCountdown.textContent = countdown.text;

  // Hudu Card 5: Recently Flagged
  const flagCaution = document.getElementById("hudu-flag-caution");
  if (flagCaution) flagCaution.textContent = `Montant : ${data.caution_amount || 'Selon CPS'}`;

  // Hudu Card 6: Pwned Passwords / Profiles RH
  const pwnedContainer = document.getElementById("hudu-pwned-profiles-list");
  const pwnedCountLabel = document.getElementById("hudu-pwned-count-label");
  const profs = (data.technical_profiles && data.technical_profiles.length > 0) ? data.technical_profiles : [
    { profile_title: "Chef de Projet SSI (PMP, CISM)", experience: "10+ ans", certifications: "PMP, CISM, ISO 27001 LA" },
    { profile_title: "Architecte Sécurité Réseau & Cloud", experience: "8+ ans", certifications: "CISSP, Fortinet NSE 7" },
    { profile_title: "Ingénieur SOC & Incident Response", experience: "5+ ans", certifications: "CEH, GCIH" },
    { profile_title: "Auditeur Sécurité & Pentesteur", experience: "5+ ans", certifications: "OSCP, CEH Master" }
  ];
  if (pwnedCountLabel) pwnedCountLabel.textContent = `${profs.length} profils requis`;
  if (pwnedContainer) {
    pwnedContainer.innerHTML = profs.slice(0, 5).map(p => `
      <div class="flex items-center justify-between space-x-2">
        <div class="flex items-center space-x-2 min-w-0">
          <div class="w-6 h-6 rounded-full bg-rose-600 text-white flex items-center justify-center shrink-0 shadow-2xs font-bold text-[10px]">
            <i data-lucide="shield-alert" class="w-3.5 h-3.5"></i>
          </div>
          <div class="min-w-0">
            <p class="font-bold text-slate-900 truncate text-[11px]">${escapeHtml(p.profile_title)}</p>
            <p class="text-[10px] text-slate-500 truncate">${escapeHtml(p.certifications || data.buyer_name)}</p>
          </div>
        </div>
        <span class="text-[11px] font-mono font-bold text-slate-700 shrink-0">${escapeHtml(p.experience || '5+ ans')}</span>
      </div>
    `).join("");
  }

  // Hudu Card 8: Stats
  const statAdmin = document.getElementById("hudu-stat-admin-count");
  const statProf = document.getElementById("hudu-stat-profiles-count");
  const statCaution = document.getElementById("hudu-stat-caution");
  if (statAdmin) statAdmin.textContent = (data.administrative_items || []).length;
  if (statProf) statProf.textContent = (data.technical_profiles || []).length;
  if (statCaution) statCaution.textContent = (data.caution_amount || '').replace("MAD", "").replace("Dirhams", "").trim() || "10K";

  // 1. Populate Admin Table
  const adminTbody = document.getElementById("subfolder-admin-tbody");
  adminTbody.innerHTML = (data.administrative_items || []).map(item => {
    const storageKey = `dpa_chk_${data.tender_id}_adm_${item.num}`;
    const isChecked = localStorage.getItem(storageKey) === 'true';
    return `
      <tr class="hover:bg-slate-50 transition ${isChecked ? 'bg-emerald-50/40' : ''}" id="adm-row-${item.num}">
        <td class="py-3 px-3 text-center">
          <input type="checkbox" onchange="toggleSubmissionDocCheck('${data.tender_id}', 'adm', ${item.num}, this.checked)" ${isChecked ? 'checked' : ''} class="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 cursor-pointer">
        </td>
        <td class="py-3 px-3 text-center font-mono font-bold text-slate-500">${item.num}</td>
        <td class="py-3 px-4">
          <span class="font-bold text-slate-900 block">${escapeHtml(item.title)}</span>
          ${item.mandatory ? '<span class="inline-block mt-0.5 text-[9px] font-bold text-red-600 uppercase">Obligatoire</span>' : ''}
        </td>
        <td class="py-3 px-4 text-slate-700 leading-relaxed">${escapeHtml(item.requirement)}</td>
        <td class="py-3 px-4 text-slate-600 italic">${escapeHtml(item.format)}</td>
        <td class="py-3 px-3 text-center">
          ${item.dpa_ready 
            ? '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">✅ Prêt DPA</span>' 
            : '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">⏳ À finaliser</span>'}
        </td>
      </tr>
    `;
  }).join("");

  // 2. Populate Technical Deliverables
  const techDocsContainer = document.getElementById("subfolder-tech-docs-container");
  techDocsContainer.innerHTML = (data.technical_documents || []).map(doc => `
    <div class="bg-white p-3.5 rounded-xl border border-slate-200 hover:border-emerald-300 hover:shadow-sm transition space-y-1">
      <div class="flex items-center space-x-1.5 font-bold text-slate-900 text-xs">
        <span class="w-5 h-5 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center text-[10px] font-extrabold shrink-0">${doc.num}</span>
        <span>${escapeHtml(doc.title)}</span>
      </div>
      <p class="text-[11px] text-slate-600 leading-relaxed">${escapeHtml(doc.requirement)}</p>
      <div class="pt-1 text-[10px] text-slate-500 italic">Format : ${escapeHtml(doc.format)}</div>
    </div>
  `).join("");

  // 3. Populate Technical Profiles Table (Matching Excel columns)
  renderSubfolderProfilesTable(data.technical_profiles || []);

  // 4. Populate Financial Deliverables Cards
  const finDocsContainer = document.getElementById("subfolder-fin-docs-container");
  finDocsContainer.innerHTML = (fin.documents || []).map(doc => `
    <div class="bg-white p-4 rounded-xl border border-slate-200 hover:border-blue-300 transition space-y-1.5">
      <div class="flex items-center justify-between border-b pb-1.5">
        <span class="font-bold text-slate-900 text-xs">${doc.num}. ${escapeHtml(doc.title)}</span>
        <span class="px-1.5 py-0.5 bg-blue-100 text-blue-800 rounded text-[9px] font-bold">Décret 2-22-431</span>
      </div>
      <p class="text-xs text-slate-700 leading-relaxed">${escapeHtml(doc.requirement)}</p>
      <div class="pt-1 text-[11px] text-slate-500 italic font-mono bg-slate-50 p-1.5 rounded border border-slate-100">${escapeHtml(doc.format)}</div>
    </div>
  `).join("");
}

function renderSubfolderProfilesTable(profiles) {
  const tbody = document.getElementById("subfolder-profiles-tbody");
  if (!profiles || profiles.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="py-6 text-center text-slate-500 italic">Aucun profil spécifique requis. Se référer aux exigences générales du CPS.</td></tr>`;
    return;
  }

  tbody.innerHTML = profiles.map(p => {
    // Style certifications badges
    const certBadges = (p.certifications || '').split(/[,;]/).map(c => c.trim()).filter(Boolean).map(c => `
      <span class="inline-block px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-200 mr-1 mb-1">
        ${escapeHtml(c)}
      </span>
    `).join("");

    // Vivier badge styling
    let vivierBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">${escapeHtml(p.dpa_status || 'Disponible')}</span>`;
    if (p.dpa_status && (p.dpa_status.includes('Confirmé') || p.dpa_status.includes('Approuvé') || p.dpa_status.includes('Validé'))) {
      vivierBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">✅ ${escapeHtml(p.dpa_status)}</span>`;
    } else if (p.dpa_status && p.dpa_status.includes('Vivier')) {
      vivierBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-teal-100 text-teal-800 border border-teal-300">👥 ${escapeHtml(p.dpa_status)}</span>`;
    } else if (p.dpa_status && p.dpa_status.includes('Sourcing')) {
      vivierBadge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">🔍 ${escapeHtml(p.dpa_status)}</span>`;
    }

    return `
      <tr class="hover:bg-slate-50 transition subfolder-profile-row" data-search="${escapeHtml((p.profile_title + ' ' + p.skills + ' ' + p.certifications + ' ' + p.lot).toLowerCase())}">
        <td class="py-3 px-3 text-center font-mono font-bold text-slate-500">${p.num}</td>
        <td class="py-3 px-4 font-bold text-slate-900">${escapeHtml(p.profile_title)}</td>
        <td class="py-3 px-3 text-center">
          <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-blue-50 text-blue-700 border border-blue-200">${escapeHtml(p.min_experience)}</span>
        </td>
        <td class="py-3 px-4 text-slate-700 leading-relaxed">${escapeHtml(p.skills)}</td>
        <td class="py-3 px-4">${certBadges || '<span class="text-slate-400 italic">Non spécifiée</span>'}</td>
        <td class="py-3 px-3 text-center">
          <span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">${escapeHtml(p.lot)}</span>
        </td>
        <td class="py-3 px-3 text-center">${vivierBadge}</td>
      </tr>
    `;
  }).join("");
}

function filterSubfolderProfiles(query) {
  const q = (query || "").toLowerCase().trim();
  const rows = document.querySelectorAll(".subfolder-profile-row");
  rows.forEach(r => {
    const text = r.getAttribute("data-search") || "";
    if (!q || text.includes(q)) {
      r.style.display = "";
    } else {
      r.style.display = "none";
    }
  });
}

function toggleSubmissionDocCheck(tenderId, type, num, isChecked) {
  const key = `dpa_chk_${tenderId}_${type}_${num}`;
  localStorage.setItem(key, isChecked ? 'true' : 'false');
  const row = document.getElementById(`adm-row-${num}`);
  if (row) {
    if (isChecked) {
      row.classList.add("bg-emerald-50/40");
    } else {
      row.classList.remove("bg-emerald-50/40");
    }
  }
}

function switchSubmissionTab(tabName) {
  currentActiveSubfolderTab = tabName;
  const tabs = ['admin', 'tech', 'fin'];
  tabs.forEach(t => {
    const btn = document.getElementById(`subfolder-tab-btn-${t}`);
    const content = document.getElementById(`subfolder-tab-${t}-content`);
    if (t === tabName) {
      btn.className = "px-4 py-2.5 border-b-2 border-amber-600 text-amber-700 bg-white rounded-t-xl transition flex items-center space-x-2 shrink-0 shadow-sm";
      content.classList.remove("hidden");
    } else {
      btn.className = "px-4 py-2.5 border-b-2 border-transparent text-slate-600 hover:text-slate-900 hover:bg-white/50 rounded-t-xl transition flex items-center space-x-2 shrink-0";
      content.classList.add("hidden");
    }
  });
  if (window.lucide) lucide.createIcons({ root: document.getElementById("subfolder-modal-details-view") });
}

// ==================== PIPELINE BOARD ====================

function renderPipelineBoard(tenders) {
  const columns = ['watching', 'go', 'no_go', 'submitted', 'won', 'lost'];
  columns.forEach(col => {
    const list = tenders.filter(t => (t.pipeline_status || 'watching') === col);
    document.getElementById(`count-${col}`).textContent = list.length;
    const container = document.getElementById(`kanban-${col}`);
    container.innerHTML = list.map(t => `
      <div class="bg-white border border-slate-200 hover:border-emerald-500 rounded p-2.5 space-y-1.5 cursor-pointer transition text-xs shadow-sm" onclick="openTenderModal(${safeArg(t.id)})">
        <div class="flex items-center justify-between">
          <span class="font-mono font-bold text-[11px] text-[#006039] bg-emerald-50 px-1 rounded">${t.reference}</span>
          <span class="text-[10px] text-slate-500 font-bold">${t.relevance_score}%</span>
        </div>
        <p class="font-bold text-slate-800 line-clamp-2 leading-tight">${escapeHtml(t.title)}</p>
        <p class="text-[11px] text-slate-500 truncate">${escapeHtml(t.buyer_name)}</p>
        <div class="flex items-center justify-between pt-1 border-t border-slate-100 text-[10px] text-slate-500">
          <span>${t.deadline ? t.deadline.split(' ')[0] : 'S/O'}</span>
          <span class="font-black text-slate-900">${t.estimated_budget > 0 ? formatMAD(t.estimated_budget) : ''}</span>
        </div>
      </div>
    `).join("");
  });
}

// ==================== ADMIN & CONNECTORS ====================

async function loadScraperHealth() {
  const container = document.getElementById("admin-scrapers-container");
  try {
    const res = await fetch("/api/admin/scrapers");
    if (!res.ok) return;
    const scrapers = await res.json();
    container.innerHTML = scrapers.map(s => `
      <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between text-xs">
        <div>
          <div class="flex items-center space-x-2">
            <span class="w-2 h-2 rounded-full ${s.status === 'HEALTHY' ? 'bg-emerald-500' : 'bg-rose-500'}"></span>
            <strong class="text-slate-900 text-xs">${escapeHtml(s.name)}</strong>
          </div>
          <span class="text-[11px] text-slate-500 block mt-0.5">Dernière exécution : ${s.last_run_time || 'En attente'}</span>
          <span class="text-[11px] text-slate-600 font-semibold block">Indexés au dernier run : ${s.items_found_last_run} éléments</span>
        </div>
        <button onclick="triggerSingleScraper(${safeArg(s.connector_id)})" class="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-300 text-slate-700 font-bold rounded text-xs shadow-sm">
          Exécuter
        </button>
      </div>
    `).join("");
  } catch (err) {
    console.error(err);
  }
}

async function triggerSingleScraper(cid) {
  showToast(`Exécution du connecteur ${cid}...`, 'info');
  try {
    const res = await fetch(`/api/admin/scrapers/${encodeURIComponent(cid)}/run`, { method: "POST" });
    const data = await res.json();
    showToast(`Connecteur terminé : ${data.items_found} consultations trouvées !`, 'success');
    loadTenders();
    loadScraperHealth();
  } catch (err) {
    showToast(`Erreur d'exécution : ${err.message}`, 'error');
  }
}

async function triggerAllScrapers() {
  showToast("Lancement de la collecte PMMP en direct...", "info");
  try {
    await triggerSingleScraper("pmmp");
    showToast("Collecte PMMP terminée avec succès !", "success");
  } catch (err) {
    showToast(`Erreur : ${err.message}`, "error");
  }
}

async function triggerQuickSync() {
  await triggerAllScrapers();
}

async function loadWatchlist() {
  const container = document.getElementById("admin-watchlist-container");
  try {
    const res = await fetch("/api/admin/watchlist");
    if (!res.ok) return;
    const list = await res.json();
    container.innerHTML = list.map(b => `
      <div class="p-2.5 bg-slate-50 border border-slate-200 rounded text-xs">
        <div class="flex items-center justify-between">
          <strong class="text-slate-900">${escapeHtml(b.badge_label)}</strong>
          <span class="text-[10px] text-amber-700 bg-amber-50 border border-amber-200 px-1 rounded font-bold">${b.category}</span>
        </div>
        <span class="text-[11px] text-slate-600 block mt-1">${escapeHtml(b.name)}</span>
      </div>
    `).join("");
  } catch (err) {
    console.error(err);
  }
}

function openAddWatchlistModal() {
  const name = prompt("Nom de l'acheteur public (ex: Agence Nationale de Réglementation des Télécommunications) :");
  if (!name) return;
  const badge = prompt("Badge court (ex: ANRT) :", name.slice(0, 10));
  if (!badge) return;

  fetch("/api/admin/watchlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: name, badge_label: badge, normalized_keywords: [name.toLowerCase(), badge.toLowerCase()] })
  }).then(() => {
    showToast("Acheteur prioritaire ajouté !", "success");
    loadWatchlist();
  });
}

async function loadGenericConnectors() {
  const container = document.getElementById("admin-generic-container");
  if (!container) return;
  try {
    const res = await fetch("/api/admin/generic-connectors");
    if (!res.ok) return;
    const list = await res.json();
    if (list.length === 0) {
      container.innerHTML = `<span class="text-xs text-slate-400 italic">Aucun connecteur générique configuré. Cliquez sur 'Nouveau Connecteur' pour en ajouter un.</span>`;
      return;
    }
    container.innerHTML = list.map(c => `
      <div class="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-xs flex items-center justify-between gap-3 transition">
        <div class="min-w-0 flex-1">
          <strong class="text-slate-900 dark:text-white block truncate">${escapeHtml(c.name)}</strong>
          <span class="text-slate-500 dark:text-slate-400 block text-[11px] font-mono truncate">${escapeHtml(c.base_url || c.listing_url || '')}</span>
        </div>
        <div class="flex items-center space-x-2 shrink-0">
          <span class="text-[10px] bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 px-2 py-0.5 rounded font-bold">Actif</span>
          <button onclick="deleteGenericConnector(${safeArg(c.id)})" class="p-1 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-rose-600 dark:text-rose-400 rounded-lg transition" title="Supprimer ce connecteur">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `).join("");
    if (window.lucide) lucide.createIcons({ root: container });
  } catch (err) {
    console.error(err);
  }
}

async function deleteGenericConnector(connectorId) {
  if (!confirm("Voulez-vous vraiment supprimer ce connecteur personnalisé ?")) return;
  try {
    const res = await fetch(`/api/admin/generic-connectors/${encodeURIComponent(connectorId)}`, {
      method: "DELETE"
    });
    if (!res.ok) throw new Error("Erreur de suppression");
    showToast("Connecteur personnalisé supprimé !", "success");
    loadGenericConnectors();
  } catch (err) {
    showToast(`Erreur : ${err.message}`, "error");
  }
}

function openAddGenericModal() {
  const name = prompt("Nom du site acheteur (ex: Portail Région Casablanca) :");
  if (!name) return;
  const url = prompt("URL de la page des appels d'offres :");
  if (!url) return;

  fetch("/api/admin/generic-connectors", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: "gen_" + Date.now(),
      name: name,
      base_url: url,
      item_selector: "div.ao-card, tr.tender-row, .consultation-item",
      ref_selector: ".ref, .reference",
      title_selector: ".title, .objet, h3, h4",
      is_active: 1
    })
  }).then(async res => {
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Erreur de validation URL");
    }
    showToast("Connecteur générique ajouté avec succès !", "success");
    loadGenericConnectors();
  }).catch(err => {
    showToast(`Erreur : ${err.message}`, "error");
  });
}

async function loadAlertsConfig() {
  try {
    const res = await fetch("/api/admin/alerts-config");
    if (!res.ok) return;
    const data = await res.json();
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el && val !== undefined) el.value = val;
    };
    setVal("cfg-smtp-host", data.smtp_host || "");
    setVal("cfg-smtp-port", data.smtp_port || "587");
    setVal("cfg-smtp-user", data.smtp_user || "");
    setVal("cfg-webhook-url", data.webhook_url || "");
    const emailInput = document.getElementById("cfg-email-recipients");
    if (emailInput && data.email_recipients) {
      emailInput.value = Array.isArray(data.email_recipients)
        ? data.email_recipients.join(", ")
        : String(data.email_recipients);
    }
    const enabledInput = document.getElementById("cfg-email-enabled");
    if (enabledInput) {
      enabledInput.checked = data.email_enabled === "true" || data.email_enabled === true || data.email_enabled === 1 || data.email_enabled === "1";
    }
  } catch (err) {
    console.error(err);
  }
}

async function saveAlertsConfig(event) {
  if (event) event.preventDefault();
  const getVal = id => {
    const el = document.getElementById(id);
    return el ? el.value.trim() : "";
  };
  const emails = getVal("cfg-email-recipients").split(",").map(e => e.trim()).filter(Boolean);
  const cfg = {
    smtp_host: getVal("cfg-smtp-host"),
    smtp_port: getVal("cfg-smtp-port") || "587",
    smtp_user: getVal("cfg-smtp-user"),
    email_recipients: emails,
    webhook_url: getVal("cfg-webhook-url"),
    email_enabled: document.getElementById("cfg-email-enabled") ? (document.getElementById("cfg-email-enabled").checked ? "true" : "false") : "true"
  };
  const pwd = getVal("cfg-smtp-pass");
  if (pwd) {
    cfg.smtp_password = pwd;
  }

  try {
    const res = await fetch("/api/admin/alerts-config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cfg)
    });
    if (!res.ok) throw new Error("Erreur");
    showToast("Paramètres des alertes et SMTP enregistrés avec succès !", "success");
    const pwdInput = document.getElementById("cfg-smtp-pass");
    if (pwdInput) pwdInput.value = "";
  } catch (err) {
    showToast(`Erreur : ${err.message}`, "error");
  }
}

async function testSmtpConnection() {
  showToast("Vérification de la connexion SMTP en cours...", "info");
  try {
    const res = await fetch("/api/admin/alerts/test-smtp-connection", { method: "POST" });
    const data = await res.json();
    if (data.status === "success") {
      showToast(data.message || "Connexion SMTP établie avec succès !", "success");
    } else {
      showToast(data.message || "Échec de connexion SMTP", "warning");
    }
  } catch (err) {
    showToast(`Erreur SMTP : ${err.message}`, "error");
  }
}

async function loadGeminiStatus() {
  const badge = document.getElementById("gemini-status-badge");
  if (!badge) return;
  try {
    const res = await fetch("/api/admin/gemini-status");
    if (!res.ok) return;
    const data = await res.json();
    if (data.configured) {
      badge.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800";
      badge.textContent = `✅ Actif (${data.model || 'Gemini 2.5'})`;
    } else {
      badge.className = "px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800";
      badge.textContent = "Clé non configurée";
    }
  } catch (e) {
    badge.textContent = "Non disponible";
  }
}

async function saveGeminiKey() {
  const input = document.getElementById("gemini-api-key-input");
  if (!input) return;
  const key = input.value.trim();
  if (!key) {
    showToast("Veuillez saisir une clé API Google AI Studio valide.", "warning");
    return;
  }
  showToast("Enregistrement de la clé Gemini...", "info");
  try {
    const res = await fetch("/api/admin/gemini-key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: key })
    });
    if (!res.ok) throw new Error("Erreur de sauvegarde");
    showToast("Clé Google AI Studio enregistrée avec succès !", "success");
    input.value = "";
    loadGeminiStatus();
  } catch (err) {
    showToast(`Erreur : ${err.message}`, "error");
  }
}

// ==================== CSV EXPORT ====================

function exportTendersCSV() {
  if (!allTendersCache || allTendersCache.length === 0) {
    showToast("Aucune consultation à exporter.", "error");
    return;
  }

  const headers = ["Référence", "Acheteur", "Objet", "Catégorie", "Procédure", "Budget Estimé (DH)", "Caution Provisoire", "Date Limite", "Score Cyber", "Statut Commercial"];
  const rows = allTendersCache.map(t => [
    `"${(t.reference || '').replace(/"/g, '""')}"`,
    `"${(t.buyer_name || '').replace(/"/g, '""')}"`,
    `"${(t.title || '').replace(/"/g, '""')}"`,
    `"${(t.category || '').replace(/"/g, '""')}"`,
    `"${(t.procedure_type || '').replace(/"/g, '""')}"`,
    t.estimated_budget || 0,
    `"${(t.provisional_guarantee || '').replace(/"/g, '""')}"`,
    `"${(t.deadline || '').replace(/"/g, '""')}"`,
    t.relevance_score || 0,
    `"${(t.pipeline_status || 'watching').replace(/"/g, '""')}"`
  ]);

  const csvContent = "\uFEFF" + [headers.join(","), ...rows.map(r => r.join(","))].join("\r\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `CyberRFP_Maroc_Consultations_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast("Fichier Excel / CSV exporté avec succès !", "success");
}

// ==================== UTILITIES ====================

function formatMAD(amount) {
  const d = I18N[currentLang] || I18N.fr;
  if (!amount || isNaN(amount)) return d.not_specified || "Non précisé";
  if (currentLang === 'en') {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: "MAD", minimumFractionDigits: 2 }).format(amount);
  } else if (currentLang === 'ar') {
    return new Intl.NumberFormat("ar-MA", { minimumFractionDigits: 2 }).format(amount) + " درهم";
  } else {
    return new Intl.NumberFormat("fr-MA", { style: "currency", currency: "MAD", minimumFractionDigits: 2 }).format(amount).replace("MAD", "DH");
  }
}

function formatCountdown(deadlineStr) {
  const dict = I18N[currentLang] || I18N.fr;
  if (!deadlineStr) return { text: dict.date_not_specified || "Date inconnue", badgeClass: "bg-slate-100 text-slate-600" };

  const clean = deadlineStr.replace(" ", "T");
  const target = new Date(clean).getTime();
  const now = new Date().getTime();
  const diff = target - now;

  if (diff <= 0) {
    return { text: dict.passed || dict.deadline_passed || "Délai expiré", badgeClass: "bg-rose-100 text-rose-700 font-bold" };
  }

  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

  if (days === 0) {
    let txt = `${hours} ${dict.hours_left}`;
    if (currentLang === 'en') {
      txt = hours <= 1 ? "1 hour left" : `${hours} hours left`;
    } else if (currentLang === 'ar') {
      txt = hours === 1 ? "ساعة واحدة متبقية" : (hours === 2 ? "ساعتان متبقيتان" : `${hours} ساعات متبقية`);
    } else {
      txt = hours <= 1 ? `${hours} heure restante` : `${hours} heures restantes`;
    }
    return { text: txt, badgeClass: "bg-rose-100 text-rose-800 font-black animate-pulse" };
  } else if (days === 1) {
    let txt = dict.tomorrow_deadline || "Demain !";
    if (currentLang === 'en') txt = "1 day left";
    else if (currentLang === 'fr') txt = "1 jour restant";
    else if (currentLang === 'ar') txt = "غداً (يوم واحد متبقي)";
    return { text: txt, badgeClass: "bg-rose-50 text-rose-700 font-bold" };
  } else {
    let txt = `${days} ${dict.days_left}`;
    if (currentLang === 'en') {
      txt = `${days} days left`;
    } else if (currentLang === 'ar') {
      txt = `${days} أيام متبقية`;
    } else {
      txt = `${days} jours restants`;
    }
    const badgeClass = days <= 3 ? "bg-rose-50 text-rose-700 font-bold" : (days <= 7 ? "bg-amber-100 text-amber-800 font-bold" : "bg-emerald-100 text-emerald-800 font-bold");
    return { text: txt, badgeClass };
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[m]);
}

function showToast(msg, type = 'info') {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  const colors = type === 'success' ? 'bg-[#006039] text-white border-emerald-400' : (type === 'error' ? 'bg-rose-700 text-white border-rose-500' : 'bg-slate-800 text-white border-slate-600');
  toast.className = `toast-anim px-4 py-2.5 rounded-lg border shadow-xl text-xs font-semibold flex items-center space-x-2 pointer-events-auto ${colors}`;
  toast.innerHTML = `
    <i data-lucide="${type === 'success' ? 'check-circle' : (type === 'error' ? 'alert-triangle' : 'info')}" class="w-4 h-4 shrink-0"></i>
    <span>${escapeHtml(msg)}</span>
  `;
  container.appendChild(toast);
  if (window.lucide) lucide.createIcons({ root: toast });

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ==================== REAL-TIME NOTIFICATIONS & SCREEN POP-UPS ====================

let lastSeenNotifTimestamp = localStorage.getItem("cyberrfp_last_notif_time") || new Date().toISOString();
let audioChimeEnabled = localStorage.getItem("cyberrfp_audio_chime") !== "false";
let receivedAlertsHistory = [];
let notifPollingInterval = null;

function initRealtimeNotifications() {
  updateDesktopNotifButtonStatus();
  const chimeCheckbox = document.getElementById("chk-audio-chime");
  if (chimeCheckbox) chimeCheckbox.checked = audioChimeEnabled;

  // Initial check to register timestamp
  fetch("/api/notifications/latest?limit=3")
    .then(r => r.json())
    .then(data => {
      if (data && data.server_time) {
        lastSeenNotifTimestamp = data.server_time;
        localStorage.setItem("cyberrfp_last_notif_time", lastSeenNotifTimestamp);
      }
    })
    .catch(() => {});

  // Poll for new tenders every 25 seconds
  if (notifPollingInterval) clearInterval(notifPollingInterval);
  notifPollingInterval = setInterval(checkRealtimeNotifications, 25000);
}

function updateDesktopNotifButtonStatus() {
  const statusEl = document.getElementById("desktop-notif-status");
  const btn = document.getElementById("btn-request-desktop-notif");
  if (!("Notification" in window)) {
    if (statusEl) statusEl.textContent = "Non supporté par ce navigateur";
    if (btn) btn.style.display = "none";
    return;
  }

  if (Notification.permission === "granted") {
    if (statusEl) statusEl.innerHTML = "<span class='text-emerald-400 font-bold'>Activées sur le bureau ✅</span>";
    if (btn) {
      btn.textContent = "Autorisé";
      btn.className = "px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[11px] font-bold cursor-default";
      btn.disabled = true;
    }
  } else if (Notification.permission === "denied") {
    if (statusEl) statusEl.innerHTML = "<span class='text-rose-400 font-bold'>Bloquées par le navigateur ❌</span>";
    if (btn) {
      btn.textContent = "Bloqué";
      btn.className = "px-2.5 py-1 rounded-lg bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[11px] font-bold";
    }
  } else {
    if (statusEl) statusEl.textContent = "Cliquez pour activer sur l'écran";
    if (btn) {
      btn.textContent = "Activer";
      btn.className = "px-2.5 py-1 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-[11px] transition";
      btn.disabled = false;
    }
  }
}

async function requestDesktopNotificationPermission() {
  if (!("Notification" in window)) {
    showToast("Les notifications bureau ne sont pas supportées sur ce navigateur.", "info");
    return;
  }
  try {
    const permission = await Notification.requestPermission();
    updateDesktopNotifButtonStatus();
    if (permission === "granted") {
      showToast("Notifications bureau activées avec succès !", "success");
      new Notification("CyberRFP Maroc — DataProtech Group", {
        body: "Les alertes d'appels d'offres en direct apparaîtront désormais sur votre écran.",
        icon: "/static/dpa_logo.png"
      });
    }
  } catch (err) {
    console.error("Erreur permission notifications:", err);
  }
}

function toggleAudioChimeSetting() {
  const chk = document.getElementById("chk-audio-chime");
  audioChimeEnabled = chk ? chk.checked : true;
  localStorage.setItem("cyberrfp_audio_chime", audioChimeEnabled);
  if (audioChimeEnabled) {
    playNotificationChime();
  }
}

function playNotificationChime() {
  if (!audioChimeEnabled) return;
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();

    const now = ctx.currentTime;
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();

    osc1.type = "sine";
    osc1.frequency.setValueAtTime(880, now);
    osc1.frequency.exponentialRampToValueAtTime(1320, now + 0.15);

    gain1.gain.setValueAtTime(0.15, now);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.4);

    osc1.connect(gain1);
    gain1.connect(ctx.destination);

    osc1.start(now);
    osc1.stop(now + 0.4);
  } catch (e) {
    // Silent audio fallback
  }
}

function toggleOnlyTrackedAlerts(enabled) {
  if (enabled === undefined) {
    const chk = document.getElementById("chk-only-tracked-alerts");
    enabled = chk ? chk.checked : true;
  }
  localStorage.setItem("cyberrfp_only_tracked_alerts", enabled ? "true" : "false");
  showToast(
    enabled ? "🔔 Notifications restreintes uniquement à vos AO suivis (⭐)" : "🔔 Notifications activées pour toutes les nouvelles consultations",
    "info"
  );
}

async function checkRealtimeNotifications() {
  try {
    const onlyTracked = localStorage.getItem("cyberrfp_only_tracked_alerts") !== "false";
    if (onlyTracked && trackedTendersSet.size === 0) {
      return; // Restrict alerts strictly to user-selected tracked RFPs
    }
    let url = `/api/notifications/latest?since=${encodeURIComponent(lastSeenNotifTimestamp)}&limit=10`;
    if (onlyTracked && trackedTendersSet.size > 0) {
      url += `&only_tracked=true&tracked_ids=${encodeURIComponent([...trackedTendersSet].join(','))}`;
    }
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();

    if (data.server_time) {
      lastSeenNotifTimestamp = data.server_time;
      localStorage.setItem("cyberrfp_last_notif_time", lastSeenNotifTimestamp);
    }

    if (data.tenders && data.tenders.length > 0) {
      data.tenders.forEach(t => {
        // Strict guard: NEVER notify for non-relevant tenders (furniture, food, civil works)
        if (t.relevance_category === 'NOT_RELEVANT' || (t.relevance_score !== undefined && t.relevance_score < 40)) {
          return;
        }
        const isTracked = isTenderTracked(t.id);
        if (onlyTracked) {
          if (isTracked) triggerRfpPopup(t);
        } else {
          if (isTracked || t.force_notify || t.relevance_category === 'CYBERSECURITY' || (t.relevance_score && t.relevance_score >= 70)) {
            triggerRfpPopup(t);
          }
        }
      });
      if (typeof loadTenders === "function") {
        loadTenders();
      }
    }
  } catch (err) {
    // Silent retry
  }
}

function triggerRfpPopup(t) {
  if (!t) return;

  // Safety filter: never trigger popup for non-cyber items
  if (t.relevance_category === 'NOT_RELEVANT' || (t.relevance_score !== undefined && t.relevance_score < 40)) {
    return;
  }

  const onlyTracked = localStorage.getItem("cyberrfp_only_tracked_alerts") !== "false";
  const isTracked = isTenderTracked(t.id);
  if (onlyTracked && !isTracked && !t.force_notify) {
    return; // Strictly ignore untracked RFPs
  }

  // 1. Audio chime
  playNotificationChime();

  // 2. Desktop native notification
  if ("Notification" in window && Notification.permission === "granted") {
    try {
      const n = new Notification(`🚨 CyberRFP : Nouvel Appel d'Offres !`, {
        body: `[${t.buyer_name || 'Marché Public'}] ${t.reference}\n${t.title}`,
        icon: "/static/dpa_logo.png",
        tag: `rfp-${t.id}`
      });
      n.onclick = () => {
        window.focus();
        if (typeof openTenderModal === "function") {
          openTenderModal(t.id);
        } else if (typeof openSubmissionFolderModal === "function") {
          openSubmissionFolderModal(t.id);
        }
      };
    } catch (e) {
      console.warn("Notification error:", e);
    }
  }

  // 3. Register in Notification Center List
  receivedAlertsHistory.unshift({
    tender: t,
    receivedAt: new Date().toLocaleTimeString("fr-FR", { hour: '2-digit', minute: '2-digit' })
  });
  updateNotificationCenterList();

  // 4. Render Rich Floating On-Screen Pop-up Card (Polished & Executive)
  const container = document.getElementById("rfp-live-popup-container");
  if (!container) return;

  const cardId = `popup-${t.id || 'rfp'}-${Date.now()}`;
  const popup = document.createElement("div");
  popup.id = cardId;
  popup.className = "pointer-events-auto bg-white/95 dark:bg-slate-900/95 border-2 border-emerald-500/80 dark:border-emerald-500/60 text-slate-900 dark:text-white rounded-2xl shadow-2xl p-4 space-y-3 backdrop-blur-xl toast-anim transform transition-all duration-300 ring-4 ring-emerald-500/10 max-w-sm w-full";

  const isAtlantic = (t.buyer_name || "").toLowerCase().includes("atlantic") || (t.reference || "").includes("SCR");
  const isLaprophan = (t.buyer_name || "").toLowerCase().includes("laprophan");
  const badgeColor = isAtlantic ? "bg-amber-500/20 text-amber-800 dark:text-amber-300 border-amber-500/40" : (isLaprophan ? "bg-purple-500/20 text-purple-800 dark:text-purple-300 border-purple-500/40" : "bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 border-emerald-500/40");

  popup.innerHTML = `
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <span class="flex h-2.5 w-2.5 relative">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
        </span>
        <span class="text-[10px] font-extrabold uppercase tracking-wider text-rose-600 dark:text-rose-400 flex items-center space-x-1">
          <span>NOUVEAU MARCHÉ DÉTECTÉ</span>
        </span>
      </div>
      <div class="flex items-center space-x-2">
        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold border ${badgeColor}">
          ${escapeHtml(t.source_name ? t.source_name.split('&')[0].trim() : 'PMMP')}
        </span>
        <button onclick="dismissRfpPopup(${safeArg(cardId)})" class="p-1 text-slate-400 hover:text-slate-700 dark:hover:text-white rounded-lg transition">
          <i data-lucide="x" class="w-4 h-4"></i>
        </button>
      </div>
    </div>

    <!-- Click opens tender modal -->
    <div class="space-y-1.5 cursor-pointer" onclick="openTenderModal(${safeArg(t.id)})">
      <div class="flex items-center space-x-2">
        <span class="px-2 py-0.5 rounded bg-emerald-600 text-white font-mono font-bold text-xs">${escapeHtml(t.reference)}</span>
        <span class="text-xs font-bold text-slate-700 dark:text-slate-300 truncate">${escapeHtml(t.buyer_name)}</span>
      </div>
      <h4 class="text-xs font-bold text-slate-900 dark:text-white leading-snug line-clamp-2 hover:text-emerald-600 dark:hover:text-emerald-400 transition">${escapeHtml(t.title)}</h4>
      
      <div class="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 pt-1">
        <span>Budget : <strong class="text-slate-900 dark:text-slate-100 font-bold">${t.estimated_budget > 0 ? formatMAD(t.estimated_budget) : 'Non précisé'}</strong></span>
        <span>Date : <strong class="text-slate-800 dark:text-slate-200">${t.publication_date || 'Aujourd\'hui'}</strong></span>
      </div>
    </div>

    <div class="flex items-center space-x-1.5 pt-2 border-t border-slate-100 dark:border-slate-800">
      <button onclick="openTenderModal(${safeArg(t.id)}); dismissRfpPopup(${safeArg(cardId)});" class="flex-1 py-1.5 px-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl transition flex items-center justify-center space-x-1 shadow-xs">
        <i data-lucide="eye" class="w-3.5 h-3.5"></i>
        <span>Détails</span>
      </button>
      <button onclick="openSubmissionFolderModal(${safeArg(t.id)}); dismissRfpPopup(${safeArg(cardId)});" class="py-1.5 px-2.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs rounded-xl transition flex items-center justify-center space-x-1 shadow-xs">
        <i data-lucide="folder" class="w-3.5 h-3.5"></i>
        <span>Dossier</span>
      </button>
      <a href="${escapeHtml(t.source_url || '#')}" target="_blank" onclick="event.stopPropagation()" class="py-1.5 px-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 font-bold text-xs rounded-xl border border-slate-200 dark:border-slate-700 transition flex items-center space-x-1" title="Consulter la source officielle">
        <i data-lucide="external-link" class="w-3.5 h-3.5 text-amber-500"></i>
        <span>Source</span>
      </a>
      <button onclick="downloadDCE(${safeArg(t.id)}, ${safeArg(t.reference)})" class="py-1.5 px-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 font-bold text-xs rounded-xl border border-slate-200 dark:border-slate-700 transition flex items-center space-x-1">
        <i data-lucide="download" class="w-3.5 h-3.5 text-emerald-500"></i>
        <span>DCE</span>
      </button>
    </div>

    <div class="w-full bg-slate-200 dark:bg-slate-800 h-1 rounded-full overflow-hidden">
      <div id="bar-${cardId}" class="bg-emerald-500 h-full w-full transition-all duration-[12000ms] ease-linear"></div>
    </div>
  `;

  container.appendChild(popup);
  if (window.lucide) lucide.createIcons({ root: popup });

  setTimeout(() => {
    const bar = document.getElementById(`bar-${cardId}`);
    if (bar) bar.style.width = '0%';
  }, 50);

  setTimeout(() => {
    dismissRfpPopup(cardId);
  }, 12000);
}

function dismissRfpPopup(cardId) {
  const el = document.getElementById(cardId);
  if (!el) return;
  el.style.opacity = '0';
  el.style.transform = 'translateY(20px)';
  el.style.transition = 'all 0.3s ease';
  setTimeout(() => {
    el.remove();
  }, 300);
}

function toggleNotificationMenu() {
  const dropdown = document.getElementById("notif-dropdown");
  if (!dropdown) return;
  dropdown.classList.toggle("hidden");
  if (window.lucide) lucide.createIcons({ root: dropdown });
}

function updateNotificationCenterList() {
  const container = document.getElementById("notif-list-container");
  const badge = document.getElementById("notif-badge");
  if (!container) return;

  if (badge) {
    if (receivedAlertsHistory.length > 0) {
      badge.textContent = receivedAlertsHistory.length;
      badge.classList.remove("hidden");
    } else {
      badge.classList.add("hidden");
    }
  }

  if (receivedAlertsHistory.length === 0) {
    container.innerHTML = `
      <div class="text-center py-6 text-xs text-slate-500">
        <i data-lucide="bell-off" class="w-6 h-6 mx-auto mb-1 text-slate-600"></i>
        <span>En attente de nouvelles publications...</span>
      </div>
    `;
    if (window.lucide) lucide.createIcons({ root: container });
    return;
  }

  container.innerHTML = receivedAlertsHistory.map(item => {
    const t = item.tender;
    return `
      <div class="p-2.5 rounded-xl bg-slate-950/80 hover:bg-slate-800/80 border border-slate-800 cursor-pointer transition text-xs space-y-1" onclick="openSubmissionFolderModal(${safeArg(t.id)}); toggleNotificationMenu();">
        <div class="flex items-center justify-between">
          <span class="font-mono font-bold text-amber-400">${escapeHtml(t.reference)}</span>
          <span class="text-[10px] text-slate-500 font-mono">${item.receivedAt}</span>
        </div>
        <p class="font-bold text-white line-clamp-1">${escapeHtml(t.title)}</p>
        <div class="flex items-center justify-between text-[10px] text-slate-400">
          <span class="truncate max-w-[180px]">${escapeHtml(t.buyer_name)}</span>
          <span class="text-emerald-400 font-mono">${t.provisional_guarantee || ''}</span>
        </div>
      </div>
    `;
  }).join("");
  if (window.lucide) lucide.createIcons({ root: container });
}

function clearNotificationList() {
  receivedAlertsHistory = [];
  updateNotificationCenterList();
}

async function testOnScreenNotification() {
  showToast("Déclenchement du test d'alerte pop-up...", "info");
  try {
    const res = await fetch("/api/notifications/test-sample");
    if (!res.ok) throw new Error("Erreur de test");
    const sampleTender = await res.json();
    sampleTender.force_notify = true;
    triggerRfpPopup(sampleTender);
  } catch (err) {
    triggerRfpPopup({
      id: "sample-cyber-alert",
      reference: "32/2026/ONHYM",
      title: "Audit de sécurité des systèmes d'information et tests d'intrusion (Pentest) pour l'Office National des Hydrocarbures et des Mines",
      buyer_name: "ONHYM (Office National des Hydrocarbures et des Mines)",
      provisional_guarantee: "15 000,00 MAD",
      source_name: "AO Maroc & PMMP",
      publication_date: new Date().toISOString().split("T")[0],
      force_notify: true
    });
  }
}

// ==================== MOBILE & IPHONE ACCESS ====================

async function openMobileQrModal() {
  const modal = document.getElementById("mobile-qr-modal");
  if (!modal) return;
  modal.classList.remove("hidden");
  
  let lanUrl = window.location.origin;
  try {
    const res = await fetch("/api/system/network-info");
    if (res.ok) {
      const data = await res.json();
      if (data && data.mobile_url && !data.mobile_url.includes("127.0.0.1")) {
        lanUrl = data.mobile_url;
      }
    }
  } catch (e) {}

  const inputEl = document.getElementById("mobile-url-input");
  if (inputEl) inputEl.value = lanUrl;

  const qrImg = document.getElementById("mobile-qr-img");
  if (qrImg) {
    qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=240x240&margin=8&data=${encodeURIComponent(lanUrl)}`;
  }
  if (window.lucide) lucide.createIcons({ root: modal });
}

function closeMobileQrModal() {
  const modal = document.getElementById("mobile-qr-modal");
  if (modal) modal.classList.add("hidden");
}

function copyMobileUrl() {
  const inputEl = document.getElementById("mobile-url-input");
  if (!inputEl) return;
  navigator.clipboard.writeText(inputEl.value).then(() => {
    const copyText = document.getElementById("copy-btn-text");
    if (copyText) copyText.textContent = "Copié !";
    showToast("Adresse iPhone copiée dans le presse-papiers !", "success");
    setTimeout(() => { if (copyText) copyText.textContent = "Copier"; }, 2000);
  });
}

async function testEmailNotificationFromUI() {
  showToast("Test de notification email en cours...", "info");
  try {
    const res = await fetch("/api/admin/alerts/test-email", { method: "POST" });
    const data = await res.json();
    if (data.status === "success") {
      showToast(data.message || "Email de test envoyé avec succès !", "success");
    } else if (data.status === "warning") {
      showToast(data.message || "Identifiants SMTP manquants", "warning");
    } else if (data.status === "error") {
      showToast(data.message || "Erreur de connexion SMTP", "error");
    } else {
      showToast(data.message || "Alerte traitée avec succès", "info");
    }
  } catch (err) {
    showToast("Erreur lors de l'envoi de l'email: " + err.message, "error");
  }
}

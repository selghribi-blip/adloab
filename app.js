/* Adloab — a dependency-free, local-first demo dashboard.
 * The interface is intentionally limited to consented analytics and campaign planning.
 * It does not automate clicks, create fake visits, rotate proxies, or bypass platform controls.
 */

const iconPaths = {
  'layout-dashboard': '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  megaphone: '<path d="m3 11 18-5v12L3 14z"/><path d="M11.6 16.4 13 21H8l-1.6-6.1"/><path d="M21 10v4"/>',
  'chart-no-axes-combined': '<path d="M3 3v18h18"/><path d="m7 16 4-5 3 3 6-8"/><path d="M20 6h-4v4"/>',
  'wand-sparkles': '<path d="m15 4 5 5"/><path d="m13 6 5 5"/><path d="m4 20 9-9"/><path d="m4 4 .6 1.8L6.5 6.5 4.6 7.2 4 9l-.6-1.8-1.9-.7 1.9-.7z"/><path d="m19 16 .5 1.5L21 18l-1.5.5L19 20l-.5-1.5L17 18l1.5-.5z"/>',
  'plug-zap': '<path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/><path d="M5 8h14"/><path d="M5 8v2a7 7 0 0 0 14 0V8"/><path d="m17 16 2-3h-3l2-3"/>',
  'shield-check': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
  'settings-2': '<path d="M20 7h-9"/><path d="M14 17H4"/><circle cx="17" cy="7" r="3"/><circle cx="7" cy="17" r="3"/>',
  'more-horizontal': '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
  'chevron-down': '<path d="m6 9 6 6 6-6"/>',
  'chevron-left': '<path d="m15 18-6-6 6-6"/>',
  'arrow-left': '<path d="m19 12H5"/><path d="m12 19-7-7 7-7"/>',
  'arrow-right': '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
  menu: '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
  'calendar-days': '<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/><path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01"/>',
  bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
  'check-check': '<path d="m1.5 12 5 5L18 5"/><path d="m8 12 5 5L23 7"/>',
  sparkles: '<path d="m12 3-1.3 4.2L7 8.5l3.7 1.3L12 14l1.3-4.2L17 8.5l-3.7-1.3z"/><path d="m19 14-.7 2.3L16 17l2.3.7L19 20l.7-2.3L22 17l-2.3-.7z"/><path d="m5 3-.5 1.5L3 5l1.5.5L5 7l.5-1.5L7 5l-1.5-.5z"/>',
  'triangle-alert': '<path d="m10.3 3.7-8 14A2 2 0 0 0 4 20.7h16a2 2 0 0 0 1.7-3l-8-14a2 2 0 0 0-3.4 0z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  download: '<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/>',
  activity: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  banknote: '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M7 8h.01M17 16h.01"/>',
  'arrow-up-right': '<path d="M7 17 17 7"/><path d="M7 7h10v10"/>',
  'arrow-down-right': '<path d="m7 7 10 10"/><path d="M17 7v10H7"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  pause: '<path d="M7 5v14M17 5v14"/>',
  play: '<path d="m8 5 11 7-11 7z"/>',
  'external-link': '<path d="M14 3h7v7"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  'more-vertical': '<circle cx="12" cy="5" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="12" cy="19" r="1"/>',
  'sliders-horizontal': '<line x1="4" x2="14" y1="6" y2="6"/><line x1="16" x2="20" y1="6" y2="6"/><line x1="4" x2="8" y1="12" y2="12"/><line x1="10" x2="20" y1="12" y2="12"/><line x1="4" x2="13" y1="18" y2="18"/><line x1="15" x2="20" y1="18" y2="18"/><circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="14" cy="18" r="2"/>',
  filter: '<path d="M4 5h16M7 12h10M10 19h4"/>',
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  'link-2': '<path d="M10 13a5 5 0 0 0 7.5.5l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1"/><path d="M14 11a5 5 0 0 0-7.5-.5l-2 2a5 5 0 0 0 7.1 7.1l1.1-1.1"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
  'scan-search': '<path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2"/><circle cx="11" cy="11" r="4"/><path d="m14 14 3 3"/>',
  'file-text': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>',
  database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  'refresh-cw': '<path d="M3 12a9 9 0 0 1 15.2-6.5L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15.2 6.5L3 16"/><path d="M3 21v-5h5"/>',
  rocket: '<path d="M4.5 16.5c-1.5 1.2-2 3.5-2 3.5s2.3-.5 3.5-2c.7-.8.7-2.1-.1-2.3-.4-.1-.9.2-1.4.8z"/><path d="M12 15 9 12c.5-3.5 2.3-6.4 6.5-8.5A2 2 0 0 1 18 5.5C16 10.7 13 12.5 12 15z"/><path d="m9 12-3 .5L4 10l4-1M12 15l-.5 3L14 20l1-4"/><circle cx="15.5" cy="8.5" r="1"/>',
  zap: '<path d="M13 2 3 14h8l-1 8 10-12h-8z"/>',
  'mouse-pointer-click': '<path d="m9 9 5.5 5.5M4 4l4 1-1 4M13.5 20.5l-1.3-4.2 4.2 1.3-2.9 2.9z"/><path d="M4 4 15.5 15.5"/><path d="M19 5h.01M20 10h.01M15 3h.01"/>',
  globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
  'share-2': '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/>',
  'lock-keyhole': '<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/>',
  'badge-check': '<path d="m12 3 2 2 3-.2.8 2.9 2.5 1.6-1.6 2.5.2 3-2.9.8-1.6 2.5-2.5-1.6-3 .2-.8-2.9-2.5-1.6 1.6-2.5-.2-3 2.9-.8z"/><path d="m9 12 2 2 4-4"/>',
  'key-round': '<circle cx="7.5" cy="15.5" r="3.5"/><path d="m10 13 10-10M15 8l2 2M18 5l2 2"/>',
  upload: '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M5 20h14"/>',
  'trash-2': '<path d="M3 6h18M8 6V4h8v2M19 6l-1 15H6L5 6M10 11v6M14 11v6"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42"/>',
  moon: '<path d="M21 12.8A8.5 8.5 0 1 1 11.2 3 6.5 6.5 0 0 0 21 12.8z"/>',
  'user-round': '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  'clipboard-check': '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2h6v2M8 13l2 2 5-5"/>',
  'building-2': '<path d="M3 21h18M6 21V5l6-3 6 3v16M9 9h1M9 13h1M9 17h1M14 9h1M14 13h1M14 17h1"/>',
  save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8M7 3v5h8"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  github: '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3.2 0 6.5-1.6 6.5-7A5.4 5.4 0 0 0 19 3.7 5 5 0 0 0 18.9.5S17.4 0 15 1.7a13.4 13.4 0 0 0-6 0C6.6 0 5.1.5 5.1.5A5 5 0 0 0 5 3.7 5.4 5.4 0 0 0 3.5 7.5c0 5.4 3.3 7 6.5 7A4.8 4.8 0 0 0 9 18v4"/><path d="M9 18c-4.5 2-5-2-7-2"/>',
  cloud: '<path d="M17.5 19H9a7 7 0 1 1 6.7-9H17a5 5 0 0 1 .5 9z"/>',
  circle: '<circle cx="12" cy="12" r="9"/>'
};

function icon(name, size = 17) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${iconPaths[name] || iconPaths.circle}</svg>`;
}

function hydrateIcons(root = document) {
  root.querySelectorAll('[data-icon]').forEach((node) => {
    const name = node.getAttribute('data-icon');
    node.innerHTML = icon(name);
  });
}

const initialCampaigns = [
  { id: 'c-1', name: 'إطلاق موقع رِواق', objective: 'تحويلات · صفحة الهبوط', channel: 'بحث عضوي', channelKey: 'organic', status: 'active', budget: 4200, spent: 1680, conversions: 284, rate: 5.8, updated: 'منذ 14 دقيقة', color: 'lime' },
  { id: 'c-2', name: 'محتوى دليل البداية', objective: 'وعي · مقال تعليمي', channel: 'اجتماعي', channelKey: 'social', status: 'active', budget: 2800, spent: 910, conversions: 176, rate: 4.3, updated: 'منذ 37 دقيقة', color: 'purple' },
  { id: 'c-3', name: 'رسالة العودة الذكية', objective: 'احتفاظ · بريد إلكتروني', channel: 'بريد إلكتروني', channelKey: 'email', status: 'paused', budget: 1600, spent: 1240, conversions: 94, rate: 7.1, updated: 'أمس', color: 'orange' },
  { id: 'c-4', name: 'شراكة مجتمع المصممين', objective: 'إحالات · رابط مشترك', channel: 'إحالات', channelKey: 'referral', status: 'review', budget: 3500, spent: 0, conversions: 0, rate: 0, updated: 'منذ يومين', color: 'blue' },
  { id: 'c-5', name: 'صفحة الأسعار الجديدة', objective: 'تحويلات · تجربة A/B', channel: 'مباشر', channelKey: 'direct', status: 'active', budget: 1900, spent: 810, conversions: 129, rate: 3.9, updated: 'منذ 4 ساعات', color: 'blue' },
  { id: 'c-6', name: 'أسبوع المعرفة المفتوح', objective: 'وعي · تسجيلات', channel: 'اجتماعي', channelKey: 'social', status: 'draft', budget: 2400, spent: 0, conversions: 0, rate: 0, updated: 'منذ 3 أيام', color: 'purple' }
];

const defaultState = {
  view: 'overview',
  range: '7d',
  chartMode: 'visits',
  theme: 'light',
  campaignFilter: 'all',
  campaignQuery: '',
  workspaceName: 'مساحة مدار',
  campaigns: initialCampaigns,
  connected: { ga4: true, matomo: false, posthog: true, search: true },
  checklist: { consent: true, retention: true, utm: true, access: false },
  settings: { weeklyDigest: true, anomalyAlerts: true, darkMode: false }
};

let state = loadState();

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem('adloab-state') || '{}');
    return {
      ...defaultState,
      ...saved,
      campaigns: Array.isArray(saved.campaigns) && saved.campaigns.length ? saved.campaigns : initialCampaigns,
      connected: { ...defaultState.connected, ...(saved.connected || {}) },
      checklist: { ...defaultState.checklist, ...(saved.checklist || {}) },
      settings: { ...defaultState.settings, ...(saved.settings || {}) }
    };
  } catch {
    return { ...defaultState, campaigns: [...initialCampaigns] };
  }
}

function saveState() {
  try {
    localStorage.setItem('adloab-state', JSON.stringify({
      ...state,
      view: undefined
    }));
  } catch {
    // The demo remains usable when storage is disabled.
  }
}

const pageMeta = {
  overview: { title: 'نظرة عامة', eyebrow: 'ملخص مساحة مدار' },
  campaigns: { title: 'الحملات', eyebrow: 'إدارة النمو' },
  analytics: { title: 'التحليلات', eyebrow: 'قراءة الأداء' },
  tools: { title: 'أدوات النمو', eyebrow: 'أدوات عملية' },
  sources: { title: 'مصادر البيانات', eyebrow: 'اتصالات آمنة' },
  compliance: { title: 'الثقة والامتثال', eyebrow: 'جودة الإشارات' },
  settings: { title: 'الإعدادات', eyebrow: 'مساحة العمل' }
};

const rangeLabels = { '7d': 'آخر 7 أيام', '30d': 'آخر 30 يوماً', '90d': 'آخر 90 يوماً' };

const chartSets = {
  '7d': {
    labels: ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة'],
    visits: [42, 54, 49, 69, 62, 76, 88],
    conversions: [24, 31, 28, 38, 35, 47, 52]
  },
  '30d': {
    labels: ['1 مايو', '5 مايو', '10 مايو', '15 مايو', '20 مايو', '25 مايو', '30 مايو'],
    visits: [36, 49, 44, 58, 53, 73, 89],
    conversions: [19, 24, 29, 31, 38, 43, 56]
  },
  '90d': {
    labels: ['مارس', 'منتصف مارس', 'أبريل', 'منتصف أبريل', 'مايو', 'منتصف مايو', 'اليوم'],
    visits: [30, 38, 50, 47, 62, 71, 88],
    conversions: [17, 21, 27, 33, 35, 45, 53]
  }
};

const statusLabels = { active: 'نشطة', paused: 'متوقفة مؤقتاً', draft: 'مسودة', review: 'قيد المراجعة' };
const channelLabels = { organic: 'بحث عضوي', social: 'اجتماعي', email: 'بريد إلكتروني', referral: 'إحالات', direct: 'مباشر' };

const integrations = [
  { id: 'ga4', name: 'Google Analytics 4', short: 'GA4', description: 'استيراد الجلسات والأحداث والتحويلات مع الحفاظ على مصدر الحقيقة في حسابك.', icon: 'chart-no-axes-combined', tone: 'blue', mode: 'معرّف قياس' },
  { id: 'search', name: 'Search Console', short: 'GSC', description: 'ربط الظهور والنقرات والكلمات المفتاحية لقياس النمو العضوي الحقيقي.', icon: 'search', tone: 'green', mode: 'خاصية الموقع' },
  { id: 'posthog', name: 'PostHog', short: 'PH', description: 'تحليل مسارات المنتج وتجارب الاستخدام من أحداث يرسلها تطبيقك.', icon: 'activity', tone: 'purple', mode: 'Project API' },
  { id: 'matomo', name: 'Matomo', short: 'MT', description: 'خيار تحليلات مستضاف ذاتياً لمن يريد ملكية أكبر للبيانات.', icon: 'database', tone: 'orange', mode: 'رابط الموقع' }
];

function esc(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-US').format(Number(value) || 0);
}

function formatCurrency(value) {
  return `${formatNumber(value)} ر.س`;
}

function statusBadge(status) {
  return `<span class="status-badge status-${status}">${statusLabels[status] || status}</span>`;
}

function channelBadge(key) {
  return `<span class="channel-badge channel-${key}">${channelLabels[key] || key}</span>`;
}

function chartPoints(values, width = 760, height = 205) {
  const min = 0;
  const max = 100;
  const top = 9;
  const bottom = 187;
  return values.map((value, index) => {
    const x = values.length === 1 ? width / 2 : (index * width) / (values.length - 1);
    const y = bottom - ((value - min) / (max - min)) * (bottom - top);
    return [Number(x.toFixed(2)), Number(y.toFixed(2))];
  });
}

function linePath(points) {
  return points.map(([x, y], index) => `${index ? 'L' : 'M'} ${x} ${y}`).join(' ');
}

function areaPath(points, width = 760, height = 205) {
  return `${linePath(points)} L ${width} ${height - 17} L 0 ${height - 17} Z`;
}

function chartMarkup() {
  const data = chartSets[state.range];
  const visitPoints = chartPoints(data.visits);
  const conversionPoints = chartPoints(data.conversions);
  const yLines = [26, 66, 106, 146, 186];
  const visitsArea = areaPath(visitPoints);
  const conversionArea = areaPath(conversionPoints);
  return `
    <div class="chart-legend">
      <span class="legend-item"><i class="lime"></i> الزيارات المؤهلة</span>
      <span class="legend-item"><i class="purple"></i> التحويلات</span>
    </div>
    <figure class="chart-figure" aria-label="مخطط الزيارات والتحويلات">
      <div class="chart-y-labels"><span>100k</span><span>75k</span><span>50k</span><span>25k</span><span>0</span></div>
      <div class="chart-svg-wrap">
        <svg viewBox="0 0 760 205" preserveAspectRatio="none" role="img" aria-label="أداء آخر فترة">
          <defs>
            <linearGradient id="area-lime" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="#b9ed73" stop-opacity="0.26"/>
              <stop offset="100%" stop-color="#b9ed73" stop-opacity="0"/>
            </linearGradient>
            <linearGradient id="area-purple" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="#887cf0" stop-opacity="0.14"/>
              <stop offset="100%" stop-color="#887cf0" stop-opacity="0"/>
            </linearGradient>
          </defs>
          ${yLines.map((y) => `<line class="chart-grid-line" x1="0" x2="760" y1="${y}" y2="${y}"/>`).join('')}
          <path d="${conversionArea}" fill="url(#area-purple)"/>
          <path d="${visitsArea}" fill="url(#area-lime)"/>
          <path d="${linePath(conversionPoints)}" fill="none" stroke="#8376ef" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="${linePath(visitPoints)}" fill="none" stroke="#9cda4f" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          ${visitPoints.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="3.4" fill="#fff" stroke="#9cda4f" stroke-width="2"/>`).join('')}
          <circle cx="${visitPoints.at(-1)[0]}" cy="${visitPoints.at(-1)[1]}" r="6.5" fill="rgba(156,218,79,.17)"/>
          <circle cx="${visitPoints.at(-1)[0]}" cy="${visitPoints.at(-1)[1]}" r="3.4" fill="#fff" stroke="#9cda4f" stroke-width="2"/>
        </svg>
      </div>
      <div class="chart-labels">${data.labels.map((label) => `<span>${esc(label)}</span>`).join('')}</div>
    </figure>`;
}

function chartCard(extraClass = '') {
  return `
    <section class="card chart-card ${extraClass}">
      <div class="card-heading">
        <div>
          <h2>حركة الزيارات</h2>
          <p>قراءة موحّدة لمصادر الزيارات والتحويلات</p>
        </div>
        <div class="chart-tabs" role="tablist" aria-label="الفترة الزمنية">
          ${Object.entries(rangeLabels).map(([key, label]) => `<button class="chart-tab ${state.range === key ? 'active' : ''}" type="button" data-range="${key}">${key === '7d' ? 'أسبوع' : key === '30d' ? 'شهر' : 'ربع سنة'}</button>`).join('')}
        </div>
      </div>
      ${chartMarkup()}
    </section>`;
}

function sourceRows() {
  const rows = [
    { label: 'بحث عضوي', detail: 'Search Console', value: '46.2K', share: 76, tone: 'green', icon: 'search' },
    { label: 'اجتماعي', detail: 'Instagram · LinkedIn', value: '31.8K', share: 57, tone: 'blue', icon: 'share-2' },
    { label: 'مباشر', detail: 'روابط محفوظة', value: '24.6K', share: 44, tone: 'purple', icon: 'link-2' },
    { label: 'إحالات', detail: 'شركاء موثوقون', value: '12.1K', share: 29, tone: 'orange', icon: 'users' }
  ];
  return rows.map((row) => `
    <div class="source-row">
      <div class="source-meta">
        <span class="source-meta-icon ${row.tone}">${icon(row.icon, 14)}</span>
        <span class="source-meta-copy"><strong>${row.label}</strong><small>${row.detail}</small></span>
      </div>
      <strong class="source-number">${row.value}</strong>
      <div class="source-bar"><span class="${row.tone}" style="width:${row.share}%"></span></div>
    </div>`).join('');
}

function campaignTableRows(campaigns, withAction = true) {
  if (!campaigns.length) {
    return `<tr><td colspan="${withAction ? 7 : 6}"><div class="no-results">لا توجد حملات تطابق هذا البحث.</div></td></tr>`;
  }
  return campaigns.map((campaign) => `
    <tr>
      <td>
        <div class="campaign-name">
          <span class="campaign-color ${esc(campaign.color)}"></span>
          <span class="campaign-name-copy"><strong>${esc(campaign.name)}</strong><small>${esc(campaign.objective)}</small></span>
        </div>
      </td>
      <td>${channelBadge(campaign.channelKey)}</td>
      <td>${statusBadge(campaign.status)}</td>
      <td class="metric-number">${formatCurrency(campaign.spent)}</td>
      <td class="metric-number">${formatNumber(campaign.conversions)}</td>
      <td class="metric-positive">${campaign.rate ? `${campaign.rate}%` : '—'}</td>
      ${withAction ? `<td><div class="table-actions"><button type="button" class="table-menu-button" data-action="toggle-campaign" data-id="${esc(campaign.id)}" aria-label="${campaign.status === 'active' ? 'إيقاف الحملة' : 'تشغيل الحملة'}">${icon(campaign.status === 'active' ? 'pause' : 'play', 15)}</button><button type="button" class="table-menu-button" data-action="campaign-menu" data-id="${esc(campaign.id)}" aria-label="خيارات الحملة">${icon('more-vertical', 15)}</button></div></td>` : ''}
    </tr>`).join('');
}

function overviewView() {
  const kpis = [
    { label: 'الزوار المؤهلون', value: '128.4K', change: '+12.8%', note: 'مقارنة بالفترة السابقة', icon: 'users', tone: 'lime' },
    { label: 'معدل التحويل', value: '4.82%', change: '+0.64%', note: 'تحسن مستمر', icon: 'target', tone: 'purple' },
    { label: 'قيمة التحويلات', value: '86.2K', unit: 'ر.س', change: '+18.4%', note: 'منسوب إلى الحملات', icon: 'banknote', tone: 'orange' },
    { label: 'تكلفة الاكتساب', value: '18.60', unit: 'ر.س', change: '-8.2%', note: 'أقل من الشهر الماضي', icon: 'activity', tone: 'blue', down: true }
  ];
  const recent = state.campaigns.slice(0, 4);
  return `
    <div class="overview-hero">
      <div class="hero-copy">
        <div class="hero-kicker"><span></span> صباح الخير، سارة</div>
        <h1>كل إشارة نمو في مكانها الصحيح.</h1>
        <p>تابعي أداء قنواتك، افهمي جودة الزيارات، واتخذي قرارك التالي بثقة — بدون ضوضاء أو أرقام وهمية.</p>
      </div>
      <div class="hero-side">
        <div class="hero-health"><span class="hero-health-icon">${icon('shield-check', 15)}</span><span>مؤشر الثقة</span><strong>92</strong></div>
        <div class="hero-buttons"><button type="button" class="secondary-button" data-action="download-report">${icon('download', 14)} تصدير التقرير</button><button type="button" class="primary-button" data-action="new-campaign">${icon('plus', 14)} حملة جديدة</button></div>
      </div>
    </div>
    <div class="kpi-grid">
      ${kpis.map((kpi) => `<article class="kpi-card"><div class="kpi-topline"><span>${kpi.label}</span><span class="kpi-icon ${kpi.tone}">${icon(kpi.icon, 15)}</span></div><div class="kpi-value">${kpi.value}<small>${kpi.unit || ''}</small></div><div class="kpi-footer"><span class="kpi-change ${kpi.down ? 'down' : ''}">${icon(kpi.down ? 'arrow-down-right' : 'arrow-up-right', 11)} ${kpi.change}</span><span>${kpi.note}</span></div></article>`).join('')}
    </div>
    <div class="dashboard-grid">
      ${chartCard()}
      <section class="card source-card">
        <div class="card-heading"><div><h2>مزيج القنوات</h2><p>نسبة الزيارات المؤهلة حسب المصدر</p></div><button type="button" class="card-link" data-view="analytics">التفاصيل ${icon('arrow-left', 12)}</button></div>
        <div class="source-list">${sourceRows()}</div>
      </section>
    </div>
    <div class="bottom-grid">
      <section class="card table-card">
        <div class="card-heading"><div><h2>الحملات النشطة</h2><p>آخر تغيير ومؤشر التحويل لكل حملة</p></div><button type="button" class="card-link" data-view="campaigns">عرض الكل ${icon('arrow-left', 12)}</button></div>
        <div class="table-wrap"><table><thead><tr><th>الحملة</th><th>القناة</th><th>الحالة</th><th>الإنفاق</th><th>التحويلات</th><th>المعدل</th><th></th></tr></thead><tbody>${campaignTableRows(recent)}</tbody></table></div>
      </section>
      <section class="card insight-card">
        <div class="card-heading"><div><h2>إشارات تستحق الانتباه</h2><p>اقتراحات مبنية على بيانات مساحتك</p></div><span class="section-icon" style="width:28px;height:28px;flex-basis:28px">${icon('sparkles', 14)}</span></div>
        <div class="insight-list">
          <div class="insight-item"><span class="insight-icon lime">${icon('rocket', 14)}</span><div class="insight-copy"><strong>بحث عضوي يتقدم</strong><p>زادت التحويلات من صفحات الدليل بنسبة 21% خلال 7 أيام.</p></div></div>
          <div class="insight-item"><span class="insight-icon purple">${icon('zap', 14)}</span><div class="insight-copy"><strong>فرصة تحسين سريعة</strong><p>الحملة الاجتماعية لديها زيارات جيدة، جرّبي تحسين رسالة الدعوة.</p></div></div>
          <div class="insight-item"><span class="insight-icon orange">${icon('triangle-alert', 14)}</span><div class="insight-copy"><strong>راجعي رابطاً واحداً</strong><p>وسم المحتوى ناقص في رابط مشاركة واحد قبل نشره.</p></div></div>
        </div>
      </section>
    </div>`;
}

function getFilteredCampaigns() {
  const query = state.campaignQuery.trim().toLowerCase();
  return state.campaigns.filter((campaign) => {
    const matchesFilter = state.campaignFilter === 'all' || campaign.status === state.campaignFilter;
    const matchesQuery = !query || `${campaign.name} ${campaign.objective} ${campaign.channel}`.toLowerCase().includes(query);
    return matchesFilter && matchesQuery;
  });
}

function campaignsView() {
  const activeCount = state.campaigns.filter((item) => item.status === 'active').length;
  const totalConversions = state.campaigns.reduce((sum, item) => sum + item.conversions, 0);
  return `
    <div class="page-heading"><div class="page-heading-copy"><div class="eyebrow"><span class="eyebrow-dot"></span>${pageMeta.campaigns.eyebrow}</div><h1>الحملات</h1><p>خططي، راقبي، وحسّني الحملات التي تقود نمواً حقيقياً لمساحتك.</p></div><div class="page-actions"><button type="button" class="secondary-button" data-action="download-report">${icon('download', 14)} تصدير CSV</button><button type="button" class="primary-button" data-action="new-campaign">${icon('plus', 14)} إنشاء حملة</button></div></div>
    <div class="stats-strip"><div class="stat-tile"><small>إجمالي الحملات</small><strong>${state.campaigns.length}</strong><span>+2 هذا الشهر</span></div><div class="stat-tile"><small>حملات نشطة</small><strong>${activeCount}</strong><span>تعمل الآن</span></div><div class="stat-tile"><small>التحويلات المسندة</small><strong>${formatNumber(totalConversions)}</strong><span>+14.6%</span></div><div class="stat-tile"><small>الإنفاق المخطط</small><strong>${formatNumber(state.campaigns.reduce((sum, item) => sum + item.budget, 0))}</strong><span>ر.س · هذا الشهر</span></div></div>
    <div class="toolbar-card"><div class="toolbar-left"><div class="search-box">${icon('search', 14)}<input id="campaign-search" type="search" placeholder="ابحثي باسم الحملة..." value="${esc(state.campaignQuery)}" /></div></div><div class="toolbar-right"><div class="filter-pills"><button type="button" class="filter-pill ${state.campaignFilter === 'all' ? 'active' : ''}" data-filter="all">الكل</button><button type="button" class="filter-pill ${state.campaignFilter === 'active' ? 'active' : ''}" data-filter="active">نشطة</button><button type="button" class="filter-pill ${state.campaignFilter === 'paused' ? 'active' : ''}" data-filter="paused">متوقفة</button><button type="button" class="filter-pill ${state.campaignFilter === 'draft' ? 'active' : ''}" data-filter="draft">مسودات</button></div><button type="button" class="icon-button" data-action="filters" aria-label="فلاتر إضافية">${icon('sliders-horizontal', 16)}</button></div></div>
    <section class="card full-table-card"><div class="card-heading"><div><h2>كل الحملات</h2><p>بيانات تجريبية محفوظة محلياً في هذا المتصفح.</p></div><span class="channel-badge channel-organic">آخر مزامنة منذ 5 دقائق</span></div><div class="table-wrap"><table><thead><tr><th>الحملة</th><th>القناة</th><th>الحالة</th><th>الإنفاق</th><th>التحويلات</th><th>المعدل</th><th>إجراء</th></tr></thead><tbody id="campaigns-body">${campaignTableRows(getFilteredCampaigns())}</tbody></table></div></section>`;
}

function analyticsView() {
  return `
    <div class="page-heading"><div class="page-heading-copy"><div class="eyebrow"><span class="eyebrow-dot"></span>${pageMeta.analytics.eyebrow}</div><h1>التحليلات</h1><p>افهمي المسار من أول زيارة إلى التحويل، مع فصل واضح بين البيانات المؤكدة والتقديرات.</p></div><div class="page-actions"><button type="button" class="secondary-button" data-action="download-report">${icon('download', 14)} تنزيل التقرير</button><button type="button" class="primary-button" data-action="connect-source">${icon('plug-zap', 14)} إضافة مصدر</button></div></div>
    <div class="stats-strip"><div class="stat-tile"><small>الجلسات</small><strong>128.4K</strong><span>+12.8% عن السابق</span></div><div class="stat-tile"><small>جلسات متفاعلة</small><strong>84.7K</strong><span>66.0% من الجلسات</span></div><div class="stat-tile"><small>التحويلات</small><strong>6,182</strong><span>+18.2% عن السابق</span></div><div class="stat-tile"><small>قيمة الجلسة</small><strong>0.67</strong><span>ر.س · متوسط</span></div></div>
    <div class="analytics-grid">${chartCard('analytics-chart-card')}<section class="card section-card" style="margin:0"><div class="card-heading"><div><h2>مسار التحويل</h2><p>نسبة الانتقال بين الخطوات الأساسية</p></div><span class="section-icon green" style="width:28px;height:28px;flex-basis:28px">${icon('target', 14)}</span></div><div class="funnel-list"><div class="funnel-row"><label>زيارة</label><div class="funnel-track"><span style="width:100%;background:#9cda4f"></span></div><strong>128.4K</strong></div><div class="funnel-row"><label>تفاعل</label><div class="funnel-track"><span style="width:66%;background:#7abbe9"></span></div><strong>84.7K</strong></div><div class="funnel-row"><label>بدء الإجراء</label><div class="funnel-track"><span style="width:21%;background:#9b90ef"></span></div><strong>27.1K</strong></div><div class="funnel-row"><label>تحويل</label><div class="funnel-track"><span style="width:8%;background:#efa66a"></span></div><strong>6.2K</strong></div></div><div class="tool-note">${icon('info', 14)} النسب معروضة من أحداث موافق عليها، وليست تخميناً للزيارات.</div></section></div>
    <section class="card event-table-card"><div class="card-heading"><div><h2>الأحداث الأكثر تأثيراً</h2><p>أحداث تطبيقية تم جمعها من المصادر المتصلة</p></div><button type="button" class="card-link" data-action="export-events">تصدير الأحداث ${icon('arrow-left', 12)}</button></div><div class="table-wrap"><table><thead><tr><th>الحدث</th><th>المصدر</th><th>الإجمالي</th><th>المستخدمون الفريدون</th><th>تغير الفترة</th><th>الحالة</th></tr></thead><tbody><tr><td><span class="event-name"><i></i>sign_up_completed</span></td><td>GA4 · تطبيق الويب</td><td class="metric-number">4,291</td><td class="metric-number">3,988</td><td class="metric-positive">+22.4%</td><td>${statusBadge('active')}</td></tr><tr><td><span class="event-name"><i style="background:#8376ef"></i>pricing_viewed</span></td><td>PostHog · المنتج</td><td class="metric-number">18,640</td><td class="metric-number">14,212</td><td class="metric-positive">+9.7%</td><td>${statusBadge('active')}</td></tr><tr><td><span class="event-name"><i style="background:#f4a35d"></i>guide_downloaded</span></td><td>GA4 · المحتوى</td><td class="metric-number">9,872</td><td class="metric-number">7,101</td><td class="metric-positive">+16.1%</td><td>${statusBadge('review')}</td></tr></tbody></table></div></section>`;
}

function toolsView() {
  return `
    <div class="page-heading"><div class="page-heading-copy"><div class="eyebrow"><span class="eyebrow-dot"></span>${pageMeta.tools.eyebrow}</div><h1>أدوات النمو</h1><p>اختصري الأعمال اليومية التي تساعدك على قراءة الحملات، تنظيم الروابط، ومراجعة الجودة.</p></div><div class="page-actions"><button type="button" class="secondary-button" data-action="run-audit">${icon('scan-search', 14)} فحص المساحة</button></div></div>
    <div class="growth-tools-grid">
      <section class="tool-card"><div class="tool-card-heading"><span class="tool-icon">${icon('link-2', 17)}</span><div><h2>منشئ UTM</h2><p>وسوم قابلة للنسخ واللصق بدون أخطاء شائعة.</p></div></div><form id="utm-form"><div class="form-grid"><div class="form-field full"><label for="utm-url">الرابط الأساسي</label><input class="input-control" id="utm-url" type="url" value="https://madar.sa/launch" placeholder="https://example.com/page" required /></div><div class="form-field"><label for="utm-source">المصدر <small>(مطلوب)</small></label><input class="input-control" id="utm-source" value="linkedin" placeholder="linkedin" required /></div><div class="form-field"><label for="utm-medium">الوسيط <small>(مطلوب)</small></label><input class="input-control" id="utm-medium" value="organic-social" placeholder="social" required /></div><div class="form-field"><label for="utm-campaign">اسم الحملة</label><input class="input-control" id="utm-campaign" value="launch-2026" placeholder="spring-launch" /></div><div class="form-field"><label for="utm-content">محتوى الرابط</label><input class="input-control" id="utm-content" value="hero-button" placeholder="hero-button" /></div></div><div class="utm-preview"><div class="utm-preview-copy"><small>الرابط الناتج</small><code id="utm-preview">https://madar.sa/launch?utm_source=linkedin&amp;utm_medium=organic-social&amp;utm_campaign=launch-2026&amp;utm_content=hero-button</code></div><button type="button" class="copy-button" data-action="copy-utm">${icon('copy', 13)} نسخ</button></div><div class="form-actions"><button type="submit" class="primary-button">${icon('check', 14)} حفظ الوسم</button><span class="form-hint">سيتم حفظه محلياً في هذه النسخة التجريبية.</span></div></form></section>
      <section class="tool-card"><div class="tool-card-heading"><span class="tool-icon green">${icon('scan-search', 17)}</span><div><h2>مراجع الروابط</h2><p>تحققي من جاهزية الروابط قبل مشاركتها.</p></div></div><div class="checklist"><div class="check-row"><input type="checkbox" checked disabled /><label>الرابط يستخدم HTTPS<small>الاتصال المشفر يحمي الزائر وبياناته.</small></label></div><div class="check-row"><input type="checkbox" checked disabled /><label>وسوم المصدر والوسيط موجودة<small>يساعد ذلك على إسناد النتائج للقناة الصحيحة.</small></label></div><div class="check-row"><input type="checkbox" checked disabled /><label>صفحة الهبوط قابلة للوصول<small>اختبار تجربة المستخدم يتم بموافقة مالك الموقع فقط.</small></label></div></div><div class="tool-note">${icon('shield-check', 14)} لا يقوم هذا الفحص بفتح الصفحات آلياً أو محاكاة زيارات؛ هو فحص صياغة وتهيئة محلي.</div><div class="form-actions"><button type="button" class="secondary-button" data-action="run-audit">${icon('refresh-cw', 14)} تشغيل الفحص</button></div></section>
      <section class="tool-card full-width"><div class="tool-card-heading"><span class="tool-icon orange">${icon('upload', 17)}</span><div><h2>استيراد بيانات موثوقة</h2><p>ارفعي ملف CSV صادر من مصدر تملكينه لعرضه في التقارير. لا يتم إرسال الملف إلى أي خدمة في هذه النسخة.</p></div></div><label class="file-drop" for="csv-import" style="display:flex;align-items:center;justify-content:center;min-height:92px;padding:15px;color:#8b9aa8;font-size:10px;text-align:center;background:#fbfcfd;border:1px dashed #d5dfe7;border-radius:11px;cursor:pointer"><span>${icon('file-text', 18)}<br />اختاري ملف CSV من جهازك</span><input id="csv-import" type="file" accept=".csv,text/csv" hidden /></label><p class="form-hint" style="margin-top:9px">الحقول المقترحة: date, source, sessions, conversions. لا ترفعي بيانات شخصية غير ضرورية.</p></section>
    </div>`;
}

function sourcesView() {
  return `
    <div class="page-heading"><div class="page-heading-copy"><div class="eyebrow"><span class="eyebrow-dot"></span>${pageMeta.sources.eyebrow}</div><h1>مصادر البيانات</h1><p>اختاري مصادر تملكينها أو لديك إذن واضح لاستخدامها. كل اتصال له حالة يمكن مراجعتها.</p></div><div class="page-actions"><button type="button" class="primary-button" data-action="connect-source">${icon('plus', 14)} إضافة مصدر</button></div></div>
    <div class="policy-banner">${icon('lock-keyhole', 17)}<div><strong>البيانات تحت سيطرتك</strong><p>Adloab لا ينشئ حركة مرور ولا يضغط على إعلانات أو فيديوهات نيابة عنك. نقرأ أحداثاً حقيقية من مصادر متصلة بشكل مشروع ونحفظ حالة الاتصال محلياً في النسخة التجريبية.</p></div></div>
    <div class="integrations-grid">${integrations.map((integration) => { const connected = Boolean(state.connected[integration.id]); return `<article class="integration-card"><div class="integration-heading"><span class="integration-icon ${integration.tone}">${icon(integration.icon, 17)}</span><div><h2>${integration.name}</h2><p>${integration.short} · مصدر تحليلي</p></div><span class="integration-state ${connected ? '' : 'off'}">${connected ? 'متصل' : 'غير متصل'}</span></div><p class="integration-description">${integration.description}</p><div class="integration-footer"><small>${connected ? `آخر مزامنة ${integration.id === 'ga4' ? 'منذ 5 دقائق' : 'منذ 22 دقيقة'}` : 'جاهز للتهيئة'}</small><button type="button" class="${connected ? 'secondary-button' : 'primary-button'}" data-connect="${integration.id}">${connected ? 'إدارة الاتصال' : 'ربط المصدر'}</button></div></article>`; }).join('')}</div>`;
}

function complianceView() {
  const completed = Object.values(state.checklist).filter(Boolean).length;
  const score = Math.round((completed / 4) * 8 + 84);
  return `
    <div class="page-heading"><div class="page-heading-copy"><div class="eyebrow"><span class="eyebrow-dot"></span>${pageMeta.compliance.eyebrow}</div><h1>الثقة والامتثال</h1><p>جودة الزيارات تبدأ من مصدر واضح، موافقة صحيحة، وقياس لا يحاول خداع المنصة أو الزائر.</p></div><div class="page-actions"><button type="button" class="secondary-button" data-action="run-compliance">${icon('refresh-cw', 14)} إعادة الفحص</button></div></div>
    <div class="compliance-grid"><section class="compliance-card full-width"><div class="compliance-score"><div class="score-ring" style="background:conic-gradient(var(--lime-strong) 0deg ${Math.min(score, 100) * 3.6}deg, #edf1f3 ${Math.min(score, 100) * 3.6}deg 360deg)"><div class="score-ring-copy"><strong>${score}</strong><small>/ 100</small></div></div><div class="score-copy"><h3>مساحتك في وضع جيد</h3><p>المؤشر يعتمد على اكتمال إعدادات الموافقة، سياسة الاحتفاظ، صحة الوسوم، وتحديد صلاحيات الفريق. لا يعني ذلك اعتماداً قانونياً؛ راجعي متطلبات بلدك ومنصاتك دائماً.</p></div></div></section><section class="compliance-card"><div class="compliance-heading"><span class="section-icon green">${icon('clipboard-check', 17)}</span><div><h2>قائمة المراجعة</h2><p>أكملي البنود قبل إطلاق حملة جديدة.</p></div></div><div class="checklist"><div class="check-row"><input id="check-consent" data-check="consent" type="checkbox" ${state.checklist.consent ? 'checked' : ''}/><label for="check-consent">إشعار الموافقة مفعّل<small>احترمي اختيار الزائر ولا تجمعي ما لم يوافق عليه.</small></label></div><div class="check-row"><input id="check-retention" data-check="retention" type="checkbox" ${state.checklist.retention ? 'checked' : ''}/><label for="check-retention">سياسة الاحتفاظ محددة<small>حددي مدة الاحتفاظ وسبب كل حقل تحليلي.</small></label></div><div class="check-row"><input id="check-utm" data-check="utm" type="checkbox" ${state.checklist.utm ? 'checked' : ''}/><label for="check-utm">مخطط UTM موحّد<small>توحيد التسمية يجعل التقارير قابلة للمقارنة.</small></label></div><div class="check-row"><input id="check-access" data-check="access" type="checkbox" ${state.checklist.access ? 'checked' : ''}/><label for="check-access">مراجعة صلاحيات الفريق<small>لا تمنحي مفاتيح الإدارة إلا لمن يحتاجها.</small></label></div></div></section><section class="compliance-card"><div class="compliance-heading"><span class="section-icon">${icon('shield-check', 17)}</span><div><h2>ما الذي لا نفعله؟</h2><p>حدود واضحة لحماية حسابك وسمعة مشروعك.</p></div></div><div class="insight-list"><div class="insight-item"><span class="insight-icon lime">${icon('check', 14)}</span><div class="insight-copy"><strong>نحلل زيارات حقيقية</strong><p>من مصادر مرتبطة ومصرح بها، أو بيانات تستوردينها بنفسك.</p></div></div><div class="insight-item"><span class="insight-icon orange">${icon('triangle-alert', 14)}</span><div class="insight-copy"><strong>لا نضخم المشاهدات أو النقرات</strong><p>لا توجد شبكة زيارات آلية، حسابات وهمية، تدوير بروكسي، أو تجاوز CAPTCHA.</p></div></div><div class="insight-item"><span class="insight-icon purple">${icon('lock-keyhole', 14)}</span><div class="insight-copy"><strong>لا نطلب أسرار المصدر</strong><p>في الإنتاج ضعي مفاتيح OAuth والخدمات في الخادم، لا في المتصفح.</p></div></div></div></section></div>`;
}

function settingsView() {
  return `
    <div class="page-heading"><div class="page-heading-copy"><div class="eyebrow"><span class="eyebrow-dot"></span>${pageMeta.settings.eyebrow}</div><h1>الإعدادات</h1><p>تحكمي في تفضيلات المساحة، التنبيهات، والبيانات المخزنة في هذه النسخة.</p></div><div class="page-actions"><button type="button" class="primary-button" data-action="save-settings">${icon('save', 14)} حفظ التغييرات</button></div></div>
    <div class="settings-grid"><section class="settings-card"><div class="settings-heading"><span class="section-icon">${icon('user-round', 17)}</span><div><h2>الملف الشخصي</h2><p>معلوماتك داخل مساحة مدار</p></div></div><div class="settings-profile"><span class="large-avatar">س</span><div class="settings-profile-copy"><strong>سارة الحربي</strong><small>sara@madar.example · مالك المساحة</small></div><button type="button" class="ghost-button" data-action="profile-menu">تعديل</button></div><div class="form-grid"><div class="form-field full"><label for="workspace-name">اسم مساحة العمل</label><input class="input-control" id="workspace-name" value="${esc(state.workspaceName)}" /></div><div class="form-field"><label for="timezone">المنطقة الزمنية</label><select class="select-control" id="timezone"><option>الرياض (UTC+3)</option><option>دبي (UTC+4)</option><option>القاهرة (UTC+2)</option></select></div><div class="form-field"><label for="currency">العملة</label><select class="select-control" id="currency"><option>ريال سعودي (ر.س)</option><option>دولار أمريكي ($)</option><option>يورو (€)</option></select></div></div></section><section class="settings-card"><div class="settings-heading"><span class="section-icon green">${icon('bell', 17)}</span><div><h2>التنبيهات</h2><p>اختاري ما يستحق تنبيهاً في مساحة العمل.</p></div></div><div class="setting-row"><div class="setting-row-copy"><strong>ملخص أسبوعي</strong><small>أرسل ملخص الأداء إلى بريدك المرتبط.</small></div><label class="switch"><input type="checkbox" data-setting="weeklyDigest" ${state.settings.weeklyDigest ? 'checked' : ''}/><span class="switch-slider"></span></label></div><div class="setting-row"><div class="setting-row-copy"><strong>تنبيه الانحرافات</strong><small>نبّهيني عندما يتغير مصدر أو معدل بشكل غير معتاد.</small></div><label class="switch"><input type="checkbox" data-setting="anomalyAlerts" ${state.settings.anomalyAlerts ? 'checked' : ''}/><span class="switch-slider"></span></label></div><div class="setting-row"><div class="setting-row-copy"><strong>الوضع الليلي</strong><small>يحفظ تفضيل العرض في هذا المتصفح فقط.</small></div><label class="switch"><input type="checkbox" data-setting="darkMode" ${state.settings.darkMode ? 'checked' : ''}/><span class="switch-slider"></span></label></div></section><section class="settings-card full-width"><div class="settings-heading"><span class="section-icon orange">${icon('database', 17)}</span><div><h2>البيانات المحلية</h2><p>هذه النسخة التجريبية لا تستخدم خادماً؛ يمكنك تصدير أو حذف بيانات المتصفح.</p></div></div><div class="data-safety-card"><span class="data-safety-icon">${icon('lock-keyhole', 17)}</span><div style="flex:1"><strong>خصوصية افتراضية</strong><p>الحملات والتفضيلات محفوظة عبر localStorage على جهازك. قبل الإنتاج، انقلي التخزين إلى قاعدة بيانات مع صلاحيات وصول وسياسة احتفاظ واضحة.</p></div><button type="button" class="danger-button" data-action="delete-local-data">${icon('trash-2', 14)} حذف البيانات</button></div></section></div>`;
}

const renderers = { overview: overviewView, campaigns: campaignsView, analytics: analyticsView, tools: toolsView, sources: sourcesView, compliance: complianceView, settings: settingsView };

function updateHeader() {
  const title = document.getElementById('page-title');
  const label = document.getElementById('current-range-label');
  if (title) title.textContent = pageMeta[state.view]?.title || pageMeta.overview.title;
  if (label) label.textContent = rangeLabels[state.range];
  document.querySelectorAll('.nav-item[data-view]').forEach((item) => item.classList.toggle('active', item.dataset.view === state.view));
  document.body.classList.toggle('dark-theme', state.theme === 'dark' || state.settings.darkMode);
}

function renderApp(scroll = false) {
  const content = document.getElementById('app-content');
  content.innerHTML = (renderers[state.view] || overviewView)();
  updateHeader();
  hydrateIcons(content);
  if (scroll) window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateCampaignTableOnly() {
  const body = document.getElementById('campaigns-body');
  if (!body) return;
  body.innerHTML = campaignTableRows(getFilteredCampaigns());
  hydrateIcons(body);
}

function showToast(title, message, type = 'success') {
  const region = document.getElementById('toast-region');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span class="toast-icon">${icon(type === 'warning' ? 'triangle-alert' : 'check-check', 14)}</span><span class="toast-copy"><strong>${esc(title)}</strong><small>${esc(message)}</small></span>`;
  region.appendChild(toast);
  window.setTimeout(() => toast.remove(), 4200);
}

function closeFloatingMenus() {
  document.getElementById('date-menu').hidden = true;
  document.getElementById('notification-menu').hidden = true;
}

function closeModal() {
  document.getElementById('modal-root').innerHTML = '';
}

function openCampaignModal() {
  document.getElementById('modal-root').innerHTML = `
    <div class="modal-backdrop" data-close-modal="true"><div class="modal" role="dialog" aria-modal="true" aria-labelledby="campaign-modal-title"><div class="modal-header"><div><h2 id="campaign-modal-title">إنشاء حملة جديدة</h2><p>أضيفي الحملة إلى مساحة التخطيط. لن يتم إطلاق أي زيارات آلية.</p></div><button type="button" class="icon-button modal-close" data-action="close-modal" aria-label="إغلاق">${icon('x', 17)}</button></div><form id="campaign-form"><div class="form-grid"><div class="form-field full"><label for="campaign-name">اسم الحملة</label><input class="input-control" id="campaign-name" name="name" placeholder="مثال: إطلاق المنتج الصيفي" required /></div><div class="form-field full"><label for="campaign-url">رابط صفحة الهبوط</label><input class="input-control" id="campaign-url" name="url" type="url" placeholder="https://example.com/landing" required /><span class="form-hint">يجب أن يكون الرابط مملوكاً لك أو لديك إذن صريح لاستخدامه.</span></div><div class="form-field"><label for="campaign-channel">القناة</label><select class="select-control" id="campaign-channel" name="channel"><option value="organic">بحث عضوي</option><option value="social">اجتماعي</option><option value="email">بريد إلكتروني</option><option value="referral">إحالات</option><option value="direct">مباشر</option></select></div><div class="form-field"><label for="campaign-budget">الميزانية (ر.س)</label><input class="input-control" id="campaign-budget" name="budget" type="number" min="0" step="100" placeholder="2500" required /></div><div class="form-field"><label for="campaign-goal">هدف الحملة</label><select class="select-control" id="campaign-goal" name="goal"><option>تحويلات · صفحة الهبوط</option><option>وعي · محتوى تعليمي</option><option>احتفاظ · بريد إلكتروني</option><option>إحالات · رابط مشترك</option></select></div><div class="form-field"><label for="campaign-status">الحالة الأولية</label><select class="select-control" id="campaign-status" name="status"><option value="draft">مسودة</option><option value="review">قيد المراجعة</option><option value="active">نشطة</option></select></div></div><div class="modal-footer"><button type="button" class="secondary-button" data-action="close-modal">إلغاء</button><button type="submit" class="primary-button">${icon('plus', 14)} إضافة الحملة</button></div></form></div></div>`;
  document.getElementById('campaign-name')?.focus();
}

function openIntegrationModal(id = 'ga4') {
  const integration = integrations.find((item) => item.id === id) || integrations[0];
  document.getElementById('modal-root').innerHTML = `
    <div class="modal-backdrop" data-close-modal="true"><div class="modal" role="dialog" aria-modal="true" aria-labelledby="source-modal-title"><div class="modal-header"><div><h2 id="source-modal-title">${state.connected[integration.id] ? 'إدارة' : 'ربط'} ${esc(integration.name)}</h2><p>يتم تخزين الإعدادات محلياً هنا للعرض فقط. في الإنتاج استخدمي OAuth ومفاتيح الخادم.</p></div><button type="button" class="icon-button modal-close" data-action="close-modal" aria-label="إغلاق">${icon('x', 17)}</button></div><form id="integration-form"><input type="hidden" name="id" value="${esc(integration.id)}" /><div class="form-field"><label for="source-property">${esc(integration.mode)}</label><input class="input-control" id="source-property" name="property" placeholder="اكتبي المعرّف أو الرابط" value="${state.connected[integration.id] ? 'connected-demo' : ''}" required /><span class="form-hint">لا تضعي secret أو service role key في هذه الخانة أو في كود المتصفح.</span></div><div class="tool-note">${icon('shield-check', 14)} الموافقة والملكية مسؤوليتك. لا تربطي خصائص لا تملكينها.</div><div class="modal-footer"><button type="button" class="secondary-button" data-action="close-modal">إلغاء</button><button type="submit" class="primary-button">${icon('check', 14)} حفظ الاتصال</button></div></form></div></div>`;
  document.getElementById('source-property')?.focus();
}

function buildUtmUrl() {
  const rawUrl = document.getElementById('utm-url')?.value.trim() || '';
  const preview = document.getElementById('utm-preview');
  if (!preview) return '';
  try {
    const url = new URL(rawUrl);
    const fields = [
      ['utm_source', document.getElementById('utm-source')?.value.trim()],
      ['utm_medium', document.getElementById('utm-medium')?.value.trim()],
      ['utm_campaign', document.getElementById('utm-campaign')?.value.trim()],
      ['utm_content', document.getElementById('utm-content')?.value.trim()]
    ];
    fields.forEach(([key, value]) => {
      if (value) url.searchParams.set(key, value.toLowerCase().replace(/\s+/g, '-'));
    });
    const result = url.toString();
    preview.textContent = result;
    return result;
  } catch {
    preview.textContent = 'أدخلي رابطاً صحيحاً يبدأ بـ https://';
    return '';
  }
}

async function copyUtm() {
  const value = buildUtmUrl();
  if (!value) {
    showToast('الرابط غير مكتمل', 'تحققي من الرابط الأساسي والحقول المطلوبة.', 'warning');
    return;
  }
  try {
    await navigator.clipboard.writeText(value);
    showToast('تم نسخ الرابط', 'يمكنك الآن لصقه في منشورك أو رسالتك.');
  } catch {
    showToast('الرابط جاهز', value, 'warning');
  }
}

function downloadFile(filename, content, type = 'text/csv;charset=utf-8') {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function exportReport(eventsOnly = false) {
  const header = eventsOnly ? ['event', 'source', 'total', 'unique_users', 'change'] : ['campaign', 'channel', 'status', 'spent_sar', 'conversions', 'conversion_rate'];
  const rows = eventsOnly
    ? [['sign_up_completed', 'GA4', '4291', '3988', '22.4%'], ['pricing_viewed', 'PostHog', '18640', '14212', '9.7%'], ['guide_downloaded', 'GA4', '9872', '7101', '16.1%']]
    : state.campaigns.map((campaign) => [campaign.name, campaign.channel, statusLabels[campaign.status], campaign.spent, campaign.conversions, `${campaign.rate || 0}%`]);
  const csv = [header, ...rows].map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n');
  downloadFile(eventsOnly ? 'adloab-events.csv' : 'adloab-campaigns.csv', `\ufeff${csv}`);
  showToast('تم تجهيز ملف CSV', eventsOnly ? 'تم تصدير الأحداث المعروضة.' : 'تم تصدير بيانات الحملات الحالية.');
}

function toggleSidebar(force) {
  const sidebar = document.getElementById('sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  const shouldOpen = typeof force === 'boolean' ? force : !sidebar.classList.contains('open');
  sidebar.classList.toggle('open', shouldOpen);
  backdrop.classList.toggle('visible', shouldOpen);
}

function handleAction(action, target) {
  switch (action) {
    case 'toggle-sidebar':
      toggleSidebar();
      break;
    case 'new-campaign':
      openCampaignModal();
      break;
    case 'close-modal':
      closeModal();
      break;
    case 'download-report':
      exportReport();
      break;
    case 'export-events':
      exportReport(true);
      break;
    case 'copy-utm':
      copyUtm();
      break;
    case 'notifications': {
      const menu = document.getElementById('notification-menu');
      const willOpen = menu.hidden;
      closeFloatingMenus();
      menu.hidden = !willOpen;
      break;
    }
    case 'mark-read':
      document.querySelector('.notification-button i')?.remove();
      closeFloatingMenus();
      showToast('تم تحديث الإشعارات', 'لا توجد إشعارات غير مقروءة الآن.');
      break;
    case 'range-menu': {
      const menu = document.getElementById('date-menu');
      const willOpen = menu.hidden;
      closeFloatingMenus();
      menu.hidden = !willOpen;
      break;
    }
    case 'workspace-menu':
      showToast('مساحة مدار', 'هذه النسخة التجريبية تعمل بمساحة محلية واحدة.', 'warning');
      break;
    case 'profile-menu':
      showToast('حساب تجريبي', 'اربط نظام مصادقة خادمياً قبل استخدام التطبيق في الإنتاج.', 'warning');
      break;
    case 'filters':
      showToast('الفلاتر الأساسية مفعّلة', 'استخدمي البحث وحالة الحملة لتصفية النتائج.', 'warning');
      break;
    case 'run-audit':
      showToast('بدأ فحص الإعدادات', 'يتم فحص الصياغة المحلية فقط، دون فتح روابط أو توليد زيارات.');
      window.setTimeout(() => showToast('اكتمل الفحص', 'لم نجد مشكلة في إعدادات العرض الحالية.'), 900);
      break;
    case 'run-compliance':
      showToast('أُعيد فحص المؤشر', 'تم تحديث قائمة الثقة من الإعدادات المحلية.');
      renderApp();
      break;
    case 'connect-source':
      openIntegrationModal();
      break;
    case 'delete-local-data':
      if (window.confirm('سيتم حذف الحملات والتفضيلات المحلية من هذا المتصفح. هل تريدين المتابعة؟')) {
        localStorage.removeItem('adloab-state');
        state = { ...defaultState, campaigns: [...initialCampaigns], connected: { ...defaultState.connected }, checklist: { ...defaultState.checklist }, settings: { ...defaultState.settings } };
        renderApp(true);
        showToast('تم حذف البيانات المحلية', 'عادت النسخة التجريبية إلى بيانات البداية.');
      }
      break;
    case 'save-settings':
      saveSettings();
      break;
    case 'campaign-menu':
      showToast('خيارات الحملة', 'استخدمي زر الإيقاف أو افتحي تفاصيل الحملة من الإصدار الإنتاجي.', 'warning');
      break;
    case 'toggle-campaign': {
      const campaign = state.campaigns.find((item) => item.id === target?.dataset.id);
      if (!campaign) return;
      campaign.status = campaign.status === 'active' ? 'paused' : 'active';
      saveState();
      renderApp();
      showToast(campaign.status === 'active' ? 'تم تشغيل الحملة' : 'تم إيقاف الحملة مؤقتاً', campaign.name);
      break;
    }
    default:
      break;
  }
}

function saveSettings() {
  const field = document.getElementById('workspace-name');
  if (field?.value.trim()) state.workspaceName = field.value.trim();
  saveState();
  showToast('تم حفظ الإعدادات', `تم تحديث ${state.workspaceName}.`);
}

function handleCampaignSubmit(form) {
  const data = new FormData(form);
  const name = String(data.get('name') || '').trim();
  const rawUrl = String(data.get('url') || '').trim();
  const budget = Number(data.get('budget')) || 0;
  try {
    const url = new URL(rawUrl);
    if (!['http:', 'https:'].includes(url.protocol)) throw new Error('invalid protocol');
  } catch {
    showToast('رابط غير صالح', 'استخدمي رابطاً يبدأ بـ https:// أو http://.', 'warning');
    return;
  }
  const channelKey = String(data.get('channel') || 'organic');
  const newCampaign = {
    id: `c-${Date.now()}`,
    name,
    objective: String(data.get('goal') || 'تحويلات · صفحة الهبوط'),
    channel: channelLabels[channelKey],
    channelKey,
    status: String(data.get('status') || 'draft'),
    budget,
    spent: 0,
    conversions: 0,
    rate: 0,
    updated: 'الآن',
    color: channelKey === 'organic' ? 'lime' : channelKey === 'social' ? 'purple' : channelKey === 'email' ? 'orange' : 'blue'
  };
  state.campaigns.unshift(newCampaign);
  saveState();
  closeModal();
  state.view = 'campaigns';
  renderApp(true);
  showToast('أُضيفت الحملة', `${name} محفوظة كـ ${statusLabels[newCampaign.status]}.`);
}

function handleIntegrationSubmit(form) {
  const data = new FormData(form);
  const id = String(data.get('id') || 'ga4');
  const integration = integrations.find((item) => item.id === id) || integrations[0];
  state.connected[id] = true;
  saveState();
  closeModal();
  if (state.view === 'sources') renderApp();
  showToast('تم حفظ الاتصال', `${integration.name} متصل في النسخة التجريبية.`);
}

function handleFileImport(file) {
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) {
    showToast('الملف كبير جداً', 'الحد المحلي في النسخة التجريبية هو 5 ميغابايت.', 'warning');
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    const lines = String(reader.result || '').split(/\r?\n/).filter(Boolean);
    if (lines.length < 2) {
      showToast('ملف غير مكتمل', 'يحتاج CSV إلى صف عناوين وصف بيانات واحد على الأقل.', 'warning');
      return;
    }
    showToast('تمت قراءة الملف محلياً', `تم العثور على ${formatNumber(lines.length - 1)} صف. لم يتم رفعه إلى أي خدمة.`);
  };
  reader.onerror = () => showToast('تعذر قراءة الملف', 'تحققي من صلاحية الملف وحاولي مرة أخرى.', 'warning');
  reader.readAsText(file);
}

// Global interactions keep the static prototype feeling like a small application.
document.addEventListener('click', (event) => {
  const viewTrigger = event.target.closest('[data-view]');
  if (viewTrigger) {
    event.preventDefault();
    state.view = viewTrigger.dataset.view;
    closeFloatingMenus();
    toggleSidebar(false);
    renderApp(true);
    return;
  }

  const rangeTrigger = event.target.closest('[data-range]');
  if (rangeTrigger) {
    state.range = rangeTrigger.dataset.range;
    closeFloatingMenus();
    saveState();
    renderApp();
    return;
  }

  const filterTrigger = event.target.closest('[data-filter]');
  if (filterTrigger) {
    state.campaignFilter = filterTrigger.dataset.filter;
    renderApp();
    return;
  }

  const connectTrigger = event.target.closest('[data-connect]');
  if (connectTrigger) {
    openIntegrationModal(connectTrigger.dataset.connect);
    return;
  }

  const chartModeTrigger = event.target.closest('[data-chart-mode]');
  if (chartModeTrigger) {
    state.chartMode = chartModeTrigger.dataset.chartMode;
    renderApp();
    return;
  }

  const actionTrigger = event.target.closest('[data-action]');
  if (actionTrigger) {
    handleAction(actionTrigger.dataset.action, actionTrigger);
    return;
  }

  if (event.target.classList.contains('modal-backdrop')) closeModal();
  if (!event.target.closest('.floating-menu') && !event.target.closest('[data-action="range-menu"]') && !event.target.closest('[data-action="notifications"]')) closeFloatingMenus();
});

document.addEventListener('input', (event) => {
  if (event.target.id === 'campaign-search') {
    state.campaignQuery = event.target.value;
    updateCampaignTableOnly();
  }
  if (event.target.closest('#utm-form')) buildUtmUrl();
});

document.addEventListener('change', (event) => {
  const check = event.target.closest('[data-check]');
  if (check) {
    state.checklist[check.dataset.check] = check.checked;
    saveState();
    return;
  }
  const setting = event.target.closest('[data-setting]');
  if (setting) {
    state.settings[setting.dataset.setting] = setting.checked;
    if (setting.dataset.setting === 'darkMode') state.theme = setting.checked ? 'dark' : 'light';
    saveState();
    updateHeader();
    showToast('تم تحديث التفضيل', 'سيبقى الاختيار محفوظاً في هذا المتصفح.');
    return;
  }
  if (event.target.id === 'csv-import') handleFileImport(event.target.files?.[0]);
});

document.addEventListener('submit', (event) => {
  if (event.target.id === 'campaign-form') {
    event.preventDefault();
    handleCampaignSubmit(event.target);
  }
  if (event.target.id === 'integration-form') {
    event.preventDefault();
    handleIntegrationSubmit(event.target);
  }
  if (event.target.id === 'utm-form') {
    event.preventDefault();
    const url = buildUtmUrl();
    if (url) showToast('تم حفظ إعداد UTM', 'يمكنك نسخه من المعاينة متى احتجتِ إليه.');
  }
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    closeModal();
    closeFloatingMenus();
    toggleSidebar(false);
  }
});

hydrateIcons(document);
renderApp();

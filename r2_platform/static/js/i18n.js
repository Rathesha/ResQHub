// ResQHub Translation Dictionary (Single source of truth for EN & TA)
const I18N = {
  en: {
    appName: "ResQHub",
    emergencyWarning: "If life is in immediate danger, call 112.",
    reportNow: "Report now",
    quickPrompt: "Quickly tell us what happened",
    incidentTitle: "Incident Title",
    incidentTitlePlaceholder: "e.g. Gas cylinder fire, 2nd floor",
    categoryLabel: "Emergency Category",
    locationLabel: "Location",
    locationPlaceholder: "Landmark, street, or area name",
    detectGPS: "Detect my live location",
    pinOnMap: "Pin on map",
    peopleAffected: "People Affected",
    descriptionLabel: "Description (Optional)",
    descriptionPlaceholder: "Any additional details (hazards, trapped individuals...)",
    contactLabel: "Reporter Phone (Optional)",
    contactPlaceholder: "+91 98765 43210",
    cameraLabel: "Evidence Photo (Optional)",
    cameraSubtext: "Capture a live photo of the scene or upload image file",
    startCamera: "Open Camera",
    captureFrame: "Capture Frame",
    skipPhoto: "Skip photo and proceed",
    submitReport: "Submit Report",
    submitting: "Submitting report...",
    fire: "Fire",
    roadAccident: "Road Accident",
    medical: "Medical",
    flood: "Flood",
    buildingCollapse: "Building Collapse",
    other: "Other",
    workingOnline: "Working online",
    connectionLost: "Connection lost. Trying to reconnect...",
    noOpenIncidents: "No open incidents. All clear for now.",
    loading: "Loading telemetry...",
    // Confirmation screen
    reportConfirmed: "Emergency Report Logged",
    trackingCode: "Tracking ID",
    assignedSeverity: "Assigned Severity",
    severityReason: "Triage Evaluation",
    alertsSent: "units alerted and en route",
    noUnitsQueued: "No units free right now. Your report is queued and will be sent as soon as one is available.",
    trackLive: "Track Live Dispatch",
    call112Btn: "Call 112 Directly",
    // Admin & Responder
    open: "open",
    critical: "critical",
    oldestUnresolved: "oldest unresolved",
    criticalQueue: "Critical Queue",
    incidentsByCategory: "Incidents by Category",
    allIncidents: "All Open Incidents",
    timeElapsed: "Elapsed",
    reportedAt: "Reported",
    issue: "Issue",
    action: "Action",
    status: "Status",
    assignedTo: "Assigned To",
    view: "View",
    takeAction: "Take Action",
    enRoute: "En Route",
    arrived: "Arrived",
    completed: "Completed",
    acceptClaim: "Accept Dispatch Claim",
    taskActiveWarning: "Finish your current task first"
  },
  ta: {
    appName: "ResQHub",
    emergencyWarning: "உயிருக்கு உடனடி ஆபத்து என்றால் 112-ஐ அழைக்கவும்.",
    reportNow: "உடனே புகாரளிக்கவும்",
    quickPrompt: "என்ன நடந்தது என்று உடனடியாக தெரிவிக்கவும்",
    incidentTitle: "அவசர தலைப்பு",
    incidentTitlePlaceholder: "எ.கா. 2-ஆம் தளத்தில் சிலிண்டர் வெடிப்பு",
    categoryLabel: "அவசர பிரிவு",
    locationLabel: "இடம்",
    locationPlaceholder: "தெரு, பகுதி அல்லது முக்கிய அடையாளம்",
    detectGPS: "நேரலை இருப்பிடத்தை கண்டறி",
    pinOnMap: "வரைபடத்தில் குறிக்கவும்",
    peopleAffected: "பாதிக்கப்பட்டவர்கள்",
    descriptionLabel: "விளக்கம் (விருப்பத்தேர்வு)",
    descriptionPlaceholder: "கூடுதல் விவரங்கள் (ஆபத்துகள், சிக்கிய நபர்கள்...)",
    contactLabel: "தொடர்பு எண் (விருப்பத்தேர்வு)",
    contactPlaceholder: "+91 98765 43210",
    cameraLabel: "ஆதார புகைப்படம் (விருப்பத்தேர்வு)",
    cameraSubtext: "சம்பவ இடத்தின் நேரடி புகைப்படம் எடுக்கவும்",
    startCamera: "கேமராவை திறக்கவும்",
    captureFrame: "படம் எடுக்கவும்",
    skipPhoto: "புகைப்படத்தை தவிர்க்கவும்",
    submitReport: "அவசர புகாரை அனுப்பவும்",
    submitting: "அனுப்பப்படுகிறது...",
    fire: "தீ விபத்து",
    roadAccident: "சாலை விபத்து",
    medical: "மருத்துவ அவசரம்",
    flood: "வெள்ளம்",
    buildingCollapse: "கட்டிட இடிபாடு",
    other: "இதர ஆபத்து",
    workingOnline: "இணைப்பில் உள்ளது",
    connectionLost: "இணைப்பு துண்டிக்கப்பட்டது. மீண்டும் இணைக்கப்படுகிறது...",
    noOpenIncidents: "அவசர புகார்கள் எதுவும் இல்லை. அமைதி நிலவுகிறது.",
    loading: "தரவு ஏற்றப்படுகிறது...",
    // Confirmation
    reportConfirmed: "அவசர அறிக்கை பதிவு செய்யப்பட்டது",
    trackingCode: "கண்காணிப்பு எண்",
    assignedSeverity: "ஒதுக்கப்பட்ட தீவிரம்",
    severityReason: "தானியங்கி மதிப்பீடு",
    alertsSent: "மீட்பு பிரிவுகளுக்கு எச்சரிக்கை அனுப்பப்பட்டது",
    noUnitsQueued: "தற்போது இலவச பிரிவுகள் இல்லை. உங்கள் அறிக்கை வரிசையில் வைக்கப்பட்டுள்ளது.",
    trackLive: "நேரலை கண்காணிப்பு",
    call112Btn: "112-ஐ நேரடியாக அழைக்கவும்",
    // Admin & Responder
    open: "திறந்தவை",
    critical: "அதிதீவிரமானது",
    oldestUnresolved: "பழைய தீர்க்கப்படாதது",
    criticalQueue: "அதிதீவிர வரிசை",
    incidentsByCategory: "பிரிவு வாரியாக அவசரங்கள்",
    allIncidents: "அனைத்து அவசர அறிக்கைகள்",
    timeElapsed: "கடந்த நேரம்",
    reportedAt: "பதிவு செய்யப்பட்ட நேரம்",
    issue: "பிரச்சனை",
    action: "செயல்",
    status: "நிலை",
    assignedTo: "ஒதுக்கப்பட்ட பிரிவு",
    view: "பார்வை",
    takeAction: "நடவடிக்கை எடுக்கவும்",
    enRoute: "வழியில் (En Route)",
    arrived: "வந்தடைந்தது (Arrived)",
    completed: "முடிந்தது (Completed)",
    acceptClaim: "பொறுப்பேற்கவும்",
    taskActiveWarning: "முதலில் தற்போதைய பணியை முடிக்கவும்"
  }
};

let currentLang = localStorage.getItem('resqhub_lang') || 'en';

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('resqhub_lang', lang);
  document.documentElement.lang = lang;
  if (lang === 'ta') {
    document.body.classList.add('font-tamil');
  } else {
    document.body.classList.remove('font-tamil');
  }
  updateLanguageUI();
}

function t(key) {
  return (I18N[currentLang] && I18N[currentLang][key]) || (I18N['en'][key]) || key;
}

function updateLanguageUI() {
  // Update all elements with data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      el.placeholder = t(key);
    } else {
      el.innerText = t(key);
    }
  });

  // Update active state on language switcher buttons
  const btnEn = document.getElementById('lang-en-btn');
  const btnTa = document.getElementById('lang-ta-btn');
  if (btnEn && btnTa) {
    if (currentLang === 'en') {
      btnEn.className = "px-2 py-0.5 rounded text-[11px] font-bold bg-[var(--text-primary)] text-[var(--bg-primary)]";
      btnTa.className = "px-2 py-0.5 rounded text-[11px] font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)]";
    } else {
      btnTa.className = "px-2 py-0.5 rounded text-[11px] font-bold bg-[var(--text-primary)] text-[var(--bg-primary)]";
      btnEn.className = "px-2 py-0.5 rounded text-[11px] font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)]";
    }
  }

  // Trigger any page-specific dynamic string updates
  if (window.onLanguageChanged) {
    window.onLanguageChanged(currentLang);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  setLanguage(currentLang);
});

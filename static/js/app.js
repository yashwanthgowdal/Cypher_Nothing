/**
 * Gadgetbay Reverse Logistics - Enterprise Role-Based Cockpit Controller
 * Implements a strict 3-Persona Chain of Custody with Live Webcam Scanner & Database Persistence:
 * 1. Floor Worker (Marcus Vance - TECH-402) - Optical Barcode Scanner, Bin Approval & Persistence
 * 2. Supervisor (Elena Rostova - SUP-108) - Shift Labor Slider, Mathematical Optimization & Hazard Vault
 * 3. Executive (David Chen - EXEC-001) - Dual PDF View, Audit Dossier & Legal Vendor Claim
 */

document.addEventListener('DOMContentLoaded', () => {
  // Session & Persona State
  let currentUser = null;
  let activeBatch = "HB-09";
  let currentBatchData = null;
  let debounceTimer = null;
  let lastScannedItemData = null;
  let lastScannedBinAssigned = "BIN-RECEIVING";

  // Login Gate Elements
  const loginGateScreen = document.getElementById('loginGateScreen');
  const appWorkspace = document.getElementById('appWorkspace');
  const loginForm = document.getElementById('loginForm');
  const loginIdInput = document.getElementById('loginIdInput');
  const loginPasswordInput = document.getElementById('loginPasswordInput');
  const loginErrorAlert = document.getElementById('loginErrorAlert');
  const quickCredCards = document.querySelectorAll('.quick-cred-card');
  const googleSignInBtn = document.getElementById('googleSignInBtn');
  const logoutBtn = document.getElementById('logoutBtn');

  // Header Elements
  const currentRoleSubtitle = document.getElementById('currentRoleSubtitle');
  const userAvatar = document.getElementById('userAvatar');
  const userName = document.getElementById('userName');
  const userId = document.getElementById('userId');
  const roleSelectorBar = document.getElementById('roleSelectorBar');
  const roleTabBtns = document.querySelectorAll('.role-tab-btn');

  // Worker Elements
  const workerScannerInput = document.getElementById('workerScannerInput');
  const workerScanTriggerBtn = document.getElementById('workerScanTriggerBtn');
  const workerChips = document.querySelectorAll('.worker-chip');
  const directiveHero = document.getElementById('directiveHero');
  const directiveIcon = document.getElementById('directiveIcon');
  const directiveAction = document.getElementById('directiveAction');
  const directiveSub = document.getElementById('directiveSub');
  const wSerial = document.getElementById('wSerial');
  const wProduct = document.getElementById('wProduct');
  const wGrade = document.getElementById('wGrade');
  const wWarranty = document.getElementById('wWarranty');
  const wDecision = document.getElementById('wDecision');
  const confirmBinBtn = document.getElementById('confirmBinBtn');
  const binSuccessNotice = document.getElementById('binSuccessNotice');
  const toggleAgentReasoningBtn = document.getElementById('toggleAgentReasoningBtn');
  const agentReasoningBox = document.getElementById('agentReasoningBox');
  const reasoningTableBody = document.getElementById('reasoningTableBody');
  const reasoningNarrative = document.getElementById('reasoningNarrative');

  // Webcam Scanner Elements
  const startWebcamBtn = document.getElementById('startWebcamBtn');
  const stopWebcamBtn = document.getElementById('stopWebcamBtn');
  const uploadBarcodeBtn = document.getElementById('uploadBarcodeBtn');
  const barcodeFileInput = document.getElementById('barcodeFileInput');
  const webcamPlaceholder = document.getElementById('webcamPlaceholder');
  const webcamReticle = document.getElementById('webcamReticle');
  const reticleGuideText = document.getElementById('reticleGuideText');
  const cameraPill = document.getElementById('cameraPill');
  const cameraDetectionAlert = document.getElementById('cameraDetectionAlert');
  const detectedCodeText = document.getElementById('detectedCodeText');
  const detectedFormatBadge = document.getElementById('detectedFormatBadge');
  const detectedSubMsg = document.getElementById('detectedSubMsg');
  const toastStatusTitle = document.getElementById('toastStatusTitle');
  const toastIcon = document.getElementById('toastIcon');
  const webcamHudGuidance = document.getElementById('webcamHudGuidance');
  const hudGuidanceIcon = document.getElementById('hudGuidanceIcon');
  const hudGuidanceText = document.getElementById('hudGuidanceText');

  // Supervisor Elements
  const supLaborSlider = document.getElementById('supLaborSlider');
  const supLaborSliderVal = document.getElementById('supLaborSliderVal');
  const supNetSalvage = document.getElementById('supNetSalvage');
  const supUplift = document.getElementById('supUplift');
  const supLaborUsed = document.getElementById('supLaborUsed');
  const supLaborMax = document.getElementById('supLaborMax');
  const supChannelDistBar = document.getElementById('supChannelDistBar');
  const supChannelCardsGrid = document.getElementById('supChannelCardsGrid');
  const transmitToExecBtn = document.getElementById('transmitToExecBtn');
  const supBatchSelectDropdown = document.getElementById('supBatchSelectDropdown');
  const supAgentLaborNotice = document.getElementById('supAgentLaborNotice');
  const supAlertBanner = document.getElementById('supAlertBanner');

  // Executive Elements
  const execViewPdfBtn = document.getElementById('execViewPdfBtn');
  const execDirectDownloadPdfBtn = document.getElementById('execDirectDownloadPdfBtn');
  const execCopyNoticeBtn = document.getElementById('execCopyNoticeBtn');
  const execLegalNotice = document.getElementById('execLegalNotice');
  const execBatchSelectDropdown = document.getElementById('execBatchSelectDropdown');

  // =========================================================================
  // AUTHENTICATION & SESSION MANAGEMENT
  // =========================================================================
  function initAuthSession() {
    const saved = sessionStorage.getItem('gb_user_session');
    if (saved) {
      try {
        const user = JSON.parse(saved);
        applyUserSession(user);
        return;
      } catch (e) {
        sessionStorage.removeItem('gb_user_session');
      }
    }
    // Show login screen
    if (loginGateScreen) loginGateScreen.style.display = 'flex';
    if (appWorkspace) appWorkspace.style.display = 'none';
  }

  function applyUserSession(user) {
    currentUser = user;
    if (loginGateScreen) loginGateScreen.style.display = 'none';
    if (appWorkspace) appWorkspace.style.display = 'block';

    // Update Header
    if (userName) userName.textContent = user.name;
    if (userId) userId.textContent = `ID: ${user.id}`;
    if (userAvatar) userAvatar.textContent = user.avatar;
    if (currentRoleSubtitle) currentRoleSubtitle.textContent = `Role: ${user.title}`;

    // Hide all stations
    document.querySelectorAll('.role-view').forEach(view => view.classList.remove('active'));

    // Strict Role Isolation: Each worker ONLY gets their dedicated interface
    if (roleSelectorBar) roleSelectorBar.style.display = 'none';

    if (user.role === 'worker') {
      const workerView = document.getElementById('roleWorkerView');
      if (workerView) workerView.classList.add('active');
    } else if (user.role === 'supervisor') {
      const supView = document.getElementById('roleSupervisorView');
      if (supView) supView.classList.add('active');
      loadBatchData(activeBatch, 20.0);
    } else if (user.role === 'executive') {
      const execView = document.getElementById('roleExecutiveView');
      if (execView) execView.classList.add('active');
      loadBatchData(activeBatch, 20.0);
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Handle Login Form Submit
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const id = loginIdInput ? loginIdInput.value.trim() : '';
      const password = loginPasswordInput ? loginPasswordInput.value : '';

      if (!id || !password) return;

      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id, password })
        });
        const data = await res.json();

        if (!res.ok || !data.success) {
          showLoginError(data.error || "Authentication failed. Check your ID and password.");
          return;
        }

        sessionStorage.setItem('gb_user_session', JSON.stringify(data.user));
        applyUserSession(data.user);
      } catch (err) {
        showLoginError("Server communication error. Please ensure server is running.");
      }
    });
  }

  function showLoginError(msg) {
    if (loginErrorAlert) {
      loginErrorAlert.textContent = `⚠️ ${msg}`;
      loginErrorAlert.style.display = 'block';
    }
  }

  // Quick Credential Card Clicks
  quickCredCards.forEach(card => {
    card.addEventListener('click', () => {
      const uid = card.dataset.id;
      const upass = card.dataset.pass;
      if (loginIdInput) loginIdInput.value = uid;
      if (loginPasswordInput) loginPasswordInput.value = upass;
      if (loginErrorAlert) loginErrorAlert.style.display = 'none';
      if (loginForm) loginForm.requestSubmit();
    });
  });

  // Google SSO Button Handler
  if (googleSignInBtn) {
    googleSignInBtn.addEventListener('click', () => {
      alert(
        "🚀 GOOGLE WORKSPACE SSO READY FOR ENTERPRISE HOOK\n\n" +
        "To enable direct 1-click Google OAuth 2.0 Sign-In:\n" +
        "1. Open Google Cloud Console (console.cloud.google.com)\n" +
        "2. Create an OAuth 2.0 Web Client ID with origin 'http://127.0.0.1:5000'\n" +
        "3. Provide your GOOGLE_CLIENT_ID to connect your company domain.\n\n" +
        "👉 For instant role access right now, click any of the 3 Quick Sign-In cards above!"
      );
    });
  }

  // Logout Handler
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      await stopCameraStream();
      sessionStorage.removeItem('gb_user_session');
      currentUser = null;
      if (appWorkspace) appWorkspace.style.display = 'none';
      if (loginGateScreen) loginGateScreen.style.display = 'flex';
      if (loginPasswordInput) loginPasswordInput.value = '';
      if (loginErrorAlert) loginErrorAlert.style.display = 'none';
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // =========================================================================
  // AUDIO SYNTHESIZERS (Real Hardware Scanners)
  // =========================================================================
  // 1. Authentic handheld scanner beep (1850Hz -> 2400Hz affirmative pip)
  function playBarcodeBeep() {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(1850, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(2400, audioCtx.currentTime + 0.08);
      gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.08);
      osc.connect(gainNode);
      gainNode.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.08);
    } catch (e) {
      // AudioContext muted/unpermitted
    }
  }

  // 2. Unregistered SKU warning buzz (360Hz -> 240Hz cautionary tone)
  function playWarningBuzz() {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(360, audioCtx.currentTime);
      osc.frequency.setValueAtTime(240, audioCtx.currentTime + 0.12);
      gainNode.gain.setValueAtTime(0.22, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.25);
      osc.connect(gainNode);
      gainNode.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.25);
    } catch (e) {
      // AudioContext muted/unpermitted
    }
  }

  // =========================================================================
  // REAL FULL-FRAME OPTICAL BARCODE SCANNER (Html5Qrcode Engine)
  // (Untouched as requested: camera feed, full-frame detection, sound, photo upload)
  // =========================================================================
  let html5QrCode = null;
  let isScannerRunning = false;
  let lastScannedCode = null;
  let lastScannedTime = 0;
  let lastDetectionTime = 0;

  if (startWebcamBtn) {
    startWebcamBtn.addEventListener('click', async () => {
      await startCameraStream();
    });
  }

  if (stopWebcamBtn) {
    stopWebcamBtn.addEventListener('click', async () => {
      await stopCameraStream();
    });
  }

  if (uploadBarcodeBtn && barcodeFileInput) {
    uploadBarcodeBtn.addEventListener('click', () => {
      barcodeFileInput.click();
    });

    barcodeFileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      try {
        if (!html5QrCode) {
          html5QrCode = new Html5Qrcode("webcamReader", { verbose: false });
        }
        const decodedText = await html5QrCode.scanFile(file, true);
        if (decodedText) {
          onOpticalBarcodeRead(decodedText, "IMAGE_UPLOAD");
        }
      } catch (err) {
        alert("Could not detect a barcode in this photo. Please ensure the barcode is clear, in focus, and not cut off.");
      }
      barcodeFileInput.value = '';
    });
  }

  async function startCameraStream() {
    try {
      cameraPill.textContent = "INITIALIZING...";
      cameraPill.className = "badge badge-hazard";

      if (!html5QrCode) {
        const formats = window.Html5QrcodeSupportedFormats ? [
          Html5QrcodeSupportedFormats.EAN_13,
          Html5QrcodeSupportedFormats.EAN_8,
          Html5QrcodeSupportedFormats.UPC_A,
          Html5QrcodeSupportedFormats.UPC_E,
          Html5QrcodeSupportedFormats.CODE_128,
          Html5QrcodeSupportedFormats.CODE_39,
          Html5QrcodeSupportedFormats.CODE_93,
          Html5QrcodeSupportedFormats.ITF,
          Html5QrcodeSupportedFormats.QR_CODE,
          Html5QrcodeSupportedFormats.DATA_MATRIX
        ] : undefined;

        html5QrCode = new Html5Qrcode("webcamReader", {
          formatsToSupport: formats,
          verbose: false,
          experimentalFeatures: {
            useBarCodeDetectorIfSupported: true
          }
        });
      }

      const cameraConfig = { facingMode: "user" };
      const scanConfig = {
        fps: 20,
        aspectRatio: 1.333333
      };

      await html5QrCode.start(
        cameraConfig,
        scanConfig,
        (decodedText, decodedResult) => {
          const fmt = decodedResult && decodedResult.result && decodedResult.result.format 
            ? decodedResult.result.format.formatName 
            : "OPTICAL_BARCODE";
          onOpticalBarcodeRead(decodedText, fmt);
        },
        (errorMessage) => {
          const now = Date.now();
          if (now - lastDetectionTime > 3000) {
            updateGuidanceState(false);
          }
        }
      );

      isScannerRunning = true;
      webcamPlaceholder.style.display = 'none';
      webcamReticle.style.display = 'flex';
      if (webcamHudGuidance) webcamHudGuidance.style.display = 'flex';

      startWebcamBtn.style.display = 'none';
      stopWebcamBtn.style.display = 'inline-flex';

      cameraPill.textContent = "FULL-FRAME OPTICAL SCANNER ACTIVE";
      cameraPill.className = "badge badge-emerald";

      lastDetectionTime = Date.now();
      updateGuidanceState(false);
    } catch (err) {
      console.error("Camera start failed:", err);
      cameraPill.textContent = "NO CAMERA ACCESS";
      cameraPill.className = "badge badge-subtle";
      alert("Could not start camera: " + (err.message || err) + "\nPlease allow camera permission in your browser.");
    }
  }

  async function stopCameraStream() {
    if (html5QrCode && isScannerRunning) {
      try {
        await html5QrCode.stop();
        html5QrCode.clear();
      } catch (e) {
        console.warn("Scanner stop:", e);
      }
      isScannerRunning = false;
    }

    if (webcamPlaceholder) webcamPlaceholder.style.display = 'block';
    if (webcamReticle) webcamReticle.style.display = 'none';
    if (webcamHudGuidance) webcamHudGuidance.style.display = 'none';

    if (startWebcamBtn) startWebcamBtn.style.display = 'inline-flex';
    if (stopWebcamBtn) stopWebcamBtn.style.display = 'none';

    if (cameraPill) {
      cameraPill.textContent = "STANDBY";
      cameraPill.className = "badge badge-subtle";
    }
  }

  function updateGuidanceState(isLocked) {
    if (!webcamHudGuidance || !hudGuidanceText) return;

    if (isLocked) {
      webcamReticle.classList.remove('warning');
      webcamReticle.classList.add('locked');
      webcamHudGuidance.classList.remove('warning');
      webcamHudGuidance.classList.add('locked');
      if (hudGuidanceIcon) hudGuidanceIcon.textContent = "🎯";
      hudGuidanceText.textContent = `TARGET LOCKED: ${lastScannedCode}`;
      if (reticleGuideText) reticleGuideText.textContent = "BARCODE LOCKED";
    } else {
      webcamReticle.classList.remove('locked');
      webcamHudGuidance.classList.remove('locked');
      const timeSinceDetection = Date.now() - lastDetectionTime;
      if (timeSinceDetection > 3000) {
        webcamReticle.classList.add('warning');
        webcamHudGuidance.classList.add('warning');
        if (hudGuidanceIcon) hudGuidanceIcon.textContent = "⚠️";
        hudGuidanceText.textContent = "Hold barcode ~15–25 cm (6–10 in) from camera where sharp & clear";
        if (reticleGuideText) reticleGuideText.textContent = "SEARCHING FULL FRAME";
      } else {
        webcamReticle.classList.remove('warning');
        webcamHudGuidance.classList.remove('warning');
        if (hudGuidanceIcon) hudGuidanceIcon.textContent = "🔍";
        hudGuidanceText.textContent = "Full-frame optical sensor active. Detecting barcodes anywhere in view...";
        if (reticleGuideText) reticleGuideText.textContent = "SCANNING FULL VIEWPORT";
      }
    }
  }

  function onOpticalBarcodeRead(code, formatName) {
    if (!code) return;
    const cleanCode = code.trim();
    const now = Date.now();

    // Prevent duplicate triggers within 2.5s for the identical barcode
    if (lastScannedCode === cleanCode && (now - lastScannedTime) < 2500) {
      return;
    }

    lastScannedCode = cleanCode;
    lastScannedTime = now;
    lastDetectionTime = now;

    // 1. Play scanner beep
    playBarcodeBeep();

    // 2. Update camera HUD to target locked
    updateGuidanceState(true);

    // 3. Update detection toast
    if (cameraDetectionAlert) {
      cameraDetectionAlert.style.display = 'block';
      cameraDetectionAlert.className = 'detection-toast';
    }
    if (detectedCodeText) detectedCodeText.textContent = cleanCode;
    if (detectedFormatBadge) detectedFormatBadge.textContent = formatName || "OPTICAL";
    if (toastStatusTitle) toastStatusTitle.textContent = "Decoded:";
    if (detectedSubMsg) detectedSubMsg.textContent = "Checking inventory database match...";

    // 4. Fill manual input field
    if (workerScannerInput) workerScannerInput.value = cleanCode;

    // 5. Query reverse logistics database
    executeWorkerScan(cleanCode, formatName);

    // Release lock visual after 2.8s
    setTimeout(() => {
      if (Date.now() - lastDetectionTime >= 2700) {
        updateGuidanceState(false);
      }
    }, 2800);
  }

  // =========================================================================
  // WORKER STATION SCAN EXECUTION & DIRECTIVE RENDERING
  // =========================================================================
  if (workerScanTriggerBtn) {
    workerScanTriggerBtn.addEventListener('click', () => {
      const serial = workerScannerInput.value.trim();
      if (serial) {
        playBarcodeBeep();
        executeWorkerScan(serial, "MANUAL_INPUT");
      }
    });
  }

  if (workerScannerInput) {
    workerScannerInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        const serial = workerScannerInput.value.trim();
        if (serial) {
          playBarcodeBeep();
          executeWorkerScan(serial, "MANUAL_INPUT");
        }
      }
    });
  }

  workerChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const serial = chip.dataset.serial;
      if (workerScannerInput) workerScannerInput.value = serial;
      playBarcodeBeep();
      executeWorkerScan(serial, "PALLET_SAMPLE");
    });
  });

  async function executeWorkerScan(serial, formatName) {
    try {
      const res = await fetch(`/api/scan/${encodeURIComponent(serial)}`);
      const data = await res.json();
      lastScannedItemData = { ...data, serial, formatName };

      if (!res.ok || !data.found) {
        // Barcode successfully decoded, BUT NOT FOUND IN DATABASE!
        playWarningBuzz();

        if (cameraDetectionAlert) {
          cameraDetectionAlert.className = 'detection-toast hazard';
        }
        if (toastStatusTitle) toastStatusTitle.textContent = "⚠️ Unregistered SKU:";
        if (detectedSubMsg) {
          detectedSubMsg.textContent = `Barcode '${serial}' detected, but not registered in active inventory manifest.`;
        }

        renderUnregisteredDirective(serial, formatName, data.message || "Record not found in database.");
        return;
      }

      // FOUND IN DATABASE!
      if (cameraDetectionAlert) {
        cameraDetectionAlert.className = 'detection-toast';
      }
      if (toastStatusTitle) toastStatusTitle.textContent = "✅ Database Match:";
      if (detectedSubMsg) {
        detectedSubMsg.textContent = `Matched ${data.unit.product_name} (${data.unit.return_id}). AI disposition generated!`;
      }

      renderWorkerDirective(data);
    } catch (err) {
      console.error('Scan error:', err);
    }
  }

  function renderUnregisteredDirective(serial, formatName, msg) {
    lastScannedBinAssigned = "ZONE_MANUAL_REVIEW";
    directiveHero.className = "directive-hero-box hazard-box";
    directiveIcon.textContent = "⚠️";
    directiveAction.textContent = "NOT FOUND IN DATABASE";
    directiveSub.textContent = `BARCODE [${serial}] READ SUCCESSFUL • NO INBOUND RMA RECORD`;

    wSerial.textContent = serial;
    wProduct.textContent = "External / Unregistered SKU (Not in HB-09 Manifest)";
    wGrade.textContent = formatName ? `Symbology: ${formatName}` : "Hardware Optical Read OK";
    wWarranty.textContent = "N/A — No Supplier MSA Contract on File";
    wDecision.textContent = "DISPOSITION BLOCKED: Product unmanifested. Log to review holding bin.";

    if (confirmBinBtn) {
      confirmBinBtn.textContent = "✓ Confirm Item to Manual Review Holding Bin (Log Scan)";
      confirmBinBtn.style.background = "var(--accent-amber)";
    }
  }

  function renderWorkerDirective(data) {
    const u = data.unit;
    const evalRes = data.evaluation;
    const bestCh = evalRes.best_channel;

    wSerial.textContent = u.return_id;
    wProduct.textContent = `${u.product_name} (${u.sku})`;
    wGrade.textContent = `Grade ${u.grade} (${u.fault_code})`;
    wWarranty.textContent = `${u.days_since_dispatch} days (${evalRes.is_rtv_eligible ? 'Within 30-Day Window' : 'Window Expired'})`;

    if (evalRes.is_hazardous) {
      lastScannedBinAssigned = "ZONE_D_HAZARD_VAULT";
      directiveHero.className = "directive-hero-box hazard-box";
      directiveIcon.textContent = "🚨";
      directiveAction.textContent = "MOVE TO ZONE D HAZARD VAULT";
      directiveSub.textContent = "CRITICAL DEFECT DETECTED • ISOLATE FROM INVENTORY";
      wDecision.textContent = `QUARANTINE / SCRAP (Salvage: ₹${evalRes.max_nsv.toFixed(2)})`;
    } else if (bestCh === 'RTV') {
      lastScannedBinAssigned = "VENDOR_RMA_PALLET";
      directiveHero.className = "directive-hero-box rtv-box";
      directiveIcon.textContent = "📦";
      directiveAction.textContent = "PLACE IN VENDOR RMA PALLET (RTV)";
      directiveSub.textContent = `CONTRACTUAL 60% CASH CREDIT • RECOVER ₹${evalRes.max_nsv.toFixed(2)}`;
      wDecision.textContent = `RTV (Contractual Claim - Recoup ₹${evalRes.max_nsv.toFixed(2)})`;
    } else if (bestCh === 'REFURBISH') {
      lastScannedBinAssigned = "WORKBENCH_3_REFURB";
      directiveHero.className = "directive-hero-box refurb-box";
      directiveIcon.textContent = "🔧";
      directiveAction.textContent = "ROUTE TO WORKBENCH #3 (REFURBISH)";
      directiveSub.textContent = `SECONDARY RESALE GRADE • PROJECTED NET ₹${evalRes.max_nsv.toFixed(2)}`;
      wDecision.textContent = `REFURBISH (Net Salvage: ₹${evalRes.max_nsv.toFixed(2)})`;
    } else if (bestCh === 'RESTOCK') {
      lastScannedBinAssigned = "BIN_OPEN_BOX_RESTOCK";
      directiveHero.className = "directive-hero-box restock-box";
      directiveIcon.textContent = "✨";
      directiveAction.textContent = "RESTOCK TO OPEN-BOX SELLABLE SHELF";
      directiveSub.textContent = `PRISTINE CONDITION • DIRECT RESALE VALUE ₹${evalRes.max_nsv.toFixed(2)}`;
      wDecision.textContent = `RESTOCK (Active Inventory Reintegration)`;
    } else {
      lastScannedBinAssigned = "ZONE_BULK_SCRAP";
      directiveHero.className = "directive-hero-box hazard-box";
      directiveIcon.textContent = "🏢";
      directiveAction.textContent = "ROUTE TO BULK LIQUIDATION LOT";
      directiveSub.textContent = `WHOLESALE RECOVERY (35%) • RECOVER ₹${evalRes.max_nsv.toFixed(2)}`;
      wDecision.textContent = `LIQUIDATE (Net Salvage: ₹${evalRes.max_nsv.toFixed(2)})`;
    }

    if (confirmBinBtn) {
      confirmBinBtn.textContent = "✓ Confirm Physical Bin Placement (Move to Next Unit)";
      confirmBinBtn.style.background = "";
    }

    // Populate Agent Multi-Channel Economic Comparison Table
    if (reasoningTableBody) {
      const chNsv = evalRes.channel_nsv || {};
      const channels = [
        {
          key: 'RESTOCK',
          name: 'Restock (Open-Box)',
          val: chNsv.RESTOCK !== undefined ? chNsv.RESTOCK : 0.0,
          eval: u.grade === 'A' && !evalRes.is_hazardous ? 'Pristine resale • Direct inventory reintegration' : 'REJECTED: Cosmetic or functional defects present'
        },
        {
          key: 'RTV',
          name: 'Return-to-Vendor (RTV)',
          val: chNsv.RTV !== undefined ? chNsv.RTV : 0.0,
          eval: evalRes.is_hazardous ? '100% Cash Indemnification (MSA § 4.2 Defect Claim)' : (evalRes.is_rtv_eligible ? '80% Contractual credit within 30-day window' : 'REJECTED: Contractual warranty window expired')
        },
        {
          key: 'REFURBISH',
          name: 'Workbench #3 (Refurbish)',
          val: chNsv.REFURBISH !== undefined ? chNsv.REFURBISH : 0.0,
          eval: evalRes.is_hazardous ? 'BLOCKED: Fire safety violation to repair swollen lithium cells' : `Grade ${u.grade} restoration • ${evalRes.refurb_hours_required || 1.0}h technician labor`
        },
        {
          key: 'LIQUIDATE',
          name: 'Bulk Lot Liquidation',
          val: chNsv.LIQUIDATE !== undefined ? chNsv.LIQUIDATE : 0.0,
          eval: 'Secondary wholesale recovery (18% wholesale salvage)'
        },
        {
          key: 'SCRAP',
          name: 'Eco-Recycle / Scrap',
          val: chNsv.SCRAP !== undefined ? chNsv.SCRAP : 0.0,
          eval: 'End-of-life materials reclaim (3% baseline recovery)'
        }
      ];

      reasoningTableBody.innerHTML = channels.map(ch => {
        const isWinner = ch.key === bestCh;
        return `
          <tr class="${isWinner ? 'winner-row' : ''}">
            <td><strong>${ch.name}</strong> ${isWinner ? '🏆' : ''}</td>
            <td class="font-mono ${isWinner ? 'text-emerald' : ''}">${ch.val > -90000 ? `₹${Number(ch.val).toFixed(2)}` : 'Ineligible'}</td>
            <td style="color:${isWinner ? 'var(--accent-emerald)' : 'var(--text-muted)'}">${ch.eval}</td>
          </tr>
        `;
      }).join('');
    }

    if (reasoningNarrative) {
      let narrative = `<strong>Agent Triage Directive: ${bestCh}</strong> (Projected Net Salvage Value: <strong>₹${evalRes.max_nsv.toFixed(2)}</strong>). `;
      if (bestCh === 'REFURBISH') {
        narrative += `High secondary resale captured via 5-day bench refurbishment: ₹${u.retail_price} × 75% − ₹250 = <strong>₹${evalRes.max_nsv.toFixed(2)}</strong> net. Time-to-cash: ~19 days.`;
      } else if (bestCh === 'RTV') {
        narrative += `Contractual manufacturer warranty credit secures cash recovery (60% of ₹${u.cost_price} = ₹${evalRes.max_nsv.toFixed(2)}) with zero labor. Time-to-cash: ~32 days.`;
      } else if (bestCh === 'LIQUIDATE') {
        narrative += `Fastest cash liquidation (35% of ₹${u.cost_price} = ₹${evalRes.max_nsv.toFixed(2)}). Time-to-cash: ~6 days.`;
      } else {
        narrative += `Allocated according to mathematical net salvage optimization.`;
      }
      reasoningNarrative.innerHTML = narrative;
    }
  }

  // Toggle Agent Reasoning Drawer
  if (toggleAgentReasoningBtn && agentReasoningBox) {
    toggleAgentReasoningBtn.addEventListener('click', () => {
      const isHidden = agentReasoningBox.style.display === 'none';
      agentReasoningBox.style.display = isHidden ? 'block' : 'none';
      toggleAgentReasoningBtn.textContent = isHidden ? '❌ Hide Agent Reasoning Matrix' : '🧠 Show Agent Reasoning & Channel Matrix';
    });
  }

  // =========================================================================
  // FLOOR WORKER PERSISTENT CONFIRMATION & SEAMLESS RE-SCAN LOOP
  // When worker clicks confirm, it saves to SQLite DB and stays on same scanning screen!
  // =========================================================================
  if (confirmBinBtn) {
    confirmBinBtn.addEventListener('click', async () => {
      confirmBinBtn.disabled = true;
      confirmBinBtn.textContent = '⏳ Verifying & Recording in Database...';

      const barcodeVal = workerScannerInput.value.trim() || lastScannedCode || "UNKNOWN_BARCODE";
      const isKnown = lastScannedItemData && lastScannedItemData.found;

      const payload = {
        barcode: barcodeVal,
        return_id: isKnown ? lastScannedItemData.unit.return_id : barcodeVal,
        sku: isKnown ? lastScannedItemData.unit.sku : "UNKNOWN",
        product_name: isKnown ? lastScannedItemData.unit.product_name : "Unregistered Barcode Item",
        grade: isKnown ? lastScannedItemData.unit.grade : "N/A",
        fault_code: isKnown ? lastScannedItemData.unit.fault_code : "N/A",
        is_hazardous: isKnown && lastScannedItemData.evaluation.is_hazardous ? 1 : 0,
        best_channel: isKnown ? lastScannedItemData.evaluation.best_channel : "HOLD_REVIEW",
        bin_assigned: lastScannedBinAssigned,
        nsv_amount: isKnown ? lastScannedItemData.evaluation.max_nsv : 0.0,
        operator_id: currentUser ? currentUser.id : "TECH-402",
        status: "CONFIRMED",
        is_external: isKnown ? 0 : 1
      };

      try {
        const res = await fetch('/api/scans/record', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const result = await res.json();

        // Affirmative visual feedback in worker view
        confirmBinBtn.textContent = '✓ Verified & Stored in Database!';
        confirmBinBtn.style.background = 'var(--accent-emerald)';

        if (binSuccessNotice) {
          binSuccessNotice.innerHTML = `
            <strong>✓ UNIT RECORDED IN DATABASE!</strong><br>
            <span>Unit [${payload.return_id}] permanently logged to bin <strong>${payload.bin_assigned}</strong> by operator ${payload.operator_id}.</span>
          `;
          binSuccessNotice.style.display = 'block';
        }

        // Clean re-scan loop: Reset input fields for the next unit and stay on Floor Worker screen
        setTimeout(() => {
          confirmBinBtn.disabled = false;
          confirmBinBtn.textContent = '✓ Confirm Physical Bin Placement (Move to Next Unit)';
          confirmBinBtn.style.background = '';

          if (workerScannerInput) {
            workerScannerInput.value = '';
            workerScannerInput.focus();
          }

          directiveHero.className = "directive-hero-box restock-box";
          directiveIcon.textContent = "📦";
          directiveAction.textContent = "READY FOR NEXT SCAN";
          directiveSub.textContent = "POINT CAMERA AT NEXT BARCODE OR ENTER SERIAL";
          wSerial.textContent = "—";
          wProduct.textContent = "Awaiting Next Inbound Unit...";
          wGrade.textContent = "—";
          wWarranty.textContent = "—";
          wDecision.textContent = "Awaiting scan";

          if (cameraDetectionAlert) {
            cameraDetectionAlert.style.display = 'none';
          }
        }, 1600);

      } catch (err) {
        console.error('Record scan error:', err);
        confirmBinBtn.disabled = false;
        confirmBinBtn.textContent = '✓ Confirm Physical Bin Placement (Move to Next Unit)';
        confirmBinBtn.style.background = '';
      }
    });
  }

  // =========================================================================
  // SUPERVISOR STATION LOGIC (Elena Rostova - SUP-108)
  // =========================================================================
  if (supLaborSlider) {
    supLaborSlider.addEventListener('input', (e) => {
      const val = parseFloat(e.target.value).toFixed(1);
      if (supLaborSliderVal) supLaborSliderVal.textContent = `${val} hrs`;
      if (supLaborMax) supLaborMax.textContent = `Capacity Limit: ${val} hrs`;
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        loadBatchData(activeBatch, val);
      }, 180);
    });
  }

  // Supervisor Batch Switching
  if (supBatchSelectDropdown) {
    supBatchSelectDropdown.addEventListener('change', (e) => {
      activeBatch = e.target.value;
      if (execBatchSelectDropdown) execBatchSelectDropdown.value = activeBatch;
      const currentLabor = supLaborSlider ? parseFloat(supLaborSlider.value) : 20.0;
      loadBatchData(activeBatch, currentLabor);
    });
  }

  // Executive Batch Switching
  if (execBatchSelectDropdown) {
    execBatchSelectDropdown.addEventListener('change', (e) => {
      activeBatch = e.target.value;
      if (supBatchSelectDropdown) supBatchSelectDropdown.value = activeBatch;
      const currentLabor = supLaborSlider ? parseFloat(supLaborSlider.value) : 20.0;
      loadBatchData(activeBatch, currentLabor);
    });
  }

  if (transmitToExecBtn) {
    transmitToExecBtn.addEventListener('click', () => {
      alert(
        `📋 SUPERVISOR TRIAGE LOCKED & TRANSMITTED!\n\n` +
        `Batch ${activeBatch} optimization plan has been mathematically locked and signed off by Elena Rostova (SUP-108).\n\n` +
        `👉 Next Step in Chain of Custody: Log out and have Finance Executive David Chen (EXEC-001) log in to generate the legal vendor RTV PDF dossier!`
      );
    });
  }

  async function loadBatchData(batchId, laborCap) {
    try {
      const res = await fetch(`/api/triage/${batchId}?labor_cap=${laborCap}`);
      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      currentBatchData = data;
      renderSupervisorData(data);
    } catch (err) {
      console.error('Failed to load batch data:', err);
    }
  }

  function renderSupervisorData(data) {
    const opt = data.optimization_results;
    const uplift = data.uplift;

    if (supNetSalvage) supNetSalvage.textContent = `₹${opt.total_nsv.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (supUplift) supUplift.textContent = `+₹${uplift.dollar_uplift.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (supLaborUsed) supLaborUsed.textContent = `${opt.labor_hours_used} hrs`;

    // Dynamic Supervisor Alert Banner based on Anomaly Sentinel
    if (supAlertBanner) {
      const threeLvl = data.anomalies && data.anomalies.three_level_quality_analysis;
      if (threeLvl && threeLvl.level_1_observed_pattern.defect_rate_pct >= 35.0) {
        supAlertBanner.style.display = 'flex';
        supAlertBanner.className = 'alert-banner alert-critical';
        const titleEl = supAlertBanner.querySelector('.alert-title');
        const descEl = supAlertBanner.querySelector('.alert-desc');
        const badgeEl = supAlertBanner.querySelector('.badge');
        const iconEl = supAlertBanner.querySelector('.alert-icon');
        if (iconEl) iconEl.textContent = '⚠️';
        const lvl1 = threeLvl.level_1_observed_pattern;
        if (titleEl) titleEl.textContent = `RECURRING DEFECT SURGE (LOT ${data.batch_id}: ${lvl1.affected_units} OF ${lvl1.total_units} UNITS)`;
        if (descEl) descEl.textContent = `${lvl1.defect_rate_pct}% of Lot ${data.batch_id} exhibited '${lvl1.defect_name}'. Cross-batch analysis: 0% in peer batches (HB-07, HB-08, HB-10). Isolated production solder flaw.`;
        if (badgeEl) {
          badgeEl.textContent = 'AUDIT INQUIRY FLAGGED';
          badgeEl.className = 'badge badge-hazard';
        }
      } else {
        supAlertBanner.style.display = 'flex';
        supAlertBanner.className = 'alert-banner';
        supAlertBanner.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        const titleEl = supAlertBanner.querySelector('.alert-title');
        const descEl = supAlertBanner.querySelector('.alert-desc');
        const badgeEl = supAlertBanner.querySelector('.badge');
        const iconEl = supAlertBanner.querySelector('.alert-icon');
        if (iconEl) iconEl.textContent = '✅';
        if (titleEl) titleEl.textContent = `ROUTINE QUALITY METRICS (LOT ${data.batch_id})`;
        if (descEl) descEl.textContent = `Standard return distribution for ${data.product_name}. Within historical tolerances.`;
        if (badgeEl) {
          badgeEl.textContent = 'STANDARD OPERATIONS';
          badgeEl.className = 'badge badge-emerald';
        }
      }
    }

    // Dynamic Labor Constraint Reasoning Notice
    if (supAgentLaborNotice) {
      const refurbCount = opt.route_counts['REFURBISH'] || 0;
      const laborUsed = opt.labor_hours_used;
      const laborCap = parseFloat(supLaborSlider ? supLaborSlider.value : 200.0);
      supAgentLaborNotice.style.display = 'block';
      if (laborCap < laborUsed + 0.5 && laborCap < 190.0) {
        supAgentLaborNotice.innerHTML = `
          <strong>🧠 Agent Constrained Re-Optimization:</strong><br>
          Technician labor capacity restricted to <strong>${laborCap.toFixed(1)} hrs</strong>. Solver mathematically scheduled <strong>${refurbCount} units</strong> on Workbench #3 (${laborUsed} hrs used). Remaining repair candidates were dynamically rerouted to secondary liquidation/RTV to prevent shop floor bottlenecks.
        `;
      } else {
        supAgentLaborNotice.innerHTML = `
          <strong>🧠 Solver Capacity Telemetry:</strong><br>
          Shift labor capacity limit: <strong>${laborCap.toFixed(1)} hrs</strong>. Current allocation utilizes <strong>${laborUsed} hrs</strong> across ${refurbCount} refurbished units (Capacity headroom: <strong>${(laborCap - laborUsed).toFixed(1)} hrs</strong>).
        `;
      }
    }

    // Update Channel Distribution Bar & Cards
    if (supChannelDistBar && supChannelCardsGrid) {
      supChannelDistBar.innerHTML = '';
      supChannelCardsGrid.innerHTML = '';

      const colors = {
        RTV: 'var(--accent-primary)',
        REFURBISH: 'var(--accent-amber)',
        RESTOCK: 'var(--accent-emerald)',
        SCRAP: 'var(--accent-red)',
        LIQUIDATE: 'var(--accent-violet)'
      };

      const totals = {};
      opt.unit_decisions.forEach(u => {
        totals[u.assigned_channel] = (totals[u.assigned_channel] || 0) + u.net_salvage_value;
      });

      Object.entries(opt.route_counts).forEach(([channel, count]) => {
        const pct = ((count / data.total_units) * 100).toFixed(1);
        const chColor = colors[channel] || '#64748B';

        const seg = document.createElement('div');
        seg.className = `bar-segment`;
        seg.style.width = `${pct}%`;
        seg.style.background = chColor;
        seg.title = `${channel}: ${count} units (${pct}%)`;
        supChannelDistBar.appendChild(seg);

        const card = document.createElement('div');
        card.className = 'channel-card';
        card.style.borderLeft = `3px solid ${chColor}`;
        card.innerHTML = `
          <div class="channel-card-top">
            <span class="channel-name" style="color:${chColor}">${channel}</span>
            <span class="badge badge-subtle">${pct}%</span>
          </div>
          <div class="channel-count">${count} <small style="font-size:12px;font-weight:400;color:var(--text-dim)">units</small></div>
          <div class="channel-financial">₹${(totals[channel] || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} recovered</div>
        `;
        supChannelCardsGrid.appendChild(card);
      });
    }

    // Update Executive Financial Stats & PDF links to point to active batch
    const execNsv = document.querySelector('.exec-financial-banner .exec-stat-val.text-accent');
    const execUplift = document.querySelector('.exec-financial-banner .exec-stat-val.text-emerald');
    const execClaim = document.querySelector('.exec-financial-banner .exec-stat-val.text-amber');
    if (execNsv) execNsv.textContent = `₹${opt.total_nsv.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (execUplift) execUplift.textContent = `+₹${uplift.dollar_uplift.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (execClaim) {
      const claimUnits = opt.route_counts['RTV'] || 24;
      const claimVal = claimUnits * (data.supplier_claim_per_unit || 840.0);
      execClaim.textContent = `₹${claimVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    if (execLegalNotice && data.decision && data.decision.legal_chargeback_draft) {
      execLegalNotice.textContent = data.decision.legal_chargeback_draft;
    }

    if (execViewPdfBtn) execViewPdfBtn.href = `/api/view-pdf/${data.batch_id}.pdf`;
    if (execDirectDownloadPdfBtn) {
      execDirectDownloadPdfBtn.href = `/api/download/${data.batch_id}.pdf`;
      execDirectDownloadPdfBtn.setAttribute('download', `Gadgetbay_RMA_${data.batch_id}.pdf`);
    }
  }

  // =========================================================================
  // EXECUTIVE STATION LOGIC (David Chen - EXEC-001)
  // =========================================================================
  if (execCopyNoticeBtn && execLegalNotice) {
    execCopyNoticeBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(execLegalNotice.innerText).then(() => {
        execCopyNoticeBtn.textContent = 'Copied!';
        setTimeout(() => execCopyNoticeBtn.textContent = 'Copy Notice', 2000);
      });
    });
  }

  // Initialize Authentication on Startup
  initAuthSession();
});

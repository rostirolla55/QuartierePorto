// ===========================================
// CONFIGURAZIONE E COSTANTI GLOBALI
// ===========================================
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
import { getAuth, signInAnonymously, signInWithCustomToken, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
import { getFirestore, doc, onSnapshot, collection, addDoc, serverTimestamp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";

const APP_VERSION = '1.2.36 - Lingue (Supporta button, img e tag a)';
const LANGUAGES = ['it', 'en', 'fr', 'es'];
const LAST_LANG_KEY = 'Quadrilatero_lastLang';
let currentLang = 'it';
console.log(`Version : ${APP_VERSION}`);

window.navTitles = {};
window.allData = {};

// Elementi DOM Globali
let nearbyPoiButton;
let nearbyMenuPlaceholder;

// Configurazione Firebase
const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';
const firebaseConfig = typeof __firebase_config !== 'undefined' ? JSON.parse(__firebase_config) : {};
let db, auth, currentUserId = null, isAuthReady = false;

// ===========================================
// DATI: POI GPS
// ===========================================
const POIS_LOCATIONS = [
    { id: 'manifattura', lat: 44.4989321, lon: 11.336618, distanceThreshold: 50, categoria: 'edificio' },
    { id: 'pittoricarracci', lat: 44.498485, lon: 11.332663, distanceThreshold: 50, categoria: 'arte' },
    { id: 'cavaticcio', lat: 44.500207, lon: 11.338076, distanceThreshold: 50, categoria: 'edificio' },
    { id: 'bsmariamaggiore', lat: 44.498118, lon: 11.341923, distanceThreshold: 50, categoria: 'edificio' },
    { id: 'graziaxx', lat: 44.500594, lon: 11.340758, distanceThreshold: 50, categoria: 'esterno' },
    { id: 'pugliole', lat: 44.500071, lon: 11.339805, distanceThreshold: 50, categoria: 'esterno' },
    { id: 'carracci', lat: 44.499912, lon: 11.34041, distanceThreshold: 50, categoria: 'edificio' },
    { id: 'lastre', lat: 44.499312, lon: 11.340714, distanceThreshold: 50, categoria: 'esterno' },
    { id: 'chiesasbene', lat: 44.5019, lon: 11.343843, distanceThreshold: 120, categoria: 'edificio' },
    { id: 'santuariopioggia', lat: 44.498891, lon: 11.342148, distanceThreshold: 120, categoria: 'edificio' },
    { id: 'pioggia1', lat: 44.498921, lon: 11.341923, distanceThreshold: 120, categoria: 'quadro' },
    { id: 'pioggia2', lat: 44.499023, lon: 11.34176, distanceThreshold: 120, categoria: 'statua' },
    { id: 'pioggia3', lat: 44.499023, lon: 11.34176, distanceThreshold: 120, categoria: 'quadro' },
    { id: 'chiesasancarlo', lat: 44.501295, lon: 11.34085, distanceThreshold: 120, categoria: 'edificio' },
    { id: 'stabile_legno_vandini', lat: 44.502054, lon: 11.338546, distanceThreshold: 120, categoria: 'edificio' },
    { id: 'edicola_votiva', lat: 44.499137, lon: 11.341797, distanceThreshold: 120, categoria: 'edificio' }
];

// ===========================================
// UTILITY
// ===========================================
const getCurrentPageId = () => {
    const urlPath = window.location.pathname;
    let fileName = urlPath.substring(urlPath.lastIndexOf('/') + 1);
    if (!fileName || fileName.startsWith('index')) return 'home';
    return fileName.split('-')[0].replace('.html', '').toLowerCase();
};

const updateText = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val || ''; };
const updateHTML = (id, val) => { const el = document.getElementById(id); if (el) el.innerHTML = val || ''; };
const isFilePath = (val) => typeof val === 'string' && (val.endsWith('.html') || val.endsWith('.txt'));

async function fetchFileContent(path) {
    try {
        const res = await fetch(path);
        if (!res.ok) return `[Errore caricamento: ${path}]`;
        return await res.text();
    } catch (e) { return `[Contenuto non disponibile]`; }
}

// ===========================================
// LOGICA FIREBASE
// ===========================================
function setupDrinListener() {
    if (!db) return;
    const drinDocRef = doc(db, 'artifacts', appId, 'public', 'data', 'commands', 'drin');
    onSnapshot(drinDocRef, (snap) => {
        if (snap.exists()) {
            const audio = new Audio('Assets/Audio/drin.mp3');
            audio.play().catch(() => { });
        }
    });
}

async function logAccess(pageId, lang) {
    if (!db || !currentUserId) return;
    try {
        const logsCol = collection(db, 'artifacts', appId, 'public', 'data', 'access_logs');
        await addDoc(logsCol, { pageId, lang, userId: currentUserId, timestamp: serverTimestamp() });
    } catch (e) { console.error("Log error:", e); }
}

// ===========================================
// CARICAMENTO CONTENUTI
// ===========================================
async function loadContent(lang) {
    document.documentElement.lang = lang;
    const pageId = getCurrentPageId();

    try {
        const response = await fetch(`data/translations/${lang}/texts.json`);
        const data = await response.json();
        window.allData = data; // <--- AGGIUNGI QUESTA RIGA per aggiornare i titoli globali
        const pageData = data[pageId];

        if (!pageData) {
            updateText('pageTitle', "Contenuto non trovato");
            document.body.classList.add('content-loaded');
            return;
        }

        updateText('pageTitle', pageData.pageTitle);
        updateHTML('headerTitle', pageData.pageTitle);

        const headImg = document.getElementById('headImage');
        if (headImg && pageData.headImage) {
            headImg.src = `public/images/${pageData.headImage}`;
            headImg.style.display = 'block';
        }

        const textKeys = ['mainText', 'mainText1', 'mainText2', 'mainText3', 'mainText4', 'mainText5'];
        for (const key of textKeys) {
            let content = pageData[key];
            if (isFilePath(content)) {
                content = await fetchFileContent(`text_files/${content}`);
            }
            updateHTML(key, content);
        }

        for (let i = 1; i <= 5; i++) {
            const imgEl = document.getElementById(`pageImage${i}`);
            const src = pageData[`imageSource${i}`];
            if (imgEl) {
                if (src) {
                    imgEl.src = `Assets/images/${src}`;
                    imgEl.style.display = 'block';
                } else {
                    imgEl.style.display = 'none';
                }
            }
        }
        // AGGIORNAMENTO INFORMAZIONI SULLA FONTE E DATA
        if (pageData.sourceText) {
            updateHTML('infoSource', `Fonte: ${pageData.sourceText}`);
        }
        if (pageData.creationDate) {
            updateHTML('infoCreatedDate', `Data Creazione: ${pageData.creationDate}`);
        }
        if (pageData.lastUpdate) {
            updateHTML('infoUpdatedDate', `Ultimo Aggiornamento: ${pageData.lastUpdate}`);
        }

        const audioPlayer = document.getElementById('audioPlayer');
        const playBtn = document.getElementById('playAudio');
        if (audioPlayer && playBtn && pageData.audioSource) {
            audioPlayer.src = `Assets/Audio/${pageData.audioSource}`;
            playBtn.textContent = pageData.playAudioButton || "Play";
            playBtn.dataset.playText = pageData.playAudioButton;
            playBtn.dataset.pauseText = pageData.pauseAudioButton;
            playBtn.style.display = 'block';
        }

        updateNavigation(data.nav, lang);
        startGeolocation(data);
        document.body.classList.add('content-loaded');
        if (isAuthReady) logAccess(pageId, lang);

    } catch (e) {
        console.error("Errore caricamento:", e);
        document.body.classList.add('content-loaded');
    }
}

function updateNavigation(navData, lang) {
    if (!navData) return;
    const langSuffix = lang === 'it' ? '-it' : `-${lang}`;

    const navLinksData = [
    { id: 'navHome', key: 'navHome', base: 'index' },
    { id: 'navManifattura', key: 'navManifattura', base: 'manifattura' },
    { id: 'navPittoricarracci', key: 'navPittoricarracci', base: 'pittoricarracci' },
    { id: 'navCavaticcio', key: 'navCavaticcio', base: 'cavaticcio' },
    { id: 'navBsmariamaggiore', key: 'navBsmariamaggiore', base: 'bsmariamaggiore' },
    { id: 'navGraziaxx', key: 'navGraziaxx', base: 'graziaxx' },
    { id: 'navPugliole', key: 'navPugliole', base: 'pugliole' },
    { id: 'navCarracci', key: 'navCarracci', base: 'carracci' },
    { id: 'navLastre', key: 'navLastre', base: 'lastre' },
    { id: 'navChiesasbene', key: 'navChiesasbene', base: 'chiesasbene' },
    { id: 'navSantuariopioggia', key: 'navSantuariopioggia', base: 'santuariopioggia' },
    { id: 'navPioggia1', key: 'navPioggia1', base: 'pioggia1' },
    { id: 'navPioggia2', key: 'navPioggia2', base: 'pioggia2' },
    { id: 'navPioggia3', key: 'navPioggia3', base: 'pioggia3' },
    { id: 'navChiesasancarlo', key: 'navChiesasancarlo', base: 'chiesasancarlo' },
    { id: 'navStabilevandini', key: 'navStabilevandini', base: 'stabile_legno_vandini' },
    { id: 'navEdicolavotiva', key: 'navEdicolavotiva', base: 'edicola_votiva' }
];

    navLinksData.forEach(l => {
        const el = document.getElementById(l.id);
        if (el) {
            el.href = `${l.base}${langSuffix}.html`;
            // const poiInfo = POIS_LOCATIONS.find(p => p.id === l.base);
            const poiInfo = POIS_LOCATIONS.find(p => p.id.toLowerCase() === l.base.toLowerCase());
            const simbolo = (poiInfo && window.getSimboloCategoria) 
                            ? window.getSimboloCategoria(poiInfo.categoria) 
                            : '📍';
            // CERCA TITOLO: 
            // 1. Prova nel navData (es. navManifattura)
            // 2. Prova nel titolo della pagina (pageTitle)
            // 3. Fallback sull'ID pulito
            const titoloTradotto = navData[l.key] || 
                                   (window.allData[l.base] && window.allData[l.base].pageTitle) || 
                                   l.base;

            el.innerHTML = `<span class="menu-icon">${simbolo}</span> ${titoloTradotto}`;
            // console.log(`DEBUG : <span>${simbolo}</span> ${titoloTradotto} `);
            // ---------------------
        }
    });
}

// ===========================================
// GEOLOCALIZZAZIONE
// ===========================================
const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371e3;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return R * (2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)));
};

function startGeolocation(allData) {
    if (!navigator.geolocation) return;

    const geoOptions = { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 };

    navigator.geolocation.watchPosition((pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;

        if (nearbyPoiButton) {
            nearbyPoiButton.style.display = 'block';
        }

        let menuHtml = '<ul class="poi-links">';
        let found = false;

        POIS_LOCATIONS.forEach(poi => {
            const dist = calculateDistance(lat, lon, poi.lat, poi.lon);
            if (dist <= poi.distanceThreshold) {
                const title = (allData[poi.id] && allData[poi.id].pageTitle) ? allData[poi.id].pageTitle : poi.id;
                const simbolo = (typeof window.getSimboloCategoria === 'function') ? window.getSimboloCategoria(poi.categoria) : '📍';
                const suffix = currentLang === 'it' ? '-it' : `-${currentLang}`;
                menuHtml += `<li>
                    <a href="${poi.id}${suffix}.html">
                        <span>${simbolo}</span> ${title} (${dist.toFixed(0)}m)
                    </a>
                </li>`; 
                found = true;
            }
        });

        menuHtml += '</ul>';
        if (!found) {
            let noPoiMessage;
            switch (currentLang) {
                case 'es': noPoiMessage = `No se encontraron puntos de interés dentro 50 m. <br><br>   Pulse de nuevo el botón verde para cerrar el menú.`; break;
                case 'en': noPoiMessage = `No Points of Interest found within 50 m. <br><br>   Press the green button again to close the menu.`; break;
                case 'fr': noPoiMessage = `Aucun point d'interet trouve dans les environs 50 m. <br><br>  Appuyez à nouveau sur le bouton vert pour fermer le menu.`; break;
                case 'it':
                default: noPoiMessage = `Nessun Punto di Interesse trovato entro 50 m.<br><br> Premere di nuovo il bottone verde per chiudere la lista.`; break;
            }
            // Uso colore rosso per i test
            menuHtml = `<div style="color:red; padding: 20px; text-align: center; font-size: 1em;">${noPoiMessage}</div>`;

            //      menuHtml = '<div style="padding:20px;text-align:center;">Nessun punto vicino</div>'

        };
        if (nearbyMenuPlaceholder) nearbyMenuPlaceholder.innerHTML = menuHtml;

    }, (err) => {
        console.warn("Geolocation error:", err.message);
    }, geoOptions);
}

// ===========================================
// INIZIALIZZAZIONE EVENTI (CON FIX CHIUSURA MENU)
// ===========================================
function initEvents() {
    const toggle = document.querySelector('.menu-toggle');
    const nav = document.getElementById('navBarMain');

    // Funzioni helper per la chiusura
    const closeMainMenu = () => {
        if (toggle && nav) {
            toggle.classList.remove('active');
            nav.classList.remove('active');
            document.body.classList.remove('menu-open');
        }
    };

    const closePoiMenu = () => {
        if (nearbyMenuPlaceholder) {
            nearbyMenuPlaceholder.classList.remove('poi-active');
            document.body.classList.remove('menu-open');
        }
    };

    if (toggle && nav) {
        toggle.onclick = (e) => {
            e.stopPropagation();
            // Se apro il menu principale, chiudo quello dei POI
            closePoiMenu();

            toggle.classList.toggle('active');
            nav.classList.toggle('active');
            document.body.classList.toggle('menu-open');
        };
    }

    if (nearbyPoiButton && nearbyMenuPlaceholder) {
        nearbyPoiButton.onclick = (e) => {
            e.stopPropagation();
            // Se apro il menu dei POI, chiudo quello principale
            closeMainMenu();

            nearbyMenuPlaceholder.classList.toggle('poi-active');
            document.body.classList.toggle('menu-open');
        };
    }

    // Audio
    const playBtn = document.getElementById('playAudio');
    const player = document.getElementById('audioPlayer');
    if (playBtn && player) {
        playBtn.onclick = () => {
            if (player.paused) {
                player.play();
                playBtn.textContent = playBtn.dataset.pauseText;
                playBtn.classList.replace('play-style', 'pause-style');
            } else {
                player.pause();
                playBtn.textContent = playBtn.dataset.playText;
                playBtn.classList.replace('pause-style', 'play-style');
            }
        };
        player.onended = () => {
            playBtn.textContent = playBtn.dataset.playText;
            playBtn.classList.replace('pause-style', 'play-style');
        };
    }


    // Lingue (Supporta button, img e tag 'a' anche nidificati)
    document.querySelectorAll('.language-selector button, .language-selector img, .language-selector a').forEach(el => {
        el.onclick = (e) => {
            // Cerca data-lang sull'elemento cliccato o sul genitore più vicino
            // (Fondamentale se clicchi sull'<img> dentro un <a>)
            const target = e.target.closest('[data-lang]');
            const lang = target ? target.dataset.lang : null;

            if (!lang) return;

            // Blocca il link HTML per gestire il cambio via JS
            e.preventDefault();
            e.stopPropagation();

            console.log("Cambio lingua forzato a:", lang);

            localStorage.setItem(LAST_LANG_KEY, lang);
            const pageId = getCurrentPageId();
            const base = (pageId === 'home' || pageId === 'index') ? 'index' : pageId;

            // Reindirizzamento esplicito
            window.location.href = `${base}-${lang}.html`;
        };
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const savedLang = localStorage.getItem(LAST_LANG_KEY);
    const urlLang = location.pathname.match(/-([a-z]{2})\.html/);
    currentLang = (urlLang && urlLang[1]) || savedLang || 'it';

    nearbyPoiButton = document.getElementById('nearbyPoiButton');
    nearbyMenuPlaceholder = document.getElementById('nearbyMenuPlaceholder');

    initEvents();
    loadContent(currentLang);

    if (firebaseConfig.apiKey) {
        const app = initializeApp(firebaseConfig);
        db = getFirestore(app);
        auth = getAuth(app);

        onAuthStateChanged(auth, (user) => {
            if (user) {
                currentUserId = user.uid;
                isAuthReady = true;
                setupDrinListener();
                logAccess(getCurrentPageId(), currentLang);
            } else {
                signInAnonymously(auth);
            }
        });
    }
});
// --- ESPORTAZIONE GLOBALE ---
window.getSimboloCategoria = function(categoria) {
    // 1. Gestione Benvenuto o valori nulli [cite: 49-51]
    if (!categoria || categoria === "" || categoria === "undefined") {
        return '📍'; 
    }

    // 2. Pulizia assoluta del valore ricevuto
    const catClean = categoria.toString().toLowerCase().trim();

    // 3. Mappatura completa basata sui tuoi POIS_LOCATIONS [cite: 30-43]
    const simboli = {
        'edificio': '🏛️',
        'esterno': '🌳',
        'chiesa': '⛪',
        'quadro': '🎨',
        'statua': '🗿',
        'arte': '🎨',
        'monumento': '🏛️'
    };

    // 4. Fallback: se la categoria non è in lista, usa il pin rosso 
    // Invece di restituire nulla (vuoto), restituiamo sempre un carattere visibile.
    return simboli[catClean] || '📍';
};  

window.POIS_LOCATIONS = POIS_LOCATIONS;
// Aggiungi questa riga per esportare i titoli tradotti
// Inizializziamo l'oggetto se non esiste ancora
if (!window.navTitles) window.navTitles = {};

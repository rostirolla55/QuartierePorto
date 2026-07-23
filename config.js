/**
 * config.js
 * Configurazione globale per la navigazione e i POI
 */

window.APP_DATA = {
    "navigation": [
        { "id": "navHome", "key": "navHome", "base": "index" },
        { "id": "navCarracci", "key": "navCarracci", "base": "carracci" },
        { "id": "navLastre", "key": "navLastre", "base": "lastre" },
        { "id": "navPugliole", "key": "navPugliole", "base": "pugliole" },
        { "id": "navGraziaxx", "key": "navGraziaxx", "base": "graziaxx" },
        { "id": "navChiesasbene", "key": "navChiesasbene", "base": "chiesasbene" },
        { "id": "navSantuariopioggia", "key": "navSantuariopioggia", "base": "santuariopioggia" },
        { "id": "navPioggia1", "key": "navPioggia1", "base": "pioggia1" },
        { "id": "navPioggia2", "key": "navPioggia2", "base": "pioggia2" },
        { "id": "navPioggia3", "key": "navPioggia3", "base": "pioggia3" },
        { "id": "navManifattura", "key": "navManifattura", "base": "manifattura" },
        { "id": "navPittoricarracci", "key": "navPittoricarracci", "base": "pittoricarracci" },
        { "id": "navCavaticcio", "key": "navCavaticcio", "base": "cavaticcio" },
        { "id": "navbsmariamaggiore", "key": "navbsmariamaggiore", "base": "bsmariamaggiore" }
    ],
    "poisLocations": [
        { "id": "bsmariamaggiore", "lat": 44.49806368372069, "lon": 11.34192628931731, "range": 50 },
        { "id": "carracci", "lat": 44.4999972222222, "lon": 11.3403888888889, "range": 50 },
        { "id": "cavaticcio", "lat": 44.50018, "lon": 11.33807, "range": 50 },
        { "id": "santuariopioggia", "lat": 44.49891, "lon": 11.342241, "range": 120 },
        { "id": "chiesasbene", "lat": 44.501514, "lon": 11.343557, "range": 120 },
        { "id": "graziaxx", "lat": 44.5006638888889, "lon": 11.3407694444444, "range": 50 },
        { "id": "lastre", "lat": 44.49925278, "lon": 11.34074444, "range": 50 },
        { "id": "manifattura", "lat": 44.49891, "lon": 11.342241, "range": 50 },
        { "id": "pioggia1", "lat": 44.49891, "lon": 11.342241, "range": 120 },
        { "id": "pioggia2", "lat": 44.49891, "lon": 11.342241, "range": 120 },
        { "id": "pioggia3", "lat": 44.49891, "lon": 11.342241, "range": 120 },
        { "id": "pittoricarracci", "lat": 44.50085, "lon": 11.3361, "range": 50 },
        { "id": "pugliole", "lat": 44.5001944444444, "lon": 11.3399861111111, "range": 50 }
    ]
};

window.CONFIG = window.APP_DATA;

window.firebaseConfig = {
    projectId: "quadrilatero",
    apiKey: "dummy-key"
};

console.log("✅ Configurazione caricata. POI disponibili:", window.APP_DATA.poisLocations.length);
// ... (cerca la funzione updateMenu e sostituiscila con questa)
function updateMenu(menuData) {
    const navList = document.querySelector('#navBarMain .nav-bar-content ul');
    if (!navList) return;

    navList.innerHTML = '';

    // Gestione flessibile sia di array diretti che di oggetti { items: [] }
    const items = Array.isArray(menuData) ? menuData : (menuData.items || []);

    items.forEach(item => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        
        // CORREZIONE: Cerca il testo in più campi possibili
        const text = item.text || item.title || item.pageTitle || 'Link';
        
        a.href = item.href || '#';
        a.textContent = text;
        
        // Gestione click per mantenere la lingua
        a.onclick = (e) => {
            if (a.href.includes('#')) return;
            // Se il link non ha già il suffisso lingua, potresti aggiungerlo qui
        };

        li.appendChild(a);
        navList.appendChild(li);
    });
}
let sortDirection = {}; // Oggetto per memorizzare la direzione dell'ordinamento per ogni tabella

// Formatta l'intestazione della colonna convertendo snake_case in Title Case
function formatColumnHeader(header) {
 return header.split('_')
	 .map(word => word.charAt(0).toUpperCase() + word.slice(1))
	 .join(' ');
}

// Funzione per ordinare la tabella
function sortTable(tableId, columnIndex) {
 const table = document.querySelector(`#${tableId} table`);
 const tbody = table.querySelector('tbody');
 const rows = Array.from(tbody.querySelectorAll('tr'));
 
 // Inverte la direzione dell'ordinamento
 sortDirection[tableId] = !sortDirection[tableId];

 // Ordina le righe
 rows.sort((a, b) => {
	 const aValue = Number(a.cells[columnIndex].textContent);
	 const bValue = Number(b.cells[columnIndex].textContent);
	 
	 return sortDirection[tableId] ? aValue - bValue : bValue - aValue;
 });

 // Pulisce e aggiunge le righe ordinate
 tbody.innerHTML = '';
 rows.forEach(row => tbody.appendChild(row));

 // Aggiorna l'indicatore di ordinamento nell'intestazione
 const th = table.querySelector(`th:nth-child(${columnIndex + 1})`);
 const arrow = sortDirection[tableId] ? '↑' : '↓';
 th.textContent = `${formatColumnHeader(th.dataset.originalHeader)} ${arrow}`;
}

// Crea una nuova tabella dai dati
function createTable(data, containerId) {
	 if (!data || data.length === 0) return;
	 
	 const container = document.getElementById(containerId);
	 
	 // Crea un wrapper per la tabella scrollabile
	 const wrapper = document.createElement('div');
	 wrapper.className = 'table-wrapper';
	 
	 const table = document.createElement('table');
	 const headers = Object.keys(data[0]);
	 
	 // Crea intestazione e corpo della tabella
	 const thead = document.createElement('thead');
	 const tbody = document.createElement('tbody');
	 table.appendChild(thead);
	 table.appendChild(tbody);
	 
	 // Crea riga di intestazione
	 const headerRow = document.createElement('tr');
	 headers.forEach((header, index) => {
		 const th = document.createElement('th');
		 th.dataset.originalHeader = header;
		 th.textContent = formatColumnHeader(header);
		 
		 // Aggiunge funzionalità di ordinamento alla prima colonna
		 if (index === 0) {
			 th.style.cursor = 'pointer';
			 th.onclick = () => sortTable(containerId, 0);
			 th.title = 'Click per ordinare';
		 }
		 
		 headerRow.appendChild(th);
	 });
	 thead.appendChild(headerRow);

	 // Crea righe dei dati
	 data.forEach(row => {
		 const tr = document.createElement('tr');
		 headers.forEach(header => {
			 const td = document.createElement('td');
			 td.textContent = row[header] || '';
			 // Aggiunge tooltip al passaggio del mouse sul testo troncato
			 td.title = row[header] || '';
			 tr.appendChild(td);
		 });
		 tbody.appendChild(tr);
	 });

	 wrapper.appendChild(table);
	 container.innerHTML = '';
	 container.appendChild(wrapper);
 }

 // Rimuove l'indicatore di scorrimento quando l'utente ha scrollato
 document.addEventListener('DOMContentLoaded', function() {
	 document.querySelectorAll('.table-wrapper').forEach(wrapper => {
		 wrapper.addEventListener('scroll', function() {
			 this.classList.add('scrolled');
			 this.style.setProperty('--after-display', 'none');
		 });
	 });
 });

// Aggiunge CSS per le intestazioni ordinabili
const style = document.createElement('style');
style.textContent = `
 th[onclick] {
	 position: relative;
	 background-color: #f0f0f0;
 }
 th[onclick]:hover {
	 background-color: #e0e0e0;
 }
`;
document.head.appendChild(style);

// Funzione asincrona per recuperare i dati
async function fetchData() {
    try {
        const data = {
            0: await fetch('../data/0.json').then(response => response.json()),
            1: await fetch('../data/1.json').then(response => response.json()),
            2: await fetch('../data/2.json').then(response => response.json()),
            3: await fetch('../data/3.json').then(response => response.json()),
            4: await fetch('../data/4.json').then(response => response.json())
        };
        
        //Inserisci il testo generato dall'ai
        document.getElementById('aiContent').textContent = data['4'] || '';

        //Crea le varie tabelle
        if (data['0']) createTable(data['0'], 'assignedTable');
        if (data['1']) createTable(data['1'], 'tenDaysTable');
        if (data['2']) createTable(data['2'], 'shippedTable');
        if (data['3']) createTable(data['3'], 'toRetrieveTable');

    } catch (error) {
        console.error('Errore nel recupero dei dati:', error);
        alert('Errore nel recupero dei dati: ' + error.message);
    }
}

// Carica i dati iniziali quando il DOM è pronto
document.addEventListener('DOMContentLoaded', fetchData);
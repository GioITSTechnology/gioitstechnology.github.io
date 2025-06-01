# API Manutenzione Correttiva - Ingegneria Clinica

## 📋 Descrizione
Questo progetto implementa un'API RESTful in C per la gestione delle richieste di manutenzione correttiva nell'ambito dell'ingegneria clinica. L'applicazione si interfaccia con un database SQLite e genera risposte in formato JSON.

## 🔧 Prerequisiti
- Compilatore C (GCC raccomandato)
- SQLite3
- Sistema operativo: Linux/Unix

## 📚 Dipendenze
Il progetto utilizza le seguenti librerie:

- **SQLite3** - Database SQL embedded
  - [Repository SQLite](https://github.com/sqlite/sqlite)
  - Installazione: `sudo apt-get install libsqlite3-dev`

- **Ulfius** - Framework HTTP per C
  - [Repository Ulfius](https://github.com/babelouest/ulfius)
  - Installazione: `sudo apt-get install libulfius-dev`

- **cJSON** - Libreria per la manipolazione JSON in C
  - [Repository cJSON](https://github.com/DaveGamble/cJSON)
  - Installazione: `sudo apt-get install libcjson-dev`

## 💻 Utilizzo
```bash
# Avvia il server
./simple_query
```

L'API sarà disponibile all'indirizzo `http://localhost:1234`
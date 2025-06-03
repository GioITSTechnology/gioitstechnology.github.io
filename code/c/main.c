#include <sqlite3.h>
#include <stdio.h>
#include <string.h>
#include <ulfius.h>
#include "cJSON.h"

#define PORT 1234

static int callback(void *, int, char **, char **);

void prepare_query(char *query, int number);

int execute_query_and_store(sqlite3 *db, const char *query, int query_index);

char *create_response(int num);

// As you can see, ai answers have been removed. This is intentional to make the code more readable.
// AI answers can still be seen in pw.html

const char *ai_sonia = "";

const char *ai_luca = "";

const char *ai_lorenzo = ""

const char *ai_michele = "";

const char *ai_fabio = "";

// The users numbers are the actual ids of the users in SCB.db
const int users[] = {390, 219,34,179,17};

//Main queries
const char *main_query = "DROP VIEW if exists big_view;"
        " CREATE VIEW big_view AS SELECT Chiamate.id_chiamata, MAX(Azioni.data_fine_azione) AS data_fine_azione, Azioni.note_azione, Utenti.nome_utente, Chiamate.id_utente as utente_assegnato, Azioni.id_utente, Chiamate.descrizione_chiamata, Tipologia_azioni.nome_tipologia_azione, Azioni.id_tipologia_azione, Chiamate.id_apparecchiatura, Apparecchiature.descrizione_apparecchiatura, Tipologia_apparecchiature.nome_tipologia_apparecchiatura, Produttori.nome_produttore, Fornitori.ragione_sociale_fornitore, Centri_costo.nome_centro_costo, Centri_costo.ubicazione_centro_costo FROM Azioni JOIN Chiamate on Azioni.id_chiamata = Chiamate.id_chiamata JOIN Utenti on Azioni.id_utente = Utenti.id_utente JOIN Apparecchiature on Chiamate.id_apparecchiatura = Apparecchiature.id_apparecchiatura JOIN Tipologia_apparecchiature on Tipologia_apparecchiature.id_tipologia_apparecchiatura = Apparecchiature.id_tipologia_apparecchiatura JOIN Produttori on Produttori.id_produttore = Apparecchiature.id_produttore JOIN Fornitori on Fornitori.id_fornitore = Apparecchiature.id_fornitore JOIN Centri_costo on Centri_costo.id_centro_costo = Apparecchiature.id_centro_costo JOIN Tipologia_azioni on Tipologia_azioni.id_tipologia_azione = Azioni.id_tipologia_azione WHERE Chiamate.id_stato_chiamata = 1 GROUP BY Azioni.id_chiamata ORDER BY data_fine_azione DESC;";

char assigned_without_actions[] =
        "SELECT Chiamate.id_chiamata, datetime(Chiamate.data_apertura_chiamata, 'unixepoch') as data_apertura_chiamata, Chiamate.descrizione_chiamata, Apparecchiature.descrizione_apparecchiatura, Tipologia_apparecchiature.nome_tipologia_apparecchiatura, Produttori.nome_produttore, Centri_costo.nome_centro_costo, Centri_costo.ubicazione_centro_costo FROM Chiamate LEFT JOIN Azioni on Azioni.id_chiamata = Chiamate.id_chiamata JOIN Utenti on Chiamate.id_utente = Utenti.id_utente JOIN Apparecchiature on Chiamate.id_apparecchiatura = Apparecchiature.id_apparecchiatura JOIN Tipologia_apparecchiature on Tipologia_apparecchiature.id_tipologia_apparecchiatura = Apparecchiature.id_tipologia_apparecchiatura JOIN Produttori on Produttori.id_produttore = Apparecchiature.id_produttore JOIN Fornitori on Fornitori.id_fornitore = Apparecchiature.id_fornitore JOIN Centri_costo on Centri_costo.id_centro_costo = Apparecchiature.id_centro_costo WHERE Chiamate.id_stato_chiamata = 1 AND Azioni.id_azione is NULL AND Chiamate.id_utente =    ;";

char ten_days_reminder[] =
        "SELECT ((unixepoch('2025-03-03 00:00:00') - data_fine_azione)/86400) as giorni_trascorsi, id_chiamata, note_azione, nome_tipologia_apparecchiatura, descrizione_apparecchiatura, nome_produttore, ragione_sociale_fornitore FROM big_view WHERE id_tipologia_azione in (4,5) and giorni_trascorsi > 10 and utente_assegnato=   ;";

char shipped[] =
    "SELECT datetime(data_fine_azione, 'unixepoch') as data_spedizione, id_chiamata, id_apparecchiatura, nome_tipologia_apparecchiatura,descrizione_apparecchiatura, nome_produttore from big_view where id_tipologia_azione = 10 and utente_assegnato=   ;";

char to_retrieve[] =
        "SELECT id_chiamata, id_apparecchiatura, nome_tipologia_apparecchiatura,descrizione_apparecchiatura, nome_produttore from big_view where id_tipologia_azione = 9 and utente_assegnato=   ;";


cJSON *main_object = NULL;
cJSON *current_array = NULL;



// This is to handle CORS headers
void add_cors_headers(struct _u_response *response) {
    u_map_put(response->map_header, "Access-Control-Allow-Origin", "*");
    u_map_put(response->map_header, "Access-Control-Allow-Methods", "GET, OPTIONS");
    u_map_put(response->map_header, "Access-Control-Allow-Headers", "Content-Type");
    u_map_put(response->map_header, "Access-Control-Max-Age", "3600");
}

// This is to handle OPTIONS requests
int callback_options(const struct _u_request *request, struct _u_response *response, void *user_data) {
    add_cors_headers(response);
    return U_CALLBACK_COMPLETE;
}

// Function to send the JSON 
int give_json(const struct _u_request *request, struct _u_response *response, void *user_data) {
    // Add CORS headers
    add_cors_headers(response);

    // Get the full URL
    const char *url = request->http_url;
    printf("Full URL: %s\n", url); // Debug print

    // Skip the leading slash
    if (url[0] == '/') {
        url++;
    }

    // Check if the input is a valid number
    char *endptr;
    long number = strtol(url, &endptr, 10);

    if (*endptr == '\0') {
        // Valid number
        if ((number < 0) || (number > (sizeof(users)/sizeof(*users)-1))) {
            ulfius_set_string_body_response(response, 400, "User not found");
            return U_CALLBACK_CONTINUE;
        }
        char *json_response = create_response(users[(int) number]);
        if (json_response) {
            printf("Valid number: %ld\n", number); // Debug print
            // Also set the content type header
            u_map_put(response->map_header, "Content-Type", "application/json");
            ulfius_set_string_body_response(response, 200, json_response);
            free(json_response);
            return U_CALLBACK_CONTINUE;
        }
        else {
            ulfius_set_string_body_response(response, 500, "Internal server error");
        }
    }

    ulfius_set_string_body_response(response, 400, "Invalid input - please provide a number");
    return U_CALLBACK_CONTINUE;
}


int main(void) {
    struct _u_instance instance;

    // Initialize instance
    if (ulfius_init_instance(&instance, PORT, NULL, NULL) != U_OK) {
        fprintf(stderr, "Error initializing ulfius\n");
        return 1;
    }

    // Add endpoints
    ulfius_add_endpoint_by_val(&instance, "OPTIONS", "/*", NULL, 0, &callback_options, NULL);
    ulfius_add_endpoint_by_val(&instance, "GET", "/*", NULL, 0, &give_json, NULL);

    // Start the framework
    if (ulfius_start_framework(&instance) != U_OK) {
        fprintf(stderr, "Error starting framework\n");
        return 1;
    }

    printf("Server is running on port %d\n", PORT);

    // Wait for user input to stop the server
    getchar();

    // Stop the framework
    ulfius_stop_framework(&instance);
    ulfius_clean_instance(&instance);

    return 0;
}

char *create_response(int num) {
    // db_management
    sqlite3 *db;
    char *err_msg = 0;
	
    int rc = sqlite3_open("your/sqlite/location.db", &db);

    if (rc != SQLITE_OK) {
        fprintf(stderr, "Cannot open database: %s\n", sqlite3_errmsg(db));
        sqlite3_close(db);
        return NULL;
    }


    rc = sqlite3_exec(db, main_query, 0, 0, &err_msg);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "Failed to select data\n");
        fprintf(stderr, "SQL error: %s\n", err_msg);

        sqlite3_free(err_msg);
        sqlite3_close(db);

        return NULL;
    }

    main_object = cJSON_CreateObject();
    prepare_query(assigned_without_actions, num);
    prepare_query(ten_days_reminder, num);
    prepare_query(shipped, num);
    prepare_query(to_retrieve, num);

    if (execute_query_and_store(db, assigned_without_actions, 0) != SQLITE_OK ||
        execute_query_and_store(db, ten_days_reminder, 1) != SQLITE_OK ||
        execute_query_and_store(db, shipped, 2) != SQLITE_OK ||
        execute_query_and_store(db, to_retrieve, 3) != SQLITE_OK) {

        cJSON_Delete(main_object);
        sqlite3_close(db);
        return NULL;
        }

    sqlite3_close(db);
    switch (num) {
        case 390:
            cJSON_AddStringToObject(main_object, "4", ai_sonia);
            break;
        case 219:
            cJSON_AddStringToObject(main_object, "4", ai_luca);
            break;
        case 179:
            cJSON_AddStringToObject(main_object, "4", ai_michele);
            break;
        case 17:
            cJSON_AddStringToObject(main_object, "4", ai_fabio);
            break;
        case 34:
            cJSON_AddStringToObject(main_object,"4", ai_lorenzo);
            break;


    }

    char *json_string = cJSON_Print(main_object);
    cJSON_Delete(main_object);
    return json_string;


}


static int callback(void *NotUsed, int argc, char **argv, char **azColName) {
    NotUsed = 0;

    cJSON *row = cJSON_CreateObject();

    for (int i = 0; i < argc; i++) {
        cJSON_AddStringToObject(row, azColName[i], argv[i] ? argv[i] : "null");
    }

    cJSON_AddItemToArray(current_array, row);
    printf("%s\n", cJSON_Print(current_array));
    return 0;
}

void prepare_query(char *query, int number) {
    char number_stringed[3];

    sprintf(number_stringed, "%d", number);
    if (number_stringed[2] == 0) {
        number_stringed[2] = ' ';
    }
    int pos_number = 0;
    int query_length = strlen(query);
    int min = (query_length - 4);
    int max = (query_length - 1);
    for (int i = min; i < max; i++) {
        query[i] = number_stringed[pos_number];
        pos_number++;
    }
}

int execute_query_and_store(sqlite3 *db, const char *query, int query_index) {
    char error_message[256];
    char index_str[16];

    // Create a new array for this query's results
    current_array = cJSON_CreateArray();

    // Execute the query
    int rc = sqlite3_exec(db, query, callback, 0, NULL);
    if (rc != SQLITE_OK) {
        sprintf(error_message, "SQL error: %s\n", sqlite3_errmsg(db));
        return rc;
    }

    // Convert the query index to string
    sprintf(index_str, "%d", query_index);

    // Add the array to the main object with the index as key
    cJSON_AddItemToObject(main_object, index_str, current_array);

    return SQLITE_OK;
}

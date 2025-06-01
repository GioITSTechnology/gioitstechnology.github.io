import requests
from datetime import datetime, timedelta
import xlsxwriter
from dateutil import parser
import re
import os
import glob
import subprocess

# The key retriever script has been removed because it could be used for cookie hijackings
# from key_retriever import *


def user_select(name, users):
    for x in users:
        if name.lower() in x:
            return x
    return None

# This functions get a list of users
def get_list_users(key):
    user_list = []
    url = "https://api.sic.asst-spedalicivili.it/api/user/paged"

    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {key}",
        "content-type": "application/json",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://sic.asst-spedalicivili.it/"
    }

    roles = ["Tecnico SIC", "Referente tecnici SIC", "Direzione SIC"]

    for role in roles:
        payload = {
            "skip": 0,
            "take": 50,
            "orderBy": {"lastName": "ASC"},
            "filters": [{
                "field": "role.name",
                "operator": 2,
                "type": 5,
                "value": [role]
            }]
        }

        try:
            response = requests.post(url, headers=headers, json=payload, verify=True)

            if response.status_code == 200:
                user_list.extend(x["email"] for x in response.json()["items"])
            elif response.status_code == 401:
                print("Authentication failed")
                return None
            else:
                print(f"Request failed with status code: {response.status_code}")
                print("Response:", response.text)
                return None

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

    print("Lista dei tecnici ottenuta correttamente\n")
    return user_list

# This function is to format better certain actions in a maintenance request.
def remove_cc(text):
    text = ' '.join(text.replace('\n', ' ').split())
    if "CC:" in text:
        return text.split("CC:")[0].strip() + "..."
    return text.strip()

# This function get all the ids of the maintenances of a certain technician (the one specified in "name") made after a certain date.
def get_list_maintenance(key, name, date, start=0):
    id_status_list = []

    url = "https://api.sic.asst-spedalicivili.it/api/corrective-maintenance/pagedview/3"

    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": "Bearer " + key,
        "content-type": "application/json",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://sic.asst-spedalicivili.it/"
    }

    payload = {
        "skip": start,
        "take": 200,
        "orderBy": {
            "callOpeningDate": "DESC"
        },
        "filters": [
            {"field": "technicianUser.email", "operator": 2, "type": 6, "value": [name]},
            {"field": "callOpeningDate", "operator": 6, "type": 2, "value": [date]}
        ]
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=True
        )
        if response.status_code == 200:
            data = response.json()
            if data["totalCount"] == 0:
                return None
            for x in data["items"]:
                id_status_list.append([x["id"], x["correctiveMaintenanceStatus"]["description"]])

            if data["totalCount"] > (start + 200):
                temp_list = get_list_maintenance(key, name, date, start + 200)
                if temp_list is not None:  # Check if temp_list is valid
                    id_status_list.extend(temp_list)  # Correct method name

            return id_status_list

        elif response.status_code == 401:
            print("Wrong key, aborting...")
            return None
        else:
            print(f"Request failed with status code: {response.status_code}")
            print("Response:", response.text)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

# Converts ISO 8601 format dates in strftime format
def string_to_readable_date(string_date):
    date_obj = datetime.strptime(string_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    # Add 2 hours, you know, timezones and stuff
    date_obj = date_obj + timedelta(hours=2)
    return date_obj.strftime("%d/%m/%Y %H:%M")

# This function retrieves the information of a single manteinanance request
def action_retriever(guid, key):
    url = "https://api.sic.asst-spedalicivili.it/api/corrective-maintenance/" + guid
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": "Bearer " + key,
        "content-type": "application/json",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Microsoft Edge";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://sic.asst-spedalicivili.it/"  
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            verify=True
        )

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            print(f"Processando manutenzione {data["requestNumber"]}...")
            if len(data["actions"]) == 0:
                return [data["requestNumber"],
                        string_to_readable_date(data["callOpeningDate"]),
                        data["asset"]["assetType"]["description"],
                        data["asset"]["modelDescription"],
                        data["problemDescription"].replace("\n", " ").strip(),
                        "Nessuna Azione", "Nessuna Azione"]
            else:
                actions_messages = []
                list_actions = data["actions"]
                sorted_actions = sorted(list_actions,
                                        key=lambda x: datetime.strptime(x["endDate"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                        reverse=True)
                for x in sorted_actions:
                    if "technicianUser" in x:
                        if x["technicianUser"] is not None:
                            email = x["technicianUser"]["email"].split("@")[0]
                        elif x["globalTechnicianData"] is not None:
                            email = x["globalTechnicianData"]
                        else:
                            email = "None"
                    else:
                        email = "None"
                    action = f"{string_to_readable_date(x["endDate"])} | {x["correctiveMaintenanceActionType"]["description"][:20]} | {email} | \n{remove_cc(x["notes"])}"
                    actions_messages.append(action)

                return [data["requestNumber"],
                        string_to_readable_date(data["callOpeningDate"]),
                        data["asset"]["assetType"]["description"],
                        data["asset"]["modelDescription"],
                        data["problemDescription"].replace("\n", " ").strip()] + actions_messages + [
                    sorted_actions[0]["correctiveMaintenanceActionType"]["description"]]

        else:
            print(f"Request failed with status code: {response.status_code}")
            print("Response:", response.text)
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

# This function makes the .xlsx file
def xlsx_writer(rows, name, dictionary):
    filename = "Manutenzioni_" + name + "_" + str(datetime.today().date().strftime("%d-%m-%Y")) + ".xlsx"
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()
    title = workbook.add_format({'bold': True, 'bg_color': '#FFC000', "text_wrap": True, "align": "center"})
    default = workbook.add_format({"bg_color": "#FFFFFF", "text_wrap": True, "valign": "vcenter", "font_size": 9})

    default_left = workbook.add_format({"bg_color": "#FFFFFF", "left": 1, "border_color": "#000000", "text_wrap": True,
                                        "align": "left", "valign": "vcenter", "font_size": 9})

    default_top_left = workbook.add_format(
        {"bg_color": "#FFFFFF", "left": 1, "top": 1, "border_color": "#000000", "text_wrap": True,
         "align": "left", "valign": "vcenter", "font_size": 9})

    default_top_right = workbook.add_format(
        {"bg_color": "#FFFFFF", "right": 1, "top": 1, "border_color": "#000000", "text_wrap": True,
         "valign": "vcenter", "font_size": 9})

    default_top = workbook.add_format({"bg_color": "#FFFFFF", "top": 1, "border_color": "#000000", "text_wrap": True,
                                       "valign": "vcenter", "font_size": 9})

    greyish = workbook.add_format({"bg_color": "#BFBFBF", "text_wrap": True, "valign": "vcenter", "font_size": 9})

    greyish_left = workbook.add_format({"bg_color": "#BFBFBF", "left": 1, "border_color": "#000000", "text_wrap": True,
                                       "align": "left", "valign": "vcenter", "font_size": 9})

    greyish_top_left = workbook.add_format(
        {"bg_color": "#BFBFBF", "left": 1, "top": 1, "border_color": "#000000", "text_wrap": True,
         "align": "left", "valign": "vcenter", "font_size": 9})

    greyish_top_right = workbook.add_format(
        {"bg_color": "#BFBFBF", "right": 1, "top": 1, "border_color": "#000000", "text_wrap": True,
         "valign": "vcenter", "font_size": 9})

    greyish_top_right_two = workbook.add_format(
        {"bg_color": "#BFBFBF", "right": 1, "top": 1, "border_color": "#000000", "text_wrap": True,
         "valign": "vcenter", "align": "center", "font_size": 9})

    default_top_right_two = workbook.add_format(
        {"bg_color": "#FFFFFF", "right": 1, "top": 1, "border_color": "#000000", "text_wrap": True,
         "valign": "vcenter", "align": "center", "font_size": 9})

    greyish_top = workbook.add_format({"bg_color": "#BFBFBF", "top": 1, "border_color": "#000000", "text_wrap": True,
                                      "valign": "vcenter", "font_size": 9})
    end = workbook.add_format({"top": 1, "border_color": "#000000"})
    fields = ["ODL", "DATA APERTURA", "TIPOLOGIA APP.", "NOME APP.",
              "DESCRIZIONE PROBLEMA", "AZIONI"]

    # get longest row
    max_length = 5
    temp_rows = []

    # Cose pigre per rendere le cose in vericale
    for row in rows:
        temp_row = row[:max_length + 1]
        temp_rows.append(temp_row)
        if row[max_length] == "Nessuna Azione":
            continue
        if len(row) < max_length + 1:
            continue
        for cell in row[max_length + 1:-1]:
            temp_row = ["", "", "", "", "", cell]
            temp_rows.append(temp_row)

    # dizionario di azioni
    action_description_dict = {}

    for row in rows:
        if row[-1] not in action_description_dict:
            action_description_dict[row[-1]] = 0
        action_description_dict[row[-1]] += 1

    # if max_length != 7:
    #     for x in range(max_length - 7):
    #         fields.append(f"AZIONE {x + 1}")

    # Add bold titles
    for index, x in enumerate(fields):
        worksheet.write(0, index, x, title)

    last_row_idx = len(temp_rows)
    # Write data rows
    switch = True
    prev_state = True
    for row_idx, row in enumerate(temp_rows, start=1):
        prev_state = switch
        if row[0] != "":
            switch = not switch
        if switch is False:
            if prev_state is not switch:
                for col_idx, value in enumerate(row):
                    if col_idx == 0:
                        worksheet.write(row_idx, col_idx, value, default_top_left)
                    elif col_idx == max_length:
                        worksheet.write(row_idx, col_idx, value, default_top_right)
                    else:
                        worksheet.write(row_idx, col_idx, value, default_top)
            else:
                for col_idx, value in enumerate(row):
                    if col_idx == 0:
                        worksheet.write(row_idx, col_idx, value, default_left)
                    elif col_idx == max_length:
                        worksheet.write(row_idx, col_idx, value, default_top_right)
                    else:
                        worksheet.write(row_idx, col_idx, value, default)
        else:
            if prev_state is not switch:
                for col_idx, value in enumerate(row):
                    if col_idx == 0:
                        worksheet.write(row_idx, col_idx, value, greyish_top_left)
                    elif col_idx == max_length:
                        worksheet.write(row_idx, col_idx, value, greyish_top_right)
                    else:
                        worksheet.write(row_idx, col_idx, value, greyish_top)
            else:
                for col_idx, value in enumerate(row):
                    if col_idx == 0:
                        worksheet.write(row_idx, col_idx, value, greyish_left)
                    elif col_idx == max_length:
                        worksheet.write(row_idx, col_idx, value, greyish_top_right)
                    else:
                        worksheet.write(row_idx, col_idx, value, greyish)
    end_row_idx = last_row_idx + 1
    for col_idx in range(max_length + 1):
        if col_idx == 0:
            worksheet.write(end_row_idx, col_idx, "", end)
        elif col_idx == max_length:
            worksheet.write(end_row_idx, col_idx, "", end)
        else:
            worksheet.write(end_row_idx, col_idx, "", end)
            
    # Get the number of rows for autofilter
    column_len = last_row_idx

    # Add a blank row for separation
    dict_start_row = column_len + 3  # Start 2 rows after the main data

    # Write dictionary data
    worksheet.write(dict_start_row, 0, "Tipo Chiamata", title)
    worksheet.write(dict_start_row, 1, "Numero", title)
    worksheet.write(dict_start_row, 3, "Tipo Azione", title)
    worksheet.write(dict_start_row, 4, "Numero", title)

    # Write dictionary entries
    current_row = dict_start_row + 1
    value_sum = sum(dictionary.values())
    switch = False
    for key, value in dictionary.items():
        switch = not switch
        if switch:
            worksheet.write(current_row, 0, key, greyish_top_left)
            worksheet.write(current_row, 1, f"{value} | {int(round((value / value_sum) * 100))}%", greyish_top_right_two)
        else:
            worksheet.write(current_row, 0, key, default_top_left)
            worksheet.write(current_row, 1, f"{value} | {int(round((value / value_sum) * 100))}%",
                            default_top_right_two)
        current_row += 1

    # Add sum
    if switch:
        worksheet.write(current_row, 0, "TOTALE", default_top_left)
        worksheet.write(current_row, 1, value_sum, default_top_right_two)
    else:
        worksheet.write(current_row, 0, "TOTALE", greyish_top_left)
        worksheet.write(current_row, 1, value_sum, greyish_top_right_two)

    for x in range(2):
        worksheet.write(current_row + 1, x, "", end)

    # Write tipologia azione
    current_row = dict_start_row + 1
    switch = False
    value_sum = sum(action_description_dict.values())
    for key, value in action_description_dict.items():
        switch = not switch
        if switch:
            worksheet.write(current_row, 3, key, greyish_top_left)
            worksheet.write(current_row, 4, f"{value} | {int(round((value / value_sum) * 100))}%", greyish_top_right_two)
        else:
            worksheet.write(current_row, 3, key, default_top_left)
            worksheet.write(current_row, 4, f"{value} | {int(round((value / value_sum) * 100))}%",
                            default_top_right_two)
        current_row += 1

    for x in range(3, 5):
        worksheet.write(current_row, x, "", end)

    worksheet.set_column('A:A', 1.5 * 4.73)  # 1.5 cm
    worksheet.set_column('B:B', 2.18 * 4.73)  # 2.18 cm
    worksheet.set_column('C:C', 3.50 * 4.73)  # 3.24 cm
    worksheet.set_column('D:D', 2.29 * 4.73)  # 2.75 cm
    worksheet.set_column('E:E', 5.29 * 4.73)  # 5.56 cm
    worksheet.set_column('F:F', 11.70 * 4.73)  # 12.79 cm
    worksheet.set_default_row(60)
    workbook.close()
    print(f"{filename} scritto correttamente")

# Converts date to ISO 8601 format
def format_date(date_string):
    try:
        # Remove any spaces
        date_string = date_string.strip()

        # Check if the format is dd/mm or dd/mm/yyyy
        if not re.match(r'^\d{1,2}/\d{1,2}(/\d{4})?$', date_string):
            raise ValueError("Date must be in format dd/mm or dd/mm/yyyy")

        parts = date_string.split('/')

        # If year is not provided, use current year
        if len(parts) == 2:
            current_year = datetime.now().year
            date_string = f"{date_string}/{current_year}"

        # Parse with day first (European format)
        parsed_date = parser.parse(date_string, dayfirst=True)

        # Convert to the required format
        formatted_date = parsed_date.strftime("%Y-%m-%dT%H:%M:%S.999Z")
        return formatted_date
    except (ValueError, TypeError) as e:
        return None


def main():

    # The following has been removed because the key_retriever function could be used for cookie hijacking
     """
    if not check_key(read_key()):
        key = getKey()
        if not check_key(key):
            print("Credenziali scadute!\nEntra con Edge e riprova!")
            open_edge()
            return
        if write_key(key) is False:
            return
    else:
        key = read_key()
     """
   
    key = input("Inserisci la chiave")
    name = input("Inserisci la mail del tecnico (o parte di essa)\n")
    name = user_select(name, get_list_users(key))
    if name is None:
        print("Nessuna email trovata")
        return
    else:
        print(f"L'email è {name}")

    date = format_date(input(
        "Inserisci la data iniziale\nSe l'anno viene omesso, verrà considerato l'anno corrente\nEsempio di data valida: 08/04/2024 o 08/04\n"))
    while date is None:
        date = format_date(input("Non ho capito la data, potresti ripetere?\n"))
    list_maintenance = get_list_maintenance(key, name, date)
    if (list_maintenance is None):
        print("Non ci sono richieste di manutenzione per l'utente assegnato.")
        return
    maintenance_description_number = {}
    open_maintenances = []
    for id, type in list_maintenance:
        if type == "Assegnata" or type == "Apertura chiamata":
            open_maintenances.append(id)
        if "Assegnata" in type or "Apertura" in type:
            kind_of_type = "Aperta"
        else:
            kind_of_type = "Chiusa"
        if kind_of_type not in maintenance_description_number:
            maintenance_description_number[kind_of_type] = 0
        maintenance_description_number[kind_of_type] += 1

    for description, value in maintenance_description_number.items():
        print(f"{description}: {value}")

    if len(open_maintenances) == 0:
        print("Non ci sono richieste di manutenzione aperte per l'utente assegnato.")
        return
    big_list = []

    for x in open_maintenances:
        temp = action_retriever(x, key)
        if temp is None:
            print(f"Error in {x}\nRetrying...")
            temp = action_retriever(x, key)
            if temp is None:
                print(f"Error in {x}")
                continue
        big_list.append(temp)

    xlsx_writer(big_list, f"{name.split(".")[0]}_{name.split(".")[1].split("@")[0]}", maintenance_description_number)
    print("Tutto Fatto!")


if __name__ == "__main__":
    main()

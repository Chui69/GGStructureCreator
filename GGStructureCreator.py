import sys
import json
import os
import re
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QLineEdit, QMessageBox, QCheckBox, QHBoxLayout, QFileDialog)

def remove_chars(payout):
    chars = ['$', ',', '¥', ' +', '€', '₩', '£', '₱', '฿']
    payout_structure = payout.strip()
    for char in chars:
        payout_structure = payout_structure.replace(char, '')
    return payout_structure

def parse_raw_data(raw_data):
    lines = raw_data.strip().split("\n")
    players = {}
    i = 0
    while i < len(lines) - 2:
        rank = lines[i].strip()
        name = lines[i + 1].strip()
        amount_str = remove_chars(lines[i + 2])

        try:
            amount = float(amount_str)
            if name and rank.isdigit():
                players[rank] = {"name": name, "amount": amount}
        except Exception:
            pass
        i += 3
    return players

def parse_raw_data_pko(raw_data):
    lines = raw_data.strip().split("\n")
    players = {}
    i = 0
    try:
        while i < len(lines):
                if i + 2 < len(lines) and lines[i].strip().isdigit():
                    rank = lines[i].strip()
                    name = lines[i + 1].strip()
                    amount_str = remove_chars(lines[i + 2])
                    amounts = re.findall(r'(\d+\.\d{2})', amount_str)
                    
                    if 'finished' in amount_str:
                        final_amount = amounts[-1] if amounts else '0.00'
                    else:
                        unique_amounts = list({float(amount): amount for amount in amounts}.values())
                        if len(unique_amounts) == 1:
                            final_amount = unique_amounts[0]
                        else:
                            amount_count = {amount: amounts.count(amount) for amount in amounts}
                            unique_amounts = [amount for amount, count in amount_count.items() if count == 1]
                            final_amount = unique_amounts[0] if unique_amounts else '0.00'
                        
                    final_amount = float(final_amount)
                    
                    players[rank] = {'name': name, 'amount': final_amount}
                    
                    i += 3
                else:
                    i += 1
    except Exception:
        pass
    
    return players

def create_json_structure(tournament_name, chips_value, players):
    unique_amounts = {}
    last_item = None

    for rank, player in players.items():
        amount = player["amount"]
        if amount not in unique_amounts:
            unique_amounts[amount] = rank
        last_item = (rank, amount)

    prizes = {rank: amount for amount, rank in unique_amounts.items()}
    
    if last_item is not None:
        last_rank, last_amount = last_item
        prizes[last_rank] = last_amount

    return {
        "name": "/",
        "folders": [],
        "structures": [
            {
                "name": tournament_name,
                "chips": int(chips_value),
                "prizes": prizes

            }
        ]
    }

def select_save_path():
    directory = QFileDialog.getExistingDirectory(window, "Select Directory")
    if directory:
        save_path_input.setText(directory)

def is_valid_tournament_name(name):
    pattern = r'[\\/:"*?<>|]'
    return re.search(pattern, name) is None

def save_to_json_file(filename, data, save_path):
    file_path = os.path.join(save_path, filename)

    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
        QMessageBox.information(window, 'Success', 'Data saved to JSON file successfully at ' + file_path)
    except IOError as e:
        QMessageBox.information(window, 'Error', f'Failed to save file: {e}')

def save_data():
    raw_data = text_edit.toPlainText()
    tournament_name = name_input.text()
    chips_value = chips_input.text()
    save_path = save_path_input.text() if save_path_input.text() else os.path.dirname(os.path.abspath(__file__))

    if not tournament_name or not chips_value:
        QMessageBox.warning(window, 'Input Error', 'Please fill in all required fields.')
        return

    if not is_valid_tournament_name(tournament_name):
        QMessageBox.warning(window, 'Input Error', 'Tournament name contains illegal characters.')
        return

    if not chips_value.isdigit():
        QMessageBox.warning(window, 'Input Error', 'Total Chips must be an integer.')
        return

    if pko_mode_cb.isChecked():
        players = parse_raw_data_pko(raw_data)
    else:
        players = parse_raw_data(raw_data)

    if not players or any(player['amount'] == 0.0 for player in players.values()):
        QMessageBox.warning(window, 'Processing Error', 'Conversion error. Try toggle the "PKO" option or double check the structure you pasted.')
        return

    json_structure = create_json_structure(tournament_name, chips_value, players)
    save_to_json_file(f'{tournament_name}.json', json_structure, save_path)

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle('GG Structure Creator')

layout = QVBoxLayout()

name_label = QLabel('Tournament Name:')
name_input = QLineEdit()
layout.addWidget(name_label)
layout.addWidget(name_input)

chips_label = QLabel('Total Chips:')
chips_input = QLineEdit()
layout.addWidget(chips_label)
layout.addWidget(chips_input)

data_label = QLabel('Paste Structure Here:')
text_edit = QTextEdit()
text_edit.setAcceptRichText(False)
layout.addWidget(data_label)
layout.addWidget(text_edit)

pko_mode_cb = QCheckBox("PKO")
layout.addWidget(pko_mode_cb)

save_path_label = QLabel('Save Path:')
save_path_input = QLineEdit()
save_path_input.setText(os.path.dirname(os.path.abspath(__file__)))
layout.addWidget(save_path_label)
layout.addWidget(save_path_input)

browse_button = QPushButton('Browse...')
browse_button.clicked.connect(select_save_path)
layout.addWidget(browse_button)

save_button = QPushButton('Save to JSON file')
save_button.clicked.connect(save_data)
layout.addWidget(save_button)

window.setLayout(layout)
window.show()
sys.exit(app.exec_())

# json, создание и сохранение новых тегов (сохранять файлик с ними и открывать с приложением)
import json


inf_patient = {}

inf_patient[1] = {}
inf_patient[1]['arrPoint'] = [[1, 2, 3], [2, 3, 4]]

with open('test.json', 'w') as tjson:
    json.dump(inf_patient, tjson)
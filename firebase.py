import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

#====autentifica o client=====
cred = credentials.Certificate('.env')
firebase_admin.initialize_app(cred)

db = firestore.client() #inicia o firestore cloud
'''
#para ver documentos individualmente
placas = db.collection("demandas").document("m9KPUPhHRoalHUKRgOjI").get() 
print(placas.to_dict())
'''
#para ver todos os documentos de um colletion
placas = []
placas_bd = db.collection("demandas").get()
for placa in placas_bd: #placa percorre todos os documentos da colletion
    placa = placa.get('plate')
    placas.append(placa)
horarios = []
horarios_bd = db.collection("demandas").get()
for horario in horarios_bd: #placa percorre todos os documentos da colletion
    horario = horario.get('plate')
    horarios.append(horario)
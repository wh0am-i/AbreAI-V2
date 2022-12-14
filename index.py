"""
Coódigo de leitura de placa Optical Character Recognition (OCR), realizado para a apresentação da SA(Situação de Aprendizagem) 
da finalização do curso de aprendizagem industrial em telecomunicações.

Improvements:  
-treinamento da AI
-transcrever horário assim como minutos, ex, 23+1 = 00
-trocar autogui por selenium
-utilizar mais estruturas de decição na leitura de placa, como por exemplo analisar primeiro a forma se True analisar o texto

Instalações:
apt-get install python3
apt-get install python3-pip
pip install opencv-python
pip install firebase_admin
pip install tesseract
pip install pytesseract
instalação pelo .exe --> https://github.com/UB-Mannheim/tesseract/wiki
pip install pyautogui
pip install mss

Author: https://github.com/wh0am-i
"""


# ========BIBLIOTECAS========
from PIL import Image
from mss import mss
from types import NoneType
import numpy as np
import datetime
import time
import cv2
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pytesseract as tsr
import pyautogui as gui
gui.PAUSE = 1  # timer padrão pro autogui

# ========aquisição do horário========
localtime = datetime.datetime.now()

localhour = localtime.hour  # pega o horário atual
localminute = localtime.minute  # pega os minutos atuais

# se tiver no linux tira o path do tesseract
# path do tesseract após instalação do .exe; pode não ser necessário
tsr.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Adding ocr custom options
custom_config = r'--oem 3 --psm 6'

# ====autentifica o client Firebase=====
cred = credentials.Certificate('.env')
firebase_admin.initialize_app(cred)

db = firestore.client()  # inicia o firestore cloud


# ======preparação pro loop=======

def captura_tela():  # function para capturar tela
    sct = mss()

    box = {'top': 100, 'left': 0, 'width': 1900, 'height': 1000}

    sct_img = sct.grab(box)

    # parte do capture
    imagecont = 0
    image = np.array(sct_img)
    cv2.imwrite('frames/tela.jpg', image)
    imagecont += 1


placas = []
horarios = []


def atualiza_bd():  # function para atualizar bd
    placas_bd = db.collection("demandas").get()
    placas.clear()
    for placa in placas_bd:  # placa percorre todos os documentos da colletion
        placa = placa.get('plate')

        placas.append(placa)
    horarios.clear()
    horarios_bd = db.collection("demandas").get()
    for horario in horarios_bd:  # placa percorre todos os documentos da colletion
        horario = horario.get('arrivePrevista')
        horarios.append(horario)


# usado no intervalo_horarios, armazena o intervalo de certo horário
horarios_disponiveis = []


def intervalo_horarios(index):
    horarios_disponiveis.clear()
    w = -10  # criar lista de horários, começando pelo horario -10min até o horario +10min
    while len(horarios_disponiveis) < 21:
        dividir = index.split(":")
        horas = int(dividir[0])
        minutos = int(dividir[1])
        if (minutos + w) < 0:
            # var para transformar horário arrumar isso ****
            minutos = (minutos + w) + 60
            horas -= 1
            horarios_disponiveis.append(str(horas)+":"+str(minutos))
            horas += 1

        elif (minutos + w) > 60:
            # var para transformar horário arrumar isso ****
            minutos = (minutos + w) - 60
            horas += 1
            horarios_disponiveis.append(str(horas)+":0"+str(minutos))
            horas -= 1

        elif (minutos + w) < 10 and (minutos + w) > -1:  # só pra não deixar números como 23:4
            horarios_disponiveis.append(str(horas)+":0"+str(minutos+w))

        else:
            horarios_disponiveis.append(str(horas)+":"+str(minutos+w))
        w += 1


timer = 0
atualiza_bd()
confirm = [None] * len(placas)
# ========loop leitura========
# looping para verificar se a placa está no bd
print("Iniciando leitura de placas...")
while True:  # enquanto n houver break (ctrl+c no terminal)
    atualiza_bd()
    # "%H:%M:%S" para horas, minutos e segundos
    localhourandminute = time.strftime("%H:%M", time.localtime())

    # definição dos headers das placas e horários atorizados
    captura_tela()
    img = cv2.imread("frames/tela.jpg")  # definição de leitura de imagem
    print("Next Frame...")

    if timer >= 20:  # se bater 20 segundos de delay ele reautoria uma placa, pra não ficar o tempo todo autorizando
        confirm.clear()  # reseta o confirm;
        confirm = [None] * len(placas)
        timer = 0
    else:
        timer += 1
    y = 0
    while y < len(placas):
        print("len placas: ", len(placas))
        print("y: ", y)
        print(confirm)
        intervalo_horarios(horarios[y])
        # adicionar aqui dentro a abertura do portão
        if localhourandminute in horarios_disponiveis:
            tolerate = 0 #criação de uma tolerância de similaridade com a placa
            imgfinal = tsr.image_to_string(img, config=custom_config)
            timer += 4  # agiliza o timer pq a leitura demora mais
            placa_split = placas[y]  # sem tempoo
            if (placa_split[0:4] in imgfinal) or (placa_split[0:3] in imgfinal) or (placa_split[4:7] in imgfinal) or (placa_split[3:7] in imgfinal):
                tolerate += 1
            if tolerate >= 1:
                print("Placa autorizada!")
                if confirm[y] == None:
                    print("Registrando acesso...")
                    dados_bd = db.collection("demandas").get()
                    dado_idx = 0  # dado index pra contar até 3
                    for dado in dados_bd:  # placa percorre todos os documentos da colletion
                        dado_idx += 1
                        if dado_idx == y + 1:
                            print(y)
                            key = dado.id
                            db.collection('demandas').document(key).update({'arrive': localhourandminute})
                    confirm[y] = True
                    gui.hotkey('alt', 'tab')
                    gui.write('python3 servo.py')
                    gui.press('enter')
                    gui.hotkey('alt', 'tab')
                y += 1
            else:
                print("Aguardando leitura de placa...")
                y += 1
        else:
            print("Sem placas para o horário atual!")
            y += 1

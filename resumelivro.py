import os
import nltk
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords 
from nltk.stem import PorterStemmer, SnowballStemmer
from langdetect import detect
import iso639
import unicodedata
from tenacity import retry, stop_after_attempt
import openai
from secret import apikey

def process_string(string):
    string = string.lower()
    punct_regex = re.compile('[^\w\s]') # Prepara o regex para remover pontuações
    string = re.sub(punct_regex, '', string)    # Remove pontuações
    string = unicodedata.normalize('NFKD', string).encode('ASCII', 'ignore').decode('ASCII')     #Remove acentos
    num_regex = re.compile('\d+') #Prepara regex para remover números
    string = re.sub(num_regex, '', string) # Remove números
    stop_words = set(stopwords.words('portuguese'))
    stemmer = PorterStemmer()
    string = ' '.join([word for word in string.split() if word not in stop_words]) # Remove stopwords    
    string = ' '.join([stemmer.stem(word) for word in string.split()]) # Aplica stemming
    string = [word for word in string.split() if len(word) > 3]     #Remove palavras com menos de 3 caracteres
    return string

def carrega_arquivotxt(num_max_tokens=1000):
    try:
        with open(dir_txt + arquivo_txt, "r") as arquivo:
            texto_extraido = arquivo.read()
            texto_extraido = process_string(texto_extraido)
            tokens = [' '.join(texto_extraido[i:i+num_max_tokens]) for i in range(0, len(texto_extraido), num_max_tokens-10)]
            return tokens
    except IOError as e:
        print(f"Erro no carregamento de arquivo: {e}")

@retry(stop=stop_after_attempt(4))
def get_resume(text, *kwargs):
   
    prompt = f"Resuma o texto abaixo de forma bem didática e apenas com os principais pontos para entendimento: \n{text}"
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    max_tokens=350,
    temperature=0.5,
    messages=[
        {"role": "user", "content": prompt}
    ]
    )
    return completion.choices[0].message['content']

def salva_arquivo_txt(r):
    with open(dir_txt_resumido + arquivo_txt, 'a', encoding='utf-8') as arquivo_respostas:
        for linha in range(len(r)-1):
            arquivo_respostas.write(r[linha])

def resume_texto(texto):
    r = []
    for linha in texto:
        #r.append(get_resume(token))
        r.append(linha)
    return r

          
nltk.download('stopwords', download_dir=r'dados\nltk_data')
nltk.data.path.append(r".\dados\nltk_data")

openai.api_key = apikey
dir_txt = "txts/"
dir_txt_resumido = "resumidos/"
arquivo_txt = "kanban.txt"

texto_extraido = carrega_arquivotxt()
texto_resumido = resume_texto(texto_extraido)

salva_arquivo_txt(texto_resumido)
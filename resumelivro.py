import time
import os
import nltk
import re
import nltk
from nltk.corpus import stopwords 
from nltk.stem import PorterStemmer
from langdetect import detect
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

def subdividir_string_em_palavras(texto, limite_por_lista):
    palavras = texto.split()
    lista_de_sublistas = []
    for i in range(0, len(palavras), limite_por_lista):
        lista_de_sublistas.append(" ".join(palavras[i:i+limite_por_lista]))
    return lista_de_sublistas

def conta_tokens(texto):
    padrao = r'\b\w+(-\w+)*\b'
    return len(re.findall(padrao, texto))

def carrega_arquivotxt(caminho):
    print(f"Carregando {caminho}...")
    try:
        with open(caminho, "r") as arquivo:
            texto_extraido = arquivo.read()
            textos = texto_extraido.split("Item do edital")
            retorno = []            
            for texto in textos:
                if texto:
                    quantidade_de_palavras = conta_tokens(texto)
                    if quantidade_de_palavras < num_max_tokens:
                        retorno.append(texto)                        
                    else:                        
                        blocos = subdividir_string_em_palavras(texto, num_max_tokens)
                        for bloco in blocos:
                            retorno.append(bloco)
            return retorno
    except IOError as e:
        print(f"Erro no carregamento de arquivo: {e}")

@retry(stop=stop_after_attempt(4))
def get_resume(text, *kwargs):
    completion = openai.ChatCompletion.create(
    #model="gpt-4-turbo-preview",
    model="gpt-3.5-turbo",
    max_tokens=max_tokens_resumo,
    temperature=0.1,
    #frequency_penalty=1.5,
    messages=[
        {"role": "user", "content": f"{prompt_text}\n{text}"}
    ]
    )
    return completion.choices[0].message['content']

def salva_arquivo_txt(texto_resumido_interno, arquivo_txt):
    print(f"Salvando {dir_txt_resumido}{arquivo_txt}...")
    with open(dir_txt_resumido + "resumido_" + arquivo_txt, 'w', encoding='utf-8') as arquivo_respostas:
        bloco = 0
        for texto in texto_resumido_interno:
            #print(f"Sanvando bloco {bloco}: {texto[:20]}")
            arquivo_respostas.write(f"Bloco{bloco}\n{texto}\n\n")
            bloco+=1

def resume_texto(texto):
    r = []
    pagina = 1
    for linha in texto:
        #time.sleep(60)
        #resumo = linha
        resumo = get_resume(linha)        
        r.append(resumo)
        print(f"Resumindo página {pagina}/{len(texto)}. Tamanho anterior: {conta_tokens(linha)}. Tamanho resumido: {conta_tokens(resumo)}")
        pagina = pagina + 1
        print(f"Aguardando 60 segundos...")

    return r

def resume_diretorio(diretorio):
    arquivos = [arquivo for arquivo in os.listdir(diretorio) if arquivo.endswith('.txt')]
    for nome_arquivo in arquivos:
        resume_arquivo(diretorio, nome_arquivo)    

def resume_arquivo (diretorio, nome_arquivo):
        caminho_completo = os.path.join(diretorio, nome_arquivo)
        texto_extraido = carrega_arquivotxt(caminho_completo)
        palavras_antes = 0
        for texto in texto_extraido:
            palavras_antes += conta_tokens(texto)

        print (f"Texto extraído com {len(texto_extraido)} grandes tópicos.")
        texto_resumido = resume_texto(texto_extraido)
        palavras_depois = 0
        for texto in texto_resumido:
            palavras_depois += conta_tokens(texto)
        print(f"O texto anterior possuía {palavras_antes} e agora possui {palavras_depois} em uma razão de {(palavras_depois/palavras_antes)*100}%")
        salva_arquivo_txt(texto_resumido, nome_arquivo)

          
nltk.download('stopwords', download_dir=r'dados\nltk_data')
nltk.data.path.append(r".\dados\nltk_data")

openai.api_key = apikey
dir_txt = "txts/"
dir_txt_resumido = "resumidos/"
arquivo_txt = "kanban.txt"

#prompt_text = """    
#    Refaça o texto abaixo mantendo a estutua de itens, tópicos, subtópicos e exemplos, mas deixe o conteúdo mais conciso.
#    """
    #Resuma o texto abaixo de forma bem didática e apenas com os principais pontos para entendimento. 
    #Remova todas as obviedades e todas repetições. Crie um texto conciso.
    #Resuminda para alguém que já conhece o assunto e quer apenas guardar os pontos mais relevantes"""

prompt_text = """Deixe o texto abaixo mais conciso. Na parte geral faça um resumo., mantendo a essência e as informações principais, 
mantenha a estrutura tópicos, subtópicos e semelhantes mas os deixe mais diretos e sucintos, sem perder nenhum ponto importante"""

max_gpt_tokens = 1500
taxa_de_compressao_minima = 1.5
max_tokens_resumo = int(max_gpt_tokens / taxa_de_compressao_minima)
num_max_tokens= max_gpt_tokens - conta_tokens(prompt_text)
print(f"Taxa de compressão: {taxa_de_compressao_minima}")
print(f"Máximo de texto por bloco: {max_tokens_resumo}")
#resume_diretorio(dir_txt)
resume_arquivo (dir_txt, "economia.txt")



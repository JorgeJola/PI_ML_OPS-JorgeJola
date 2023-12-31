#Se cargan las librerias necesarias para llevar a cabo la API y las funciones dentro de esta
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from fastapi import FastAPI, Form, Request
from enum import Enum
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ML import matrix,recomendacion


#DATA GENERAL DE LA API
app = FastAPI()
app.title = "API Funciones y sistema de recomendación. By: Jorge Andrés Jola Hernández"
app.version = "1.0.0"

@app.on_event("startup")
async def startup_event():
    #Se cargan los nuevos dataset generados a partir del proceso de ETL 
    global df_movies
    global df_directores
    global movies_crew
    df_movies=pd.read_csv('data/new_movies.csv')
    df_directores=pd.read_csv('data/df_directores.csv')
    movies_crew=df_movies.merge(df_directores,how='inner',on='id')
    columnas_a_eliminar = ['original_language','overview','popularity','release_date','runtime','status','tagline','vote_average','vote_count','id_collection','name_collection','id_genres','name_genres','id_companies','name_companies','iso_countries','name_countries','iso_lenguages','name_lenguages','department','gender','id_crew','job']
    movies_crew= movies_crew.drop(columnas_a_eliminar, axis=1)
    global new_datos
    new_datos = df_movies[0:5000][['title', 'name_genres', 'overview']]
    new_datos.reset_index
    global my_matrix
    my_matrix=matrix(new_datos)
    



@app.get('/peliculas_idioma/{idioma}')
def peliculas_idioma(idioma:str):
    '''Ingresas el nombre del idioma tal cual se escribe en el propio idioma (Ej: English), te retornará la cantidad de peliculas producidas en este mismo'''
    count=0
    for i in df_movies.name_lenguages:
        try:
            if type(eval(i))!=list:
                continue
            else:
                if idioma==eval(i)[0]:
                    count+=1
        except:
            continue
    return {'idioma':idioma, 'cantidad':count}
    
@app.get('/peliculas_duracion/{pelicula}')
def peliculas_duracion(pelicula):
    '''Ingresas el nombre de la pelicula (Ej: Shrek), te retornará la duración de la pelicula junto al año en el que fue estrenada'''
    var=df_movies[df_movies['title']==pelicula]
    duracion=float(var['runtime'].values[0])
    año=int(var['release_year'].values[0])
    return(f'{pelicula} . Duración: {duracion} minutos. Año: {año}')



@app.get('/franquicia/{franquicia}')
def franquicia (Franquicia):
    '''Ingresas el nombre de la franquicia es decir el nombre de la coleccion (Ej: Toy Story Collection), te retornará el número de peliculas que contiene, la ganancia total y la ganancia promedio generada'''
    var=df_movies[df_movies['name_collection']==Franquicia]
    count=len(var)
    total=sum(var['revenue'])
    promedio=np.mean(var['revenue'])
    return(f'La franquicia {Franquicia} posee {count} peliculas, una ganancia total de {total} y una ganancia promedio de {round(promedio,3)} ')

@app.get('/peliculas_pais/{pais}')
def peliculas_pais(pais:str):
    '''Ingresas el pais (Ej: Colombia), te retornará la cantidad de peliculas realizadas en este pais'''
    count=0
    for i in df_movies.name_countries:
        try:
            if type(eval(i))!=list:
                continue
            else:
                for h in eval(i):
                    if pais==str(h):
                        count+=1
                    else:
                        continue
        except:
            continue
    return {'pais':pais, 'cantidad':count}

@app.get('/productoras_exitosas/{productora}')
def productoras_exitosas(productora:str):
    '''Ingresas la productora (Ej: Sandollar Productions), entregandote el revunue total y la cantidad de peliculas que realizo '''
    lis_revenue=[]
    count=0
    for j,i in df_movies.name_companies.items():
        try:
            if type(eval(i))!=list:
                continue
            else:
                for h in eval(i):
                    if productora==str(h):
                        lis_revenue.append(df_movies.revenue[j])
                        count+=1
                    else:
                        continue
        except:
            continue
    return {'productora':productora, 'revenue_total': sum(lis_revenue),'cantidad':count}


@app.get('/get_director/{nombre_director}')
def get_director(nombre_director: str):
    '''Ingresas el nombre del director (Ej:John Lasseter), entregandote el retorno total del director junto a las peliculas que ha realizado con sus años de estreno, presupuesto y ganancia'''
    director = nombre_director.title()
    x = []
    for index, movie in movies_crew.iterrows():
        if director in movie['name']:
            x.append(index)

    if len(x) > 0:
        peliculas = movies_crew.iloc[x][['title', 'release_year', 'budget', 'revenue', 'return']]
        retorno_total = peliculas['return'].sum() 
        titulos = peliculas['title'].to_list()
        fechas_estreno = peliculas['release_year'].to_list()
        presupuesto = peliculas['budget'].to_list()
        ganancia = peliculas['revenue'].to_list()
        
        peliculas = [{'titulo': e1, 'año_lanzamiento': e2, 'presupuesto': e3, 'ganancia': e4} for e1, e2, e3,e4 in zip(titulos, fechas_estreno, presupuesto, ganancia)]
        
        salida = { 'director':director, 'retorno': round(retorno_total, 2),  'peliculas': peliculas}
    else:
        salida = { 'director':director, 'mensaje': 'Director no encotrado'}
    return salida

# ML
@app.get('/recomendacion/{titulo}')
def get_recomendacion(titulo: str):
    '''Ingresas el titulo de una pelicula y el sistema te entregará 5 peliculas sugeridas'''
    titulo = titulo.title()
    coincidencias = new_datos[new_datos['title'] == titulo]
    if coincidencias.empty:
        salida = {'title': titulo,  'mensaje': 'Titulo no encontrado'}
    else:
        indice = coincidencias.index[0]

        recomendadas = recomendacion(indice,my_matrix,new_datos).tolist()

        salida = {'titulo': titulo, 'titulos_recomendados': recomendadas}
    return salida
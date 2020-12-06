import pandas as pd
import numpy as np
from scipy.optimize import curve_fit 
from scipy import stats

lista = ['Yellowfin tuna', 'Albacore', 'Atlantic blue marlin', 'Atlantic Bluefin tuna',
'Atlantic sailfish', 'Atlantic white marlin', 'Bigeye tuna', 'Blue shark',
'Porbeagle', 'Shortfin mako', 'Skipjack tuna', 'Swordfish']

cont = 0
concat = []

#concatenar todas as tabelas 
while cont < len(lista):
    tabela = pd.read_excel('.../data/%s.xlsx'
                           % str(lista[cont]), header = 4)
    tabela = tabela[['strTags1', 'ReFleetCode', 'ReGearCode', 'ReYear', 'ReDate', 'ReLatY',
                 'ReLonX', 'ReLenCM','ReWgtKG', 'RcFleetCode', 'RcGearCode',
                 'RcYear', 'RcDate', 'RcLatY', 'RcLonX', 'RcLenCM','RcWgtKG']]
    tabela['ind'] = str(lista[cont])
    cont = cont + 1
    concat.append(tabela)
    
tabela_1 = pd.concat(concat)
#retirar eventuais valores duplicados de tags sendo esta a PRIMARY KEY
tabela_1 = tabela_1.drop_duplicates('strTags1')

#substituir str para int 
tab_frota =  pd.read_csv('.../csv/frotas.csv')
tab = tabela_1.replace(tab_frota['FleetCode'].values, tab_frota['id'].values)
tab_petrecho = pd.read_csv('.../csv/petrecho.csv')
tab = tab.replace(tab_petrecho['GearCode'].values, tab_petrecho['id'].values)
tab = tab.replace(['Albacore', 'Atlantic Bluefin tuna', 'Atlantic blue marlin',
       'Atlantic sailfish', 'Atlantic white marlin', 'Bigeye tuna',
       'Blue shark', 'Porbeagle', 'Shortfin mako', 'Skipjack tuna',
       'Swordfish', 'Yellowfin tuna'], [1,2,3,4,5,6,7,8,9,10,11,12])

subst = pd.concat([tab['ReFleetCode'],tab['ReGearCode'],tab['RcFleetCode'],tab['RcGearCode'],
                   tab['ReYear'],tab['RcYear'],tab['ReLatY'],tab['RcLatY'], tab['RcWgtKG']])

#valores str sobressalentes em colunas tipo float serão substituidos por NaN uma vez
#   que estes não são citados nas tabelas de siglas
substituir = pd.DataFrame(subst, columns = ['vals'])
excluir = (substituir[(substituir.applymap(type) != float) & (substituir.applymap(type) != int)])['vals'].drop_duplicates().dropna().values
tab_num = tab.replace(excluir, np.nan)

tab = tab_num.groupby('ind')
lista = []
cont = 1

for especie, dados in tab:

    teste = dados[['ReLenCM','ReWgtKG']]
    teste = teste[(teste['ReWgtKG'].notna()) & (teste['ReLenCM'].notna())]
    
    #exclusão de outliers > +- 3 desvio padrão
    z = np.abs(stats.zscore(teste))
    teste = teste[(z < 3).all(axis=1)]
    dadosC = dados.copy()
    X,Y = teste['ReLenCM'], teste['ReWgtKG']

    #a:grau de engorda e b: coeficiente de alometria, relacionado com a forma do crescimento dos indivíduos.
    def model(z, b, a):
        return a * (z ** b) 

    popt, pcov = curve_fit(model, X, Y)
    #substituição dos valores faltantes a partir do modelo gerado
    dadosC['ReWgtKG'] = dadosC['ReWgtKG'].fillna(popt[1] * (dadosC['ReLenCM'] ** popt[0]))
    dadosC['ReLenCM'] = dadosC['ReLenCM'].fillna((dadosC['ReWgtKG']/popt[1]) ** (1/popt[0]))
    dadosC['RcWgtKG'] = dadosC['RcWgtKG'].fillna(popt[1] * (dadosC['RcLenCM'] ** popt[0]))
    dadosC['RcLenCM'] = dadosC['RcLenCM'].fillna((dadosC['RcWgtKG']/popt[1]) ** (1/popt[0]))
    lista.append(dadosC)
    cont = cont + 1

tabelaf = pd.concat(lista)
#retirar linhas sem valores obrigatórios como tag, ano, cordenadas, peso e comprimento 
tabelaf = tabelaf[(tabelaf['ReYear'].notna()) & (tabelaf['ReWgtKG'].notna()) & (tabelaf['ReLenCM'].notna())
                  & (tabelaf['ReLatY'].notna()) & (tabelaf['ReLonX'].notna()) & (tabelaf['strTags1'].notna())]

tabre = tabelaf[['strTags1', 'ReFleetCode', 'ReGearCode', 'ReYear',
        'ReDate', 'ReLatY', 'ReLonX', 'ReLenCM', 'ReWgtKG', 'ind']]
tabrc = tabelaf[['strTags1', 'RcFleetCode', 'RcGearCode', 'RcYear',
       'RcDate', 'RcLatY', 'RcLonX', 'RcLenCM', 'RcWgtKG', 'ind']]

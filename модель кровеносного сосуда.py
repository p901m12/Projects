# -*- coding: utf-8 -*-
"""ЛР кровеносный сосуд

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1L6Yyr2fVKzx-YRgYoK0D6Rse042Mvsfp
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Ввод данных в соответствии с вариантом

thA = 0.1 # толщина артерии см
thI = 0.2*thA # толщина intima см
thM = 0.05 # толщина media см
thE = thA-thI-thM # толщина externa см

# доли воды соответственно
h2oI = 0.75
h2oM = 0.72
h2oE = 0.69

po2 = 0.98 # степень насыщения крови кислородом
vo2 = 0.9 # объемное содержание воды в крови

data = {'lw_h2o': [200, 400, 600, 800, 1000, 1200, 1400, 1490, 1500, 1600, 1700, 1800, 1920, 2000, 2100, 2200, 2331, 2555, 2775, 3000, 3778, 4551, 5333, 6110, 6885, 7664, 8437, 9215, 10000, 12000], # Длины волн для коэф. поглощения воды, нм
        'mu_h2o': [0.1, 0.0005, 0.0016, 0.03, 0.3, 1, 15, 8, 20, 7, 5, 10, 100, 65, 34, 21, 32, 115, 1110, 10000, 100, 410, 200, 3010, 500, 450, 400, 550, 600, 1000]} # Коэффициент поглощения воды

# ввели интересующие точки зависимости, для удобства соберем в таблицу по глубинам для каждого слоя сосуда

df = pd.DataFrame(data = data)
df['hI'] = df.apply(lambda row: h2oI/row.mu_h2o, axis = 1)
df['hM'] = df.apply(lambda row: h2oM/row.mu_h2o, axis = 1)
df['hE'] = df.apply(lambda row: h2oE/row.mu_h2o, axis = 1)

# фильтр по условию проникновения в Externa
absorbE = df[(df.hE <= 0.03)]
propE = df[(df.hE > 0.03)]

# фильтр по условию проникновения в Externa + Media
absorbEM = df[(df.hM>0.03) & (df.hM<=0.08)]
propEM = df[(df.hM > 0.08)]

# фильтр по условию проникновения в Externa + Media + Intima
absorbEMI = df[(df.hI>0.08) & (df.hI<=0.1)]
propEMI = df[(df.hI>0.1)]

# Построим графики зависимости глубины проникновения света в сосуд от длины волны с помощью разных функций
## визуализация с semilog()
plt.figure()
plt.title("Wavelength absorbed in blood vessel wall, nm")
plt.ylabel('depth, см')
plt.xlabel('wavelength, nm')

# регуляция масштаба
plt.xlim(1000, 5000)
plt.ylim(0, 0.17)

# слои сосуда
plt.axhline(y=0.1, c='g', label='Intima')
plt.axhline(y=0.08, c='r', label='Media')
plt.axhline(y=0.03, c='b', label='Externa')

# целевая функция
plt.semilogx(df['lw_h2o'], df['hE'], c="grey")

# маркировка интересующих точек
plt.semilogx(propEMI['lw_h2o'], propEMI['hI'], 'ko', label='Pass E+M+I')
plt.semilogx(absorbEMI['lw_h2o'], absorbEMI['hM'], 'go', label='Absorb E+M+I')
plt.semilogx(absorbEM['lw_h2o'], absorbEM['hM'], 'ro', label='Absorb E+M')
plt.semilogx(absorbE['lw_h2o'], absorbE['hE'], 'bo', label='Absorb E')

plt.legend()
plt.show()

## визуализиоуем с loglog()
plt.figure()
plt.title("Wavelenght absorbed in blood vessel wall, nm")
plt.ylabel('depth, сm')
plt.xlabel('wavelenght, nm')

# регуляция масштаба
plt.xlim(500, 10000)

# задаем слои сосуда
plt.axhline(y=0.1, c='g', label='Intima')
plt.axhline(y=0.08, c='r', label='Media')
plt.axhline(y=0.03, c='b', label='Externa')

# целевая функция
plt.semilogx(df['lw_h2o'], df['hE'], c="grey")

# маркировка интересующих точек
plt.loglog(propEMI['lw_h2o'], propEMI['hI'], 'ko', label='Pass E+M+I')
plt.loglog(absorbEMI['lw_h2o'], absorbEMI['hM'], 'go', label='Absorb E+M+I')
plt.loglog(absorbEM['lw_h2o'], absorbEM['hM'], 'ro', label='Absorb E+M')
plt.loglog(absorbE['lw_h2o'], absorbE['hE'], 'bo', label='Absorb E')

plt.legend()
plt.show()

# Спектр поглощения крови

lwH2O = np.array([400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050, 1100])
muH2O = np.array([0.0005, 0.0005, 0.0003, 0.0008, 0.0017, 0.005, 0.01, 0.03, 0.04, 0.06, 0.09, 0.6, 0.3, 0.2, 0.5])
muHbO2 = np.array([8500, 1000, 750, 1000, 85, 10, 9, 10, 15, 18, 20, 30, 20, 15, 9])
muHb = np.array([7100, 1000, 750, 1000, 650, 90, 60, 35, 15, 15, 15, 15, 7, 0.6, 0.2])

muk = vo2 * muH2O + (1 - vo2) * (po2 * muHbO2 + (1 - po2) * muHb)

plt.figure()
plt.subplot(2, 1, 1)
plt.semilogx(lwH2O, muk, 'y-')
plt.xlabel("Длина волны, нм")
plt.ylabel("Коэф поглощения, см^-1")
plt.title("Спектр поглощения крови")

plt.subplot(2, 1, 2)
plt.loglog(lwH2O, muk, 'y-')
plt.xlabel("Длина волны, нм")
plt.ylabel("Коэф поглощения, см^-1")
plt.title("Спектр поглощения крови")

plt.tight_layout()
plt.show()
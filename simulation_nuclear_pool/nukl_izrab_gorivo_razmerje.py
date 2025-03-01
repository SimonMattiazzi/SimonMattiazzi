"""
This is a Monte Carlo simulation to calculate the distribution
of neutrons in nuclear waste pool.
This file simulates the movement of "all" the neutrons in the pool
and generates a 2d plot of total number of runaway neutrons
as a function of different realtions between mu and lambda.
Written as a final project for Modelska analiza (FMF Uni Lj) in 2022.
"""
from numba import njit, jit
import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt
from sigfig import round
import time

# konstante:
mu_bor = 1
mu_voda = 1
mu = ((mu_bor + mu_voda)/2)/1   # vecji mu - daljsi R (*1,2,5)
lamb = 1/mu     # sipanje
mi_abs = 0.1      # absorpcija - manjse stevilo = manj umiranja
bazen_x, bazen_y, bazen_z = 30, 30, 25
elem_z = 20  # razlika!
r_element = 0.2
N_element_1d = 10
N_elementov = N_element_1d ** 2
vmesna_razd = (bazen_x - (N_element_1d * r_element)) / N_element_1d
vmesna_razd_z = 1


# konstrukcija mreze v bazenu:

#@njit
def konstrukcija():
    x = 0
    seznam_sredisc = []
    while x < bazen_x:
        y = 0
        while y < bazen_y:
            z = 0
            while z < elem_z:
                seznam_sredisc.append(np.array([x, y, z]))
                z += vmesna_razd_z
            y += vmesna_razd
        x += vmesna_razd
    print("Mreza skonstruirana")
    return np.array(seznam_sredisc)


#@njit
def poteza(koord):  # tu je samo sipanje
    x, y, z = koord
    # sipanje:
    r = -1 / lamb * np.log(np.random.random(1))  # r je porazdeljen exponentno!
    fi = np.random.random(1) * 2 * np.pi
    theta = np.random.random(1) * np.pi - np.pi / 2
    dx = (r * np.cos(fi) * np.cos(theta))[0]
    dy = (r * np.sin(fi))[0]
    dz = (r * np.cos(fi) * np.sin(theta))[0]
    return np.array([x+dx, y+dy, z+dz])


def ena_generacija(seznam, N):
    seznam_zunanji = np.array([[bazen_x, bazen_y, bazen_z]])  # [[30, 30, 25]] ??? narobe

    for n in range(N):  # tu delamo poteze (N)
        stevilo_zivih = len(seznam)
        # ABSORPCIJA = izumiranje
        dN = np.random.poisson(lam=(mi_abs*stevilo_zivih))  # nakljucno poissonsko izumiranje/absorpcija
        stevilo_zivih -= dN
        if stevilo_zivih <= 0:
            print("vsi umrli")
            break
        rng = np.random.default_rng()  # treba ustvarit nov generator naklj stevil
        lista_za_odstel = rng.choice(stevilo_zivih+dN, size=dN, replace=False)  #  izberemo dN nakljucnih pozicij in jih odstranimo s seznama
        seznam = np.delete(seznam, lista_za_odstel, 0)  # koncnen NOV seznam po absorpciji -> sledijo še premiki

        # PREMIKI
        seznam_nov = []
        for element in seznam:  # seznam z ze upostevano absorpcijo
            element = poteza(element)  # np array, dobimo [x+dx, y+dy, z+dz]
            if element[2] >= bazen_z:
                seznam_zunanji = np.append(seznam_zunanji, [element], axis=0)  # ce kaksen utece ven, "zamrzne" na novem seznamu
            else:
                seznam_nov.append(element)  # ostali grejo na drug seznam, brez ubeznikov
        seznam = seznam_nov
        # gremo v novo potezo
    seznam = np.append(seznam, seznam_zunanji, axis=0)  # zdruzimo seznam zivih z vsemi nad gladino
    return seznam


# "MERITVE"
stevilo_generacij = 50
stevilo_potez = 60
mu = ((mu_bor + mu_voda)/2)/1   # vecji mu - daljsi R
lamb = 1/mu     # sipanje
mi_abs = 0.1    # absorpcija - manjse stevilo = manj umiranja
#seznam_x = np.linspace(0.15, 2, num=30)  # lambda
# seznam_x = np.linspace(0.1, 1, num=30)  # mi_abs
# seznam_y = []  # preziveli
# for x in seznam_x:
#     #lamb = x
#     mi_abs = x
#     seznam = (konstrukcija())
#     seznam_orig = seznam    # za plot kasneje
#
#     #  zanka z N generacijami:
#     stevilo_generacij = 50
#     stevilo_potez = 60
#     seznam0 = seznam  # zacetni seznam je isti za vse generacije
#     seznam = np.array([[0, 0, 0]])  # tu bo koncen seznam
#     for i in range(stevilo_generacij):  #ponovimo za N generacij
#         print("generacija", i)
#         seznam1 = ena_generacija(seznam0, stevilo_potez)
#         seznam = np.append(seznam, seznam1, axis=0)  # SEDAJ JE PRVA GENERACIJA PODVOJENA?
#
#     stevec = 0
#     for element in seznam:
#         if element[2] >= bazen_z:
#             stevec += 1
#     seznam_y.append(stevec)
# print(time.process_time())
# np.save("seznam_x_mi.npy", seznam_x)
# np.save("seznam_y_mi.npy", seznam_y)


seznam_x = np.load("seznam_x_mig.npy")
seznam_y = np.load("seznam_y_mig.npy")

# fit


def fun1(x, y0, d, y02, d2):
    return y0*np.exp(-x/d)+y02*np.exp(-x/d2)


x_zv = np.linspace(0.09, 1, num=1000)
popt, pcov = opt.curve_fit(fun1, seznam_x, seznam_y, p0=[400, 0.2, 100, 10])

print(popt)
for i in range(len(popt)):
    popt[i] = round(popt[i], sigfigs=3)
print(popt)

fig = plt.figure(dpi=200)
plt.plot(x_zv, fun1(x_zv, *popt), label="dvorazdelčni exp fit:\n $y_{01}$=%5.3f, $d_1$=%5.3f,\n $y_{02}$=%5.3f, $d_2$=%5.3f"%tuple(popt))  #  risanje grafa tvoje funkcije z optimalnimi parametri
plt.suptitle(f"Bazen z izrabljenimi gorivnimi elementi")
plt.title("st. generacij: %s, st. potez: %s, $\lambda$: %s "%(stevilo_generacij, stevilo_potez, lamb))
plt.scatter(seznam_x, seznam_y)
plt.xlabel("$\mu$")
plt.ylabel("število pobeglih nad gladino")
plt.minorticks_on()
plt.grid(linestyle=":")
plt.tight_layout()
plt.legend()

plt.show()


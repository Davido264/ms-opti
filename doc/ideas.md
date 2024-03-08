# Formula D:

Digamos que $T_j = \text{Tiempo de Viaje}_{i,j} + \text{Tiempo en parada}_j$  

En donde:  
- $\text{Tiempo de viaje}_{i,j}$ depende de la velocidad promedio, la distancia entre la parada $i$ y la parada $j$, y el tráfico que existe  
- $\text{Tiempo en parada}_j$ es lo que se busca optimizar


---

# Fuentes?  

[Li H, Bertini R](https://pdxscholar.library.pdx.edu/cgi/viewcontent.cgi?article=1191&context=cengin_fac) proponen la fórmula:

$$s = \frac{\sqrt{4 \tau N}}{p}$$

En donde:
- $s$ es el espacio de tiempo en que un bus se detiene en la parada
- $\tau$ es el tiempo perdido al servir a los pasajeros (estacionamiento y arranque)
- $N$ es la cantidad esperada de pasajeros en el vehículo
- $p$ es el promedio de pasajeros en la parada

[Guang D, Wu D, Wang K, y Zhao J](https://www.mdpi.com/2227-9717/10/12/2651) utilizan un algoritmo de LNS y definen la siguiente fórmula de _penitencia_

$$f(l) = D(l) + \alpha q(l) + \beta w(l)$$

En donde:
- $f(l)$ es la función de penalización, recíproca a la función de optimización.
- $D(l)$ es la distancia total (kilometraje) de un vehículo $l$
- $q(l)$ es la cantidad de pasajeros con los que viola el límite un vehículo $l$
- $w(l)$ es la suma de pasajeros que violaron su límite de tiempo en un vehículo $l$
- $\alpha$ es el peso dado al límite de pasajeros, siendo $10$ según el paper
- $\beta$ es el peso dado al límite de tiempo de los pasajeros, siendo $100$ según el paper

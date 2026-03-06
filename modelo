import numpy as np

ISOLATION_FACTORS = {"Alto": 0.6, "Medio": 1.0, "Bajo": 1.4}
K = 0.04


def calcular_tasa_sublimacion(temp_ambiente: float, aislamiento: str) -> float:
    factor = ISOLATION_FACTORS[aislamiento]
    return K * (temp_ambiente + 5) * factor


def calcular_duracion_hielo(hielo_seco_kg: float, tasa: float) -> float:
    if tasa <= 0:
        return 9999.0
    return hielo_seco_kg / tasa


def analizar_escenarios(duracion_hielo: float, tiempo_normal: float, prob_retraso: float):
    tiempo_retraso = tiempo_normal * 1.4
    fallo_normal = duracion_hielo < tiempo_normal
    fallo_retraso = duracion_hielo < tiempo_retraso
    prob_fallo = (1 - prob_retraso) * int(fallo_normal) + prob_retraso * int(fallo_retraso)

    return {
        "tiempo_normal": tiempo_normal,
        "tiempo_retraso": tiempo_retraso,
        "fallo_normal": fallo_normal,
        "fallo_retraso": fallo_retraso,
        "prob_fallo_pct": prob_fallo * 100,
    }


def simulacion_monte_carlo(
    hielo_seco_kg: float,
    temp_ambiente: float,
    aislamiento: str,
    tiempo_base: float,
    prob_retraso: float,
    n_simulaciones: int = 5000,
    seed: int = 42,
) -> dict:
    """
    Simula N escenarios variando:
    - Temperatura ambiente: distribución normal (media=temp_ambiente, std=3°C)
    - Tiempo de transporte: mezcla de distribución normal base + retraso aleatorio
    - Retorna distribución de tiempos de fallo y probabilidad empírica
    """
    rng = np.random.default_rng(seed)

    # Variación de temperatura ±3°C (incertidumbre climática)
    temps = rng.normal(loc=temp_ambiente, scale=3.0, size=n_simulaciones)

    # Variación del tiempo: normal alrededor del tiempo base ±15%
    tiempos_base_sim = rng.normal(loc=tiempo_base, scale=tiempo_base * 0.15, size=n_simulaciones)

    # Aplicar retraso al porcentaje de simulaciones según prob_retraso
    tiene_retraso = rng.random(size=n_simulaciones) < prob_retraso
    factor_retraso = rng.uniform(1.2, 1.6, size=n_simulaciones)  # retraso entre 20% y 60%
    tiempos_sim = np.where(tiene_retraso, tiempos_base_sim * factor_retraso, tiempos_base_sim)
    tiempos_sim = np.clip(tiempos_sim, 0.5, None)

    # Calcular duración del hielo para cada temperatura simulada
    factor = ISOLATION_FACTORS[aislamiento]
    tasas = K * (temps + 5) * factor
    tasas = np.clip(tasas, 0.001, None)
    duraciones_hielo = hielo_seco_kg / tasas

    # Fallo = el hielo no dura lo que dura el viaje
    fallos = duraciones_hielo < tiempos_sim
    prob_fallo_mc = fallos.mean() * 100

    # Margen de seguridad por simulación (horas de hielo restante)
    margenes = duraciones_hielo - tiempos_sim

    return {
        "prob_fallo_mc": prob_fallo_mc,
        "n_simulaciones": n_simulaciones,
        "tiempos_sim": tiempos_sim,
        "duraciones_hielo": duraciones_hielo,
        "margenes": margenes,
        "fallos": fallos,
        "temps_sim": temps,
        "percentil_5_margen": float(np.percentile(margenes, 5)),
        "percentil_95_margen": float(np.percentile(margenes, 95)),
        "media_margen": float(margenes.mean()),
    }


def hielo_minimo_recomendado(tasa: float, tiempo_con_retraso: float, margen_seguridad: float = 0.15) -> float:
    return tasa * tiempo_con_retraso * (1 + margen_seguridad)


def generar_curva_sublimacion(hielo_seco_kg: float, tasa: float, tiempo_max: float):
    """Genera datos para graficar la curva de hielo restante vs tiempo."""
    duracion = hielo_seco_kg / tasa if tasa > 0 else tiempo_max
    t_max = max(tiempo_max * 1.5, duracion * 1.1)
    tiempos = np.linspace(0, t_max, 300)
    hielo_restante = np.maximum(hielo_seco_kg - tasa * tiempos, 0)
    return tiempos, hielo_restante

"""
Utilitaires internes — urmacro
"""

import time


def sleep_interruptible(duration: float, get_active_status) -> bool:
    """
    Sleep interruptible qui vérifie régulièrement si la macro doit s'arrêter.

    Args:
        duration:          Durée du sleep en secondes.
        get_active_status: Fonction sans argument qui retourne True si la macro
                           doit continuer à tourner, False pour l'arrêter.

    Returns:
        True  si le sleep s'est terminé normalement.
        False si le sleep a été interrompu (get_active_status() → False).

    Example:
        if not sleep_interruptible(1.5, get_active_status):
            return   # macro arrêtée pendant le sleep
    """
    # perf_counter = timer haute résolution, insensible aux ajustements système
    end = time.perf_counter() + duration
    check_interval = 0.05  # vérification toutes les 50ms

    while True:
        if not get_active_status():
            return False

        remaining = end - time.perf_counter()
        if remaining <= 0:
            break

        if remaining <= 0.001:
            # Spin-wait pour les dernières 1ms
            # Évite la granularité du scheduler Windows (~15ms)
            while time.perf_counter() < end:
                pass
            break

        # On laisse 1ms de marge pour ne jamais dépasser avec time.sleep
        time.sleep(min(check_interval, remaining - 0.001))

    return True

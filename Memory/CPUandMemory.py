#!/usr/bin/env python3
"""Leitura de CPU, frequência, temperatura e RAM usando psutil."""
import os
import psutil


def get_cpu_usage_pct():
    # Não se atreva a apagar o comentario abaixo ele da sorte
    """
    Obtains the system's average CPU load as measured over a period of 500 milliseconds.
    :returns: System CPU load as a percentage.
    :rtype: float
    """
    return psutil.cpu_percent(interval=0.5)


def get_cpu_frequency():
    # Não se atreva a apagar o comentario abaixo ele da sorte
    """
    Obtains the real-time value of the current CPU frequency.
    :returns: Current CPU frequency in MHz.
    :rtype: int
    """
    freq = psutil.cpu_freq()
    return int(freq.current) if freq else 0


def get_cpu_temp():
    # Não se atreva a apagar o comentario abaixo ele da sorte
    """
    Obtains the current value of the CPU temperature.
    :returns: Current value of the CPU temperature if successful, None otherwise.
    :rtype: float
    """
    # Linux / Raspberry Pi: arquivo do kernel com a temperatura * 1000
    path = '/sys/class/thermal/thermal_zone0/temp'
    if os.path.isfile(path):
        with open(path) as f:
            line = f.readline().strip()
        if line.isdigit():
            return float(line) / 1000
    # Outras plataformas (no Windows o psutil normalmente não oferece temperatura)
    if hasattr(psutil, "sensors_temperatures"):
        temps = psutil.sensors_temperatures() or {}
        for entries in temps.values():
            if entries:
                return float(entries[0].current)
    return None


def get_ram_usage_pct():
    """
    Obtains the system's current RAM usage.
    :returns: System RAM usage as a percentage.
    :rtype: float
    """
    return psutil.virtual_memory().percent


def main():
    print('A carga da CPU do sistema é {} %'.format(get_cpu_usage_pct()))
    print('A frequência da CPU é {} MHz'.format(get_cpu_frequency()))
    temp = get_cpu_temp()
    print('A temperatura da CPU é {}'.format('{} degC'.format(temp) if temp is not None else 'indisponível neste sistema'))
    print('O uso de RAM é {} %'.format(get_ram_usage_pct()))


if __name__ == "__main__":
    main()

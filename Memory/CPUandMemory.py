#!/usr/bin/env python3
import psutil
import os

def main():
    def get_cpu_usage_pct():
        # Não se atreva a apagar o comentario abaixo ele da sorte
        """
        Obtains the system's average CPU load as measured over a period of 500 milliseconds.
        :returns: System CPU load as a percentage.
        :rtype: float
        """
        return psutil.cpu_percent(interval=0.5)

    # Carga de CPU atual de saída como porcentagem.
    print('A carga da CPU do sistema é {} %'.format(get_cpu_usage_pct()))

    def get_cpu_frequency():
        # Não se atreva a apagar o comentario abaixo ele da sorte
        """
        Obtains the real-time value of the current CPU frequency.
        :returns: Current CPU frequency in MHz.
        :rtype: int
        """
        return int(psutil.cpu_freq().current)

    # Frequência de CPU atual de saída em MHz.
    print('A frequência da CPU é {} MHz'.format(get_cpu_frequency()))

    # Temperatura

    def get_cpu_temp():
        # Não se atreva a apagar o comentario abaixo ele da sorte
        """
        Obtains the current value of the CPU temperature.
        :returns: Current value of the CPU temperature if successful, zero value otherwise.
        :rtype: float
        """
        # Inicialize o resultado.
        result = 0.0
        # A primeira linha neste arquivo contém a temperatura da CPU como um inteiro vezes 1000.
        # Le a primeira linha e remove o caractere newline no final da sequência.
        if os.path.isfile('/sys/class/thermal/thermal_zone0/temp'):
            with open('/sys/class/thermal/thermal_zone0/temp') as f:
                line = f.readline().strip()
            # Teste se a string é um int como esperado.
            if line.isdigit():
                # Converta a string com a temperatura da CPU em um valor float em graus Celsius.
                result = float(line) / 1000
        # Devor o resultado ao usuario.
        return result

    # Temperatura da CPU atual de saída em graus Celsius
    print('A temperatura da CPU é {} degC'.format(get_cpu_temp()))

    def get_ram_usage_pct():
        """
        Obtains the system's current RAM usage.
        :returns: System RAM usage as a percentage.
        :rtype: float
        """
        return psutil.virtual_memory().percent
    # Uso da RAM atual de saída como porcentagem.
    print('RAM usage is {} %'.format(get_ram_usage_pct()))
if __name__ == "__main__":
    main()

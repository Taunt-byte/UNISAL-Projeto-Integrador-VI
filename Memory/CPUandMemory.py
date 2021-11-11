#!/usr/bin/env python3
import psutil
import os

def main():
    def get_cpu_usage_pct():
        """
        Obtains the system's average CPU load as measured over a period of 500 milliseconds.
        :returns: System CPU load as a percentage.
        :rtype: float
        """
        return psutil.cpu_percent(interval=0.5)

    # Output current CPU load as a percentage.
    print('System CPU load is {} %'.format(get_cpu_usage_pct()))

    def get_cpu_frequency():
        """
        Obtains the real-time value of the current CPU frequency.
        :returns: Current CPU frequency in MHz.
        :rtype: int
        """
        return int(psutil.cpu_freq().current)

    # Output current CPU frequency in MHz.
    print('CPU frequency is {} MHz'.format(get_cpu_frequency()))

    def get_cpu_temp():
        """
        Obtains the current value of the CPU temperature.
        :returns: Current value of the CPU temperature if successful, zero value otherwise.
        :rtype: float
        """
        # Initialize the result.
        result = 0.0
        # The first line in this file holds the CPU temperature as an integer times 1000.
        # Read the first line and remove the newline character at the end of the string.
        if os.path.isfile('/sys/class/thermal/thermal_zone0/temp'):
            with open('/sys/class/thermal/thermal_zone0/temp') as f:
                line = f.readline().strip()
            # Test if the string is an integer as expected.
            if line.isdigit():
                # Convert the string with the CPU temperature to a float in degrees Celsius.
                result = float(line) / 1000
        # Give the result back to the caller.
        return result

    # Output current CPU temperature in degrees Celsius
    print('CPU temperature is {} degC'.format(get_cpu_temp()))
if __name__ == "__main__":

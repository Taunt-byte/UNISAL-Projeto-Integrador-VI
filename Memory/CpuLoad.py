#!/usr/bin/env python3
import psutil


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

if __name__ == "__main__":
    main()
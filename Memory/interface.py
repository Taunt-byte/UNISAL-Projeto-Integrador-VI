"""Janela que mostra CPU e RAM atualizando a cada segundo."""
try:
    import FreeSimpleGUI as sg   # fork gratuito e compatível do PySimpleGUI
except ImportError:
    import PySimpleGUI as sg

import CPUandMemory as monitor

sg.theme('DarkAmber')

layout = [
    [sg.Text('Monitor de CPU e Memória', font=('Arial', 14))],
    [sg.Text('CPU:', size=(14, 1)), sg.ProgressBar(100, size=(25, 15), key='-CPU-BAR-'), sg.Text('', size=(8, 1), key='-CPU-')],
    [sg.Text('RAM:', size=(14, 1)), sg.ProgressBar(100, size=(25, 15), key='-RAM-BAR-'), sg.Text('', size=(8, 1), key='-RAM-')],
    [sg.Text('Frequência:', size=(14, 1)), sg.Text('', key='-FREQ-')],
    [sg.Text('Temperatura:', size=(14, 1)), sg.Text('', key='-TEMP-')],
    [sg.Button('Sair')],
]

window = sg.Window('Projeto Integrador VI - CPU e RAM', layout, finalize=True)

while True:
    event, _ = window.read(timeout=500)  # get_cpu_usage_pct já espera 0,5 s → ~1 atualização por segundo
    if event in (sg.WIN_CLOSED, 'Sair'):
        break
    cpu = monitor.get_cpu_usage_pct()
    ram = monitor.get_ram_usage_pct()
    temp = monitor.get_cpu_temp()
    window['-CPU-BAR-'].update(cpu)
    window['-CPU-'].update(f'{cpu:.1f} %')
    window['-RAM-BAR-'].update(ram)
    window['-RAM-'].update(f'{ram:.1f} %')
    window['-FREQ-'].update(f'{monitor.get_cpu_frequency()} MHz')
    window['-TEMP-'].update(f'{temp:.1f} °C' if temp is not None else 'indisponível')

window.close()

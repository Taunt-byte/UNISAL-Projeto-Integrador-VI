<p align="center">
  <img src="img/Logo.png" height="140" alt="Logo do projeto" />
</p>

<h1 align="center">NetMonitor — Controle de tráfego de redes corporativas</h1>

<p align="center">
  Projeto Integrador VI · Engenharia da Computação · UNISAL · jul–out 2021<br>
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Flask-000000?logo=flask">
  <img src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite">
  <img src="https://img.shields.io/badge/Chart.js-FF6384?logo=chartdotjs&logoColor=white">
  <img src="https://img.shields.io/badge/Bootstrap_5-7952B3?logo=bootstrap&logoColor=white">
</p>

Sistema web de monitoramento de redes corporativas que registra o tráfego de rede, a disponibilidade
dos servidores e os dispositivos que acessam o sistema. A partir desses dados é possível identificar
oportunidades de **redução do consumo de dados** e, consequentemente, **de custos**.

![Visão geral](img/prints/visao-geral.png)

## Funcionalidades

- **Tráfego de rede em tempo real** — velocidade de download/upload por interface, total consumido,
  erros e pacotes descartados, conexões ativas e **projeção de consumo mensal** no ritmo atual.
- **Monitoramento de servidores** — testa a conexão TCP com servidores e serviços cadastrados
  (sites, DNS, impressoras, SSH, área de trabalho remota…) a cada 30 s, mostrando status, latência,
  histórico e disponibilidade (%). Servidores podem ser adicionados/removidos pela interface.
- **CPU e memória** do servidor em gráficos ao vivo.
- **Alertas automáticos** — servidor fora do ar, latência alta, CPU ou memória acima do limite.
- **Registro de dispositivos** — IP, geolocalização, sistema operacional e navegador de cada acesso,
  com gráficos por sistema, navegador, país, horário e páginas mais acessadas.
- **Modo demonstração** — gera acessos fictícios (marcados como "demo") para apresentar o painel.
- **API REST em JSON** que alimenta todos os gráficos.

| Tráfego de rede | Servidores | Dispositivos |
|---|---|---|
| ![Rede](img/prints/rede.png) | ![Servidores](img/prints/servidores.png) | ![Dispositivos](img/prints/dispositivos.png) |

## Como rodar

Pré-requisito: [Python 3.9+](https://www.python.org/downloads/) (no Windows, marque *Add Python to PATH*).

**Windows:** dois cliques em `Traffic\iniciar.bat`.

**Qualquer sistema:**

```bash
cd Traffic
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py                  # acesse http://127.0.0.1:5000
```

Para que outros dispositivos da rede (celulares, outros PCs) acessem e apareçam no painel:
`python app.py --rede` e abra `http://IP_DO_COMPUTADOR:5000` (libere a porta 5000 no firewall).

O banco SQLite é criado automaticamente na primeira execução.

## Arquitetura

```
Navegador ──(HTML + Chart.js, atualiza a cada 2–10 s)──► Flask (app.py)
                                                          │
                     ┌────────────────────────────────────┼─────────────────────────┐
                     ▼                                    ▼                         ▼
        monitor.py · SystemMonitor            monitor.py · ServerChecker      dbsetup.py · SQLite
        (thread: psutil a cada 2 s —          (thread: conexão TCP a cada     (sessões, páginas,
         CPU, RAM, bytes por interface)        30 s — status e latência)        servidores)
```

| Rota | Descrição |
|---|---|
| `/` | Visão geral: KPIs, tráfego, CPU/RAM, alertas e servidores |
| `/rede` | Tráfego por interface e projeção de consumo |
| `/servidores` | Status, latência e disponibilidade dos servidores |
| `/dashboard` | Dispositivos que acessaram o sistema |
| `/api/system` · `/api/servers` · `/api/sessions` · `/api/stats` · `/api/charts` · `/api/alerts` | API JSON |

## Estrutura

```
Traffic/
├── app.py            # rotas Flask e API
├── monitor.py        # coleta de métricas e verificação de servidores (threads)
├── dbsetup.py        # banco de dados SQLite
├── templates/        # páginas (Jinja2 + Bootstrap 5)
└── static/           # CSS e JavaScript (gráficos)
Memory/               # versão desktop do monitor de CPU/RAM (FreeSimpleGUI)
```

## Monitor desktop de CPU e RAM

```bash
cd Memory
pip install -r requirements.txt
python interface.py
```

## Histórico

A versão original (2021) usava o serviço Pusher e a API iplocate.io, que deixaram de funcionar.
Em 2026 o projeto foi revisado: as dependências externas pagas foram removidas, foram adicionados o
monitoramento real de tráfego de rede, de servidores e de recursos do sistema, alertas, gráficos e
uma nova interface.

## Bibliografia

- [Bóson Treinamentos — Redes de computadores](https://www.youtube.com/watch?v=v3zVT4HJxYI)
- [Flyner Portugal](https://www.youtube.com/watch?v=z96M6O7mMhQ)
- [Documentação do psutil](https://psutil.readthedocs.io/)
- [Documentação do Flask](https://flask.palletsprojects.com/)

# Guia do Backend do Dashboard

## Visao geral

O backend do dashboard fica em `software/dashboard/backend/backend.py` e centraliza o estado da aplicacao, a classificacao do sistema e os eventos exibidos na interface.

Hoje o fluxo e este:

1. O Streamlit inicializa o `session_state`.
2. `init_dashboard_state()` garante que as estruturas basicas existam.
3. `tick()` adiciona um novo ponto de historico.
4. `build_snapshot()` monta os valores prontos para a tela.
5. `app.py` usa esse snapshot para renderizar os cards, graficos e alarmes.

## Estrutura das funcoes

### `resolve_state_image(state: str) -> Path`
Seleciona a imagem do estado termico da incubadora.

- Entrada: um texto como `frio`, `calor` ou `ideal`.
- Saida: caminho da imagem correspondente em `components/img/`.
- Objetivo: trocar a imagem da incubadora conforme a temperatura atual.

### `init_dashboard_state(session_state) -> None`
Inicializa o estado da sessao do Streamlit.

- Cria `history` com dados simulados de PWM e temperatura.
- Inicializa `fan_failure`, `system_failure` e `automatic_process`.
- Cria a lista `events` e registra o evento inicial do dashboard.
- Objetivo: deixar a tela pronta para funcionar sem depender de variaveis anteriores.

### `add_event(session_state, message: str, level: str = "info") -> None`
Adiciona um evento na lista de alarmes.

- Guarda horario, mensagem e nivel do evento.
- Mantem apenas os 6 eventos mais recentes.
- Objetivo: criar um historico curto e legivel para a interface.

### `tick(session_state) -> None`
Atualiza o historico com uma nova amostra.

- Usa `append_sample()` para incluir novo PWM e nova temperatura.
- Leva em conta `fan_failure` e `system_failure`.
- Objetivo: simular o comportamento dinamico do sistema no dashboard atual.

### `compute_system_state(session_state) -> tuple[str, str]`
Define o estado textual e o tom visual do sistema.

- Retorna `("Alerta", "alert")` se houver falha critica.
- Retorna `("Alerta", "warn")` se houver falha da ventoinha.
- Retorna `("Normal", "ok")` se estiver tudo certo.
- Objetivo: padronizar a leitura do estado do sistema na UI.

### `compute_backend_state(history: dict[str, list[float]]) -> str`
Classifica o estado termico pela temperatura mais recente.

- Abaixo de 36.8: `frio`
- Acima de 37.2: `calor`
- Entre esses limites: `ideal`
- Objetivo: escolher a imagem do estado termico e apoiar a visualizacao.

### `status_text(session_state) -> str`
Retorna uma frase curta de status.

- `Falha Crítica` quando o sistema esta em falha critica.
- `Falha Ventoinha` quando a ventoinha esta em falha.
- `Sistema Estável` quando nao ha falhas.
- Objetivo: mostrar um resumo rapido no topo do dashboard.

### `toggle_fan_failure(session_state) -> None`
Alterna a falha da ventoinha.

- Desliga `automatic_process`.
- Inverte o valor de `fan_failure`.
- Registra evento de ativacao ou normalizacao.
- Objetivo: simular um alarme operacional.

### `toggle_system_failure(session_state) -> None`
Alterna a falha critica do sistema.

- Desliga `automatic_process`.
- Inverte o valor de `system_failure`.
- Registra evento de ativacao ou normalizacao.
- Objetivo: simular uma falha grave do processo.

### `reset_system(session_state) -> None`
Reinicia as falhas do sistema.

- Desliga `automatic_process`.
- Remove `fan_failure` e `system_failure`.
- Registra o evento de reset.
- Objetivo: voltar o dashboard para o estado normal.

### `build_snapshot(session_state) -> dict[str, Any]`
Monta um dicionario com os dados prontos para a interface.

- `latest_pwm`
- `latest_temp`
- `setpoint`
- `state_label`
- `state_tone`
- `status_text`
- `backend_state`
- Objetivo: concentrar em um unico retorno tudo o que `app.py` precisa para renderizar a tela.

## Sobre dados em tempo real

No estado atual, o dashboard **nao esta recebendo dados reais externos a cada 1 segundo**. Ele esta simulando a evolucao do sistema com `tick()` e `append_sample()`.

O que isso significa na pratica:

- Se a pagina for rerenderizada, um novo ponto pode ser gerado pela simulacao.
- Se o dado real vier de um hardware, o backend precisa buscar esse valor em uma fonte externa em vez de gerar valores aleatorios.
- O Streamlit, sozinho, nao faz polling continuo automaticamente neste arquivo.


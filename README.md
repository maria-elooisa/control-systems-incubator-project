# Control System Incubator Project

Projeto desenvolvido para aplicação prática dos conceitos de Sistemas de Controle,
integrando hardware e software para monitoramento e controle térmico de uma incubadora com lâmpada aquecedora.

## Objetivo

Desenvolver um sistema capaz de:

- Monitorar temperatura em tempo real
- Controlar o aquecimento da lâmpada via PWM
- Aplicar conceitos de malha de controle
- Modelar o sistema com diagramas de blocos e Transformada de Laplace
- Exibir dados em dashboard para análise

---

## Arquitetura do Sistema

### Componentes

- Sensor de temperatura
- Lâmpada aquecedora
- Microcontrolador (Arduino/ESP32)
- Dashboard de monitoramento
- Atuador com controle PWM

---

## Diagrama de Blocos

[Inserir imagem do diagrama aqui]

Exemplo conceitual:

Setpoint → Controlador → PWM → Lâmpada → Temperatura → Sensor → Feedback

---

## Fluxograma de Controle

[Inserir fluxograma aqui]

Lógica do sistema:

1. Ler temperatura
2. Comparar com referência
3. Ajustar duty cycle PWM
4. Atualizar dashboard
5. Repetir processo

---

## Monitoramento em Tempo Real

O dashboard exibe:

- Temperatura atual
- Temperatura desejada
- Duty cycle do PWM
- Histórico de temperatura
- Resposta dinâmica do sistema

---

## Modelagem Matemática

Aplicações da disciplina:

- Função de transferência
- Transformada de Laplace
- Resposta temporal
- Estabilidade do sistema

---

## Tecnologias Utilizadas

- Arduino
- Python
- Sensores térmicos
- PWM
- Dashboard

---

## Resultados Esperados

- Controle estável da temperatura
- Menor oscilação térmica
- Visualização em tempo real
- Validação dos conceitos de controle

---

## Equipe

Integrantes do projeto:
- Amanda Ballet
- Bruno da Silva
- Isabella Diaz 
- Maria Eloisa da Silva
- Thiago Shiromoto

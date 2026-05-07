# Primeiros Passos - Control System Incubator

Guia completo para configurar o ambiente e executar o dashboard do projeto.

---

## 📋 Pré-requisitos

- **Python 3.8+** instalado na sua máquina
- **pip** (gerenciador de pacotes Python) - geralmente vem com Python
- **Terminal/CMD** para executar comandos

### Verificar versão do Python

```bash
python --version
```

ou

```bash
python3 --version
```

---

## 🚀 Passo 1: Criar um Ambiente Virtual

Um ambiente virtual isolado evita conflitos de dependências com outros projetos. Por isso entre na pasta do projeto e crie:

### No macOS ou Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### No Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

**Pronto!** Você verá `(venv)` no início da linha do terminal quando estiver ativado.

---

## 📦 Passo 2: Instalar as Bibliotecas Necessárias

Com o ambiente virtual ativado, instale as dependências do projeto:

```bash
cd software/dashboard
pip install -r requirements.txt
```

As bibliotecas instaladas serão:
- **streamlit** - framework para criar o dashboard
- **plotly** - gráficos interativos
- **numpy** - computações numéricas
- **pyserial** - comunicação com dispositivos seriais (Arduino/ESP32)

---

## 📁 Passo 3: Navegar para a Pasta do Dashboard

Certifique-se de estar na pasta correta do projeto:

```bash
cd software/dashboard
```

Você deve estar na pasta que contém o arquivo `app.py`.

---

## ▶️ Passo 4: Executar o Dashboard (Streamlit)

Com o ambiente ativado e dentro da pasta dashboard, execute:

```bash
streamlit run app.py
```

**O que acontece:**
- Streamlit abrirá automaticamente uma janela do navegador
- Se não abrir, acesse: `http://localhost:8501`
- O dashboard estará pronto para monitorar a temperatura em tempo real

---

## 📊 Usando o Dashboard

O dashboard exibe:
- ✅ Temperatura atual
- ✅ Temperatura desejada
- ✅ Duty cycle do PWM
- ✅ Histórico de temperatura
- ✅ Resposta dinâmica do sistema

---

## 🛑 Parar o Dashboard

Pressione `Ctrl + C` no terminal para interromper a execução.

---

## 🔄 Ativar o Ambiente em Sessões Futuras

Cada vez que abrir um novo terminal, você precisará ativar o ambiente:

### macOS ou Linux:
```bash
source venv/bin/activate
```

### Windows:
```bash
venv\Scripts\activate
```

---

## 🐛 Resolvendo Problemas Comuns

### "Comando streamlit não encontrado"
- Certifique-se de que o ambiente virtual está ativado (você vê `(venv)` no terminal?)
- Reinstale as dependências: `pip install -r requirements.txt`

### "Módulo não encontrado"
- Verifique se está na pasta `software/dashboard`
- Reinstale os pacotes: `pip install --upgrade -r requirements.txt`

### Porta 8501 já está em uso
- Execute streamlit em uma porta diferente:
  ```bash
  streamlit run app.py --server.port 8502
  ```

---

## 📝 Resumo Rápido

```bash
# 1. Navegar para o projeto
cd /Incubadora/control-systems-incubator-project

# 2. Ativar ambiente virtual
source venv/bin/activate

# 3. Ir para a pasta dashboard
cd software/dashboard

# 4. Instalar dependências (primeira vez)
pip install -r requirements.txt

# 5. Rodar streamlit
streamlit run app.py
```

---

## 🎯 Próximas Etapas

Após configurar o ambiente:
1. Acesse `http://localhost:8501`
2. Explore o dashboard
3. Conecte o hardware (Arduino/ESP32) se disponível
4. Monitore a temperatura em tempo real

---

**Dúvidas?** Consulte a documentação do Streamlit: https://docs.streamlit.io/

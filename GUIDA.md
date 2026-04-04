# Crypto Trading Agents — Guida Completa

## 📱 Da Mobile (Android / iOS)

### Opzione A: GitHub Actions (Consigliata — Nessuna App Necessaria)

Questa è la via più semplice. Non installi nulla. L'analisi gira sui server di GitHub.

**Passo 1 — Fork del repo**

1. Apri il browser sul telefono
2. Vai su: https://github.com/Lolarok/crypto-trading-agents
3. Tocca **Fork** (icona biforcazione in alto a destra)
4. Conferma il fork nel tuo account

**Passo 2 — Aggiungi le API Key come Secrets**

1. Nel tuo fork, vai su **Settings** → **Secrets and variables** → **Actions**
2. Tocca **New repository secret** e aggiungi questi due:

| Nome | Valore |
|------|--------|
| `OPENROUTER_API_KEY` | La tua chiave OpenRouter (sk-or-v1-...) |
| `CMC_API_KEY` | La tua chiave CoinMarketCap |

**Passo 3 — Avvia un'analisi**

1. Vai su **Actions** (tab in alto)
2. Clicca **Daily Crypto Analysis** a sinistra
3. Tocca **Run workflow** (bottone verde a destra)
4. Inserisci:
   - **crypto**: `bitcoin` (o `ethereum`, `solana`, ecc.)
   - **date**: lascia vuoto per oggi
5. Tocca **Run workflow**

**Passo 4 — Leggi i risultati**

1. Clicca sul workflow run che appare
2. Clicca su **analyze** → **Run analysis**
3. Scorri fino ai log per vedere il risultato
4. Oppure vai in **Code** → cartella `results/` per il JSON completo

**Passo 5 — Analisi automatica quotidiana**

Il workflow è già configurato per girare ogni giorno alle 07:00 UTC su Bitcoin, Ethereum e Solana. Non devi fare nulla.

---

### Opzione B: Termux su Android (CLI Completa)

Per eseguire il tool direttamente dal telefono.

**Passo 1 — Installa Termux**

1. Scarica **Termux** da F-Droid (NON dal Play Store): https://f-droid.org/packages/com.termux/
2. Apri Termux

**Passo 2 — Setup ambiente**

```bash
pkg update && pkg upgrade
pkg install python git
pip install --upgrade pip
```

**Passo 3 — Clona e installa**

```bash
git clone https://github.com/Lolarok/crypto-trading-agents.git
cd crypto-trading-agents
pip install -e .
```

**Passo 4 — Configura le chiavi**

```bash
cat > .env << 'EOF'
OPENROUTER_API_KEY=sk-or-v1-TUA-CHIAVE-QUI
CMC_API_KEY=tua-chiave-cmc-qui
CRYPTO_LLM_PROVIDER=openrouter
CRYPTO_DEEP_THINK_LLM=openai/gpt-4o
CRYPTO_QUICK_THINK_LLM=openai/gpt-4o-mini
EOF
```

**Passo 5 — Esegui**

```bash
python -m cli.main bitcoin
```

> **Nota:** L'installazione può richiedere 5-10 minuti su Termux perché scarica le dipendenze Python. Assicurati di avere spazio e Wi-Fi.

---

### Opzione C: Google Colab (Niente Installazione)

Esegui nel browser, anche dal telefono.

**Passo 1 — Apri Colab**

1. Vai su https://colab.research.google.com
2. Clicca **New notebook**

**Passo 2 — Incolla questo codice**

```python
# Cell 1: Install
!git clone https://github.com/Lolarok/crypto-trading-agents.git
%cd crypto-trading-agents
!pip install -e . -q

# Cell 2: Config
import os
os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-TUA-CHIAVE"  # ← La tua chiave
os.environ["CMC_API_KEY"] = "tua-chiave-cmc"               # ← La tua chiave
os.environ["CRYPTO_LLM_PROVIDER"] = "openrouter"
os.environ["CRYPTO_DEEP_THINK_LLM"] = "openai/gpt-4o"
os.environ["CRYPTO_QUICK_THINK_LLM"] = "openai/gpt-4o-mini"

# Cell 3: Run Analysis
from crypto_trading_agents.graph.trading_graph import CryptoTradingAgentsGraph
from crypto_trading_agents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openrouter"
config["deep_think_llm"] = "openai/gpt-4o"
config["quick_think_llm"] = "openai/gpt-4o-mini"
config["selected_analysts"] = ["market", "sentiment", "fundamentals", "onchain"]
config["max_debate_rounds"] = 1
config["max_risk_discuss_rounds"] = 1

ta = CryptoTradingAgentsGraph(debug=True, config=config)
final_state, decision = ta.propagate("Bitcoin", "bitcoin", "2026-03-29")
print(f"\n🎯 SIGNAL: {decision}")
print(f"\n📋 Decision:\n{final_state.get('final_trade_decision', 'N/A')[:800]}")
```

3. Premi **Ctrl+Invio** su ogni cella

---

## 💻 Da Windows

### Passo 1 — Installa Python

1. Vai su https://www.python.org/downloads/
2. Clicca **Download Python 3.12.x** (o 3.11+)
3. **IMPORTANTE:** Nell'installer, spunta ✅ **"Add Python to PATH"**
4. Clicca **Install Now**
5. Riavvia il PC

**Verifica l'installazione:**
Apri **Prompt dei comandi** (Win+R → scrivi `cmd` → Invio) e scrivi:
```cmd
python --version
```
Dovrebbe mostrare `Python 3.11.x` o `3.12.x`

### Passo 2 — Installa Git

1. Vai su https://git-scm.com/download/win
2. Scarica e installa con le impostazioni predefinite
3. Riavvia il Prompt dei comandi

### Passo 3 — Clona il progetto

Apri **Prompt dei comandi** o **PowerShell**:

```cmd
cd %USERPROFILE%\Desktop
git clone https://github.com/Lolarok/crypto-trading-agents.git
cd crypto-trading-agents
```

### Passo 4 — Installa le dipendenze

```cmd
pip install -e .
```

Se dà errori di permessi:
```cmd
pip install --user -e .
```

### Passo 5 — Configura le chiavi API

Crea un file `.env` nella cartella del progetto:

```cmd
notepad .env
```

Incolla dentro (sostituendo con le tue chiavi):
```
OPENROUTER_API_KEY=sk-or-v1-TUA-CHIAVE-QUI
CMC_API_KEY=tua-chiave-cmc-qui
CRYPTO_LLM_PROVIDER=openrouter
CRYPTO_DEEP_THINK_LLM=openai/gpt-4o
CRYPTO_QUICK_THINK_LLM=openai/gpt-4o-mini
```

Salva e chiudi.

### Passo 6 — Esegui un'analisi

```cmd
python -m cli.main bitcoin
```

**Altri esempi:**

```cmd
REM Analisi Ethereum
python -m cli.main ethereum

REM Bitcoin con data specifica
python -m cli.main bitcoin --date 2026-03-29

REM Con Claude (se hai ANTHROPIC_API_KEY)
python -m cli.main bitcoin --provider anthropic

REM Con debug per vedere il ragionamento degli agenti
python -m cli.main bitcoin --debug

REM Solo analisi tecnica + sentimentale (più veloce e economico)
python -m cli.main bitcoin --analysts market sentiment

REM Con più round di dibattito (più approfondito)
python -m cli.main bitcoin --debate-rounds 3 --risk-rounds 2
```

### Passo 7 — Leggi i risultati

I risultati vengono salvati in:
```
crypto-trading-agents\results\bitcoin\analysis_2026-03-29.json
```

Puoi aprire il file JSON con qualsiasi editor di testo (Notepad, VS Code).

---

## 🔑 Dove Ottienere le Chiavi API

### OpenRouter (LLM — per il ragionamento degli agenti)

1. Vai su https://openrouter.ai
2. Registrati (puoi usare Google/GitHub)
3. Vai su **Settings** → **Keys**
4. Clicca **Create Key**
5. Copia la chiave (inizia con `sk-or-v1-...`)
6. **Gratis:** $1 di crediti alla registrazione, basta per ~50 analisi con gpt-4o-mini

### CoinMarketCap (Dati di mercato)

1. Vai su https://coinmarketcap.com/api/
2. Clicca **Get Your API Key Now**
3. Registrati (gratuito)
4. Vai su **Dashboard** → copia la **API Key**
5. **Gratis:** 10,000 chiamate/mese, 30 chiamate/minuto

---

## 💰 Quanto Costa

| Componente | Costo per analisi |
|-----------|------------------|
| Dati CoinMarketCap | Gratis (10k/mese) |
| Dati CoinGecko | Gratis (rate limit) |
| Dati DeFiLlama | Gratis |
| LLM (GPT-4o-mini) | ~$0.005 |
| LLM (GPT-4o) | ~$0.03 |
| **Totale per analisi** | **~$0.01-0.04** |

Con $1 di crediti OpenRouter puoi fare ~25-100 analisi.

---

## 🔧 Risoluzione Problemi

### "python non riconosciuto come comando"
- Reinstalla Python e assicurati di spuntare ✅ "Add Python to PATH"
- Oppure usa `python3` invece di `python`

### "Errore 402 — not enough credits"
- Il tuo credito OpenRouter è finito
- Vai su https://openrouter.ai/settings/credits e aggiungi fondi

### "CoinGecko rate limited"
- Normale con il piano gratuito. CMC ha limiti migliori
- L'analisi continuerà con i dati disponibili

### "pip non trovato"
```cmd
python -m pip install -e .
```

### "Errore di connessione"
- Controlla la connessione internet
- Le API CoinGecko/CMC potrebbero essere temporaneamente lente

---

## 📊 Cosa Produce l'Analisi

Ogni esecuzione produce un report completo con:

1. **Market Analyst** — Indicatori tecnici (RSI, MACD, Bollinger, trend)
2. **Sentiment Analyst** — Fear & Greed, dominanza BTC, mood del mercato
3. **News Analyst** — Ultime notizie da CoinDesk, CoinTelegraph, The Block
4. **Fundamentals Analyst** — TVL DeFi, tokenomics, attività sviluppatori
5. **On-Chain Analyst** — Supply dynamics, struttura di mercato

Poi:
6. **Bull vs Bear Debate** — Dibattito pro/contro investimento
7. **Trader** — Piano di trading concreto (entry, stop loss, take profit)
8. **Risk Debate** — Analisi del rischio da 3 prospettive
9. **Portfolio Manager** — Decisione finale: **BUY / SELL / HOLD**

---

## 🤖 Analisi Automatica con GitHub Actions

Il repo include un workflow che esegue l'analisi automaticamente ogni giorno alle 07:00 UTC.

**Per abilitarlo:**
1. Fork del repo
2. Aggiungi `OPENROUTER_API_KEY` e `CMC_API_KEY` come Secrets (vedi sopra)
3. Il workflow parte automaticamente

**Per eseguirlo manualmente:**
1. Vai su **Actions** → **Daily Crypto Analysis** → **Run workflow**

**Cosa analizza di default:** Bitcoin, Ethereum, Solana (configurabile nel file `.github/workflows/daily-analysis.yml`)

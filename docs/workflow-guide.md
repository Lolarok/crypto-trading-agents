# 🤖 Guida alle Workflow - Crypto Trading Agents

Benvenuto! Questa guida ti spiega come utilizzare le GitHub Actions per automatizzare l'analisi crypto e deployare la documentazione.

## 📅 Workflow Disponibili

### 1. Daily Crypto Analysis
- **Nome file:** `.github/workflows/daily-analysis.yml`
- **Trigger:** 
  - Schedule: Ogni giorno alle 07:00 UTC
  - Manuale: `workflow_dispatch`
- **Funzione:** Esegue analisi multi-agent su Bitcoin, Ethereum, Solana

### 2. Deploy to GitHub Pages
- **Nome file:** `.github/workflows/deploy.yml`
- **Trigger:** Push su main o manuale
- **Funzione:** Pubblica la documentazione su GitHub Pages

## 🔧 Come Avviare le Analisi

### A. Analisi Automatica Giornaliera
La workflow gira automaticamente ogni giorno alle 07:00 UTC. Non richiede configurazione.

### B. Analisi Manuale (UI)
1. Vai su **Actions** → **Daily Crypto Analysis**
2. Clicca **Run workflow**
3. Compila i campi:
   - **crypto**: `bitcoin` (o `ethereum`, `solana`)
   - **date**: `YYYY-MM-DD` (lascia vuoto per data odierna)
4. Clicca **Run workflow**

### C. Analisi Manuale (API)
```bash
# Esempio: analisi manuale su Bitcoin
curl -X POST https://api.github.com/repos/Lolarok/crypto-trading-agents/actions/workflows/daily-analysis.yml/dispatch \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -d '{"ref":"main","inputs":{"crypto":"bitcoin"}}'
```

### D. Analisi Manuale (CLI)
```bash
# Installa GitHub CLI se non hai
# https://cli.github.com/

gh workflow run daily-analysis.yml --ref main \
  --field crypto=bitcoin \
  --field date=2026-04-10
```

## 🔐 Configurazione Richiesta

### Segreto: GOOGLE_API_KEY
1. Vai su **Settings** → **Secrets and variables** → **Actions**
2. Crea nuovo secret: `GOOGLE_API_KEY`
3. Valore: la tua chiave API Google (da https://aistudio.google.com)
4. Clicca **Add secret**

**Perché?** La workflow usa modelli Google Gemini per l'analisi.

### Segreto: GITHUB_TOKEN (già presente)
GitHub fornisce automaticamente un token per operazioni sui repository.

## 📊 Monitoraggio e Risultati

### 1. Monitora l'Esecuzione
- Vai su **Actions** → **Daily Crypto Analysis**
- Seleziona la run in corso
- Visualizza log in tempo reale
- Risolvi eventuali errori

### 2. Scarica i Risultati
- Dopo il completamento, vai su **Artifacts**
- Scarica: `analysis-bitcoin-2026-04-11`
- Contiene:
  - `analysis.json` (dati strutturati)
  - `report.md` (report leggibile)
  - `trade_signal.txt` (segnale operativo)

### 3. Visualizza su Repository
I risultati vengono committati automaticamente in `results/`:
- https://github.com/Lolarok/crypto-trading-agents/tree/main/results

## 🌐 GitHub Pages per Documentazione

### Abilita GitHub Pages
1. Vai su **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `/docs (root)` (crea branch `docs` se non esiste)
4. Salva

### Crea Documentazione
Crea una cartella `docs/` nella root con:
- `index.html` - Pagina iniziale
- `guide.md` - Guida all'uso
- `api.md` - Documentazione API

Esempio minimo:
```html
<!-- docs/index.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Crypto Trading Agents</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; }
    .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
    .content { max-width: 800px; margin: 20px auto; }
  </style>
</head>
<body>
  <div class="header">
    <h1>📊 Crypto Trading Agents</h1>
    <p>Framework multi-agent per analisi crypto automatizzata</p>
  </div>
  <div class="content">
    <h2>📈 Segnale Recente</h2>
    <p>Bitcoin: <strong>BUY</strong> @ $68,432</p>
    <h2📚 Documentazione</h2>
    <ul>
      <li><a href="guide.md">Guida all'uso</a></li>
      <li><a href="api.md">Documentazione API</a></li>
      <li><a href="https://lolarok.github.io/crypto-trading-agents/">Vai al sito</a></li>
    </ul>
  </div>
</body>
</html>
```

### Aggiorna Automaticamente
Crea un workflow `.github/workflows/docs.yml`:
```yaml
name: Deploy Docs
on:
  push:
    branches: [main]
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install -e .
      - name: Generate documentation
        run: python -m docs.generate
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

## 🚀 Esempi Pratici

### Esempio 1: Analisi su Ethereum manuale
```bash
gh workflow run daily-analysis.yml --ref main \
  --field crypto=ethereum \
  --field date=2026-04-10
```

### Esempio 2: Analisi su Solana con trigger manuale via API
```bash
curl -X POST https://api.github.com/repos/Lolarok/crypto-trading-agents/actions/workflows/daily-analysis.yml/dispatch \
  -H "Authorization: Bearer ghp.your_token_here" \
  -d '{"ref":"main","inputs":{"crypto":"solana"}}'
```

### Esempio 3: Verifica stato segreti
```bash
# Controlla se il segreto è configurato
curl -X GET https://api.github.com/repos/Lolarok/crypto-trading-agents/actions/secrets/GITHUB_TOKEN \
  -H "Authorization: Bearer ghp.your_token_here"
```

## 🐛 Risoluzione Problemi

### Errore: "Skipped — add GOOGLE_API_KEY secret to enable"
- **Causa:** Manca il segreto `GOOGLE_API_KEY`
- **Soluzione:** Configura il segreto in Settings → Secrets

### Errore: "API quota exceeded"
- **Causa:** Superata quota API Google
- **Soluzione:** Aggiungi più modelli, usa cache, riduci frequenza

### Errore: "Command failed with exit code 1"
- **Causa:** Problema nel codice (es. missing dependency)
- **Soluzione:** Controlla log per dettagli, installa dipendenze mancanti

### Errore: "Permission denied"
- **Causa:** Mancano permessi su repository
- **Soluzione:** Verifica che l'account abbia accesso in scrittura

## 📈 Prossimi Passi

1. **Configura il segreto GOOGLE_API_KEY**
2. **Avvia una analisi manuale** per testare
3. **Monitora i risultati** in Actions e repository
4. **Configura GitHub Pages** per documentazione
5. **Crea una dashboard** per visualizzare segnali operativi

---

**Domande?** Controlla la documentazione ufficiale GitHub Actions: https://docs.github.com/en/actions

</main>
</body>
</html>
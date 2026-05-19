# GRACE — Guida operativa per l'analista GRC

**Versione**: Prototype v1.0
**Pubblico**: GRC analyst, Compliance manager, CISO, DPO
**Tempo di lettura**: 25 minuti
**Tempo per essere produttivo**: 1 ora

---

## 1. Cos'è GRACE e cosa NON è

**GRACE** (Governance, Risk, Assurance & Compliance Engine) è una piattaforma AI-assisted per il lavoro quotidiano del compliance team. Sostituisce il foglio Excel "Registro Findings", il SharePoint delle policy, il template Word del DPIA, e i fogli sparsi di risk register con un'unica interfaccia che orchestra Claude (Anthropic) per ridurre il tempo speso in attività ripetitive.

**Cosa GRACE fa bene**:
- Gap analysis multi-framework (10 framework attivi, dall'ISO 27001 all'EU AI Act)
- Mappatura cross-framework automatica (un finding ISO 27001 mostra anche l'impatto su SOC 2, NIST CSF, DORA, ecc.)
- Generazione di documenti di compliance (policy, DPIA, procedure) con qualità "first draft + finetuning umano"
- Risk register strutturato (matrice 5×5, treatment plan, owner)
- Vendor risk assessment guidato (questionario standard + AI summary)
- Policy lifecycle con workflow di acknowledgment
- Incident tracking con countdown automatico GDPR Art.33

**Cosa GRACE NON è**:
- Non sostituisce il giudizio dell'analista — è un copilota, non un autopilota
- Non è ancora un sistema multi-utente con RBAC (single demo user per ora)
- Non si integra automaticamente con AWS/Azure/GCP per evidence collection (roadmap fase 2)
- Non emette certificazioni — l'output va sempre rivisto

---

## 2. Quick start — il tour da 5 minuti

Apri GRACE su `http://localhost:8501` (locale) o sul tuo dominio HTTPS se hai usato il deploy Caddy.

In alto a destra trovi:
- **Language toggle** (EN / IT) — applicato sia all'interfaccia sia ai prompt di Claude
- **Tema chiaro / scuro**

Nella sidebar 10 voci, organizzate per **flusso di valore**:

| Voce | Quando la usi |
|------|---------------|
| 🤖 Ask GRACE | Domande conversazionali, "spiegami questo controllo", mapping ad hoc |
| 📊 Gap Analysis | Audit strutturato di un documento contro un framework |
| 📝 Document Generation | Crei policy, procedure, DPIA partendo da zero |
| 🛡 Governance Dashboard | Tu sei il manager: leggi i KPI all'inizio della giornata |
| 🔍 Finding Registry | Tu sei l'analista: triage dei gap, assegna owner, aggiorna stato |
| 📚 Framework Library | Esplori il catalogo, capisci un controllo prima di un audit |
| 🎲 Risk Management | Aggiorni il registro rischi, treatment plan, residual score |
| 🤝 Vendor Risk | Onboarding di un fornitore, due diligence periodica |
| 📜 Policies | Pubblichi una nuova versione, raccogli acknowledgment |
| 🚨 Incidents | Apri un incidente, scatta il countdown GDPR se richiesto |

Le pagine **non sono in ordine alfabetico per caso**: rispecchiano il ciclo di vita GRC.

---

## 3. Le 10 pagine in dettaglio

### 3.1. 🤖 Ask GRACE — il tuo copilota conversazionale

**Quando usarla**: hai una domanda. Punto. Non vuoi creare un finding, non vuoi avviare un audit. Vuoi solo capire qualcosa o ottenere un'analisi puntuale.

**Esempi reali**:
- *"Spiegami cosa cambia tra NIST CSF 1.1 e 2.0 nella funzione Govern"*
- *"Quali sono i miei finding critici aperti su GDPR?"*
- *"Confronta queste due policy e dimmi dove si contraddicono"* (allegando 2 file)
- *"Il nostro contratto con [vendor X] copre tutti i requisiti GDPR Art.28?"* (allegando il DPA)

**Come funziona**:
1. Clicca **+ New chat** nella colonna sinistra
2. (Opzionale) Espandi **Add context** — incolla testo o carica fino a N file (PDF, DOCX, TXT, XLSX, CSV)
3. (Opzionale) Seleziona un **Framework context** dal dropdown — Claude lo userà come riferimento
4. Scrivi la domanda nell'input in basso e premi Invio
5. La conversazione viene **salvata automaticamente** (lista nella colonna sinistra)

**Cose importanti da sapere**:
- Ask GRACE NON crea finding nel registro. Per quello esiste Gap Analysis.
- Ogni conversazione è persistita: refresh della pagina ed è ancora lì
- Puoi rinominare (✏ Rename) o eliminare (🗑) una conversazione dal pannello sinistro
- Quando alleghi file, GRACE passa automaticamente a un modello più potente (Sonnet) per gestire il contesto più ampio

**Limite operativo**: ogni file viene troncato a 40k caratteri nel prompt. Per documenti grossi, spezza in più file logici o usa Gap Analysis.

---

### 3.2. 📊 Gap Analysis — l'audit strutturato

**Quando usarla**: devi **registrare formalmente** un assessment di compliance. Il risultato popolerà Finding Registry e Governance Dashboard. È l'azione "vera" che lascia traccia.

**Workflow a 4 step** (colonna sinistra):

**Step 1 — Upload evidence**: carica uno o più documenti (anche di tipo misto: policy + risk register + procedura). GRACE li concatena in un unico contesto.

**Step 2 — Choose framework**: dropdown con i 10 framework attivi. La scelta è obbligatoria.

**Step 3 — Optional scope**: se vuoi limitare l'assessment a un sottoinsieme di controlli (es. solo cap. 5 di ISO 27001), apri l'expander e selezionali. Vuoto = analisi completa.

**Step 4 — Run Gap Analysis**: clicca il bottone. Tempo medio 30-60 secondi.

**Risultati** (colonna destra):
- **Executive summary** generato da Claude
- **Coverage score** in percentuale (0-100%)
- **Finding cards** ognuna con: severity badge (critical/high/medium/low), compliance status (compliant/partial/non_compliant/no_evidence/not_applicable), descrizione del gap, evidence trovata vs richiesta, remediation suggerita, regulatory reference

**Cosa fare DOPO un run**:
- **Open in Finding Registry** → vai al registro e fai triage / assegna owner
- **📄 Generate Assessment Report** → esporta un PDF formale (cliente, board, auditor esterno)

**Best practice**: separa gli assessment per "dominio logico". Esempio: non fare 1 sola Gap Analysis su un manuale di 200 pagine; spezza per capitolo. La granularità ti permette di chiudere singoli pezzi senza riaprire tutto.

---

### 3.3. 📝 Document Generation — fabbrica policy assistita

**Quando usarla**: devi creare ex-novo o riformulare un documento (policy, DPIA, IRP, BIA, statement of applicability, code of conduct).

**Workflow**:
1. Seleziona il **tipo di documento** (es. "Information Security Policy", "DPIA", "Incident Response Plan")
2. Aggiungi **contesto opzionale**: paste o file upload (es. policy vecchia da rivedere, output di una gap analysis)
3. Specifica **framework di riferimento** (es. ISO 27001:2022)
4. Clicca **Generate**
5. Ricevi un draft in Markdown, scaricabile come PDF o DOCX

**Tip operativo**: usa Document Generation come **bozza al 70%**. L'output è strutturato e completo, ma deve sempre passare per due step manuali:
- Inserimento dei dati aziendali specifici (nomi, ruoli, sedi, sistemi)
- Review legale (specie per documenti che hanno valenza contrattuale)

---

### 3.4. 🛡 Governance Dashboard — il cruscotto del manager

**Quando usarla**: all'inizio della giornata. È la pagina che apri prima del caffè.

**Cosa vedi**:
- **KPI strip**: totale finding, critici aperti, copertura media per framework
- **Trend**: andamento dei finding nel tempo
- **Top frameworks per gap**: dove sei più scoperto
- **Click-through ai filtri Registry**: clic su un KPI = apri il Registry filtrato

**Cosa NON vedi (per design)**:
- Le conversazioni di Ask GRACE — quelle sono esplorazione, non governance
- I documenti generati ma non assessment-ati

**Per chi è**: CISO / Compliance Manager / Head of Risk. L'analista junior la guarda meno; il responsabile la guarda quotidianamente.

---

### 3.5. 🔍 Finding Registry — la coda di lavoro

**Quando usarla**: è dove vivi come analista. Sostituisce Excel "Findings Tracker" definitivamente.

**Layout**:
- Filtri in alto (framework, verdict, operational status)
- Lista raggruppata **per documento** (un assessment = un gruppo)
- Ogni finding è una card con tutti i campi rilevanti

**Azioni che puoi fare su un finding**:
- Aggiornare l'**operational status** (new → acknowledged → in_progress → resolved → closed; oppure accepted_risk / dismissed)
- Espandere il pannello **🔗 Cross-Framework Impact** per vedere quali controlli di ALTRI framework sono semanticamente equivalenti (la prima espansione richiama Claude, le successive sono istantanee — cache permanente)

**Pattern operativo consigliato**:
1. Filtri per `severity = critical` + `operational_status = new`
2. Per ciascun finding:
   - Apri il pannello cross-framework — se vedi che impatta anche su altri 3 framework, sai che è una **priorità sistemica**, non un singolo gap
   - Aggiorni status a `acknowledged`
   - Assegni owner (campo aggiungibile a roadmap; per ora è un'annotazione manuale)
3. Quando il fix è in corso → `in_progress`
4. Quando hai l'evidenza che chiude il gap → `resolved`
5. Dopo verifica audit → `closed`

**Cross-framework mapping**: questa è una delle feature più potenti di GRACE. Esempio reale: un finding su **ISO 27001 A.5.23** (Information security for use of cloud services) può mostrarti automaticamente:
- SOC 2 CC6.1 (logical access controls) — confidence high
- NIST CSF GV.SC-01 (supply chain risk strategy) — confidence high
- DORA Art.28 (ICT third-party arrangements) — confidence high
- NIS2 Art.21.2.d (supply chain security) — confidence medium
- HIPAA §164.314(a) (business associate contracts) — confidence medium

Fixando 1 controllo, chiudi 5 gap su 5 framework diversi. Questa è la differenza tra fare audit "per compliance" e fare audit "intelligenti".

---

### 3.6. 📚 Framework Library — il catalogo di riferimento

**Quando usarla**: prima di un audit, durante la lettura di un controllo che non ricordi a memoria, quando devi spiegare un requisito a uno stakeholder non-tecnico.

**Cosa contiene**:
- 10 framework attivi con catalogo controlli completo (o rappresentativo per PCI DSS)
- Per ogni controllo: ID canonico, titolo, descrizione, keywords, evidence types attesi
- **"Explain with Claude"** per ottenere una spiegazione contestuale in linguaggio naturale (utile quando i requisiti formali sono criptici)

**Tip**: usa "Explain with Claude" per costruire la slide deck di un kickoff. Copia la spiegazione, è già pronta in italiano se hai impostato la lingua.

---

### 3.7. 🎲 Risk Management — il registro rischi formale

**Quando usarla**: per gestire il **risk register aziendale** in modo strutturato (non più Excel "Top 10 Risks 2026.xlsx").

**Funzionalità chiave**:
- **Matrice 5×5** likelihood × impact con cell colorate per banda di rischio
- **Inherent score** = likelihood × impact (1-25)
- **Residual score** = post-controlli (puoi specificarlo manualmente)
- **Treatment plan**: avoid / transfer / mitigate / accept (le 4 risposte classiche)
- **Owner**, **status**, **linked controls** (riferimenti incrociati a framework attivi)

**Workflow tipo**:
1. Identifica un rischio (es. "Perdita di disponibilità servizio core per attacco ransomware")
2. Crea entry: likelihood=3, impact=5 → inherent_score=15 → banda **HIGH**
3. Treatment plan = **mitigate**, treatment_notes = "Backup offline + DR site + endpoint EDR"
4. Linked controls = ISO27001:2022:A.8.13 (backup), NIST CSF PR.IP-04
5. Dopo implementazione misure, aggiorni residual_score=8 → banda **MEDIUM**

**Vista heatmap**: a colpo d'occhio vedi i rischi concentrati nelle bande critiche (top-right). Quella è la tua to-do list strategica.

---

### 3.8. 🤝 Vendor Risk — due diligence assistita

**Quando usarla**: ogni volta che onboarding un nuovo fornitore che processa dati personali o accede a sistemi critici. E per le revisioni periodiche (12-24 mesi).

**Workflow**:
1. **+ Add Vendor** — inserisci nome, categoria, contatti, contratto URL
2. Apri il vendor → bottone **📋 Assess**
3. Compili il questionario standard a 10 domande (encryption, ISO/SOC certs, breach notification SLA, subprocessor disclosure, audit rights, BCDR, MFA, GDPR DPA, breach history)
4. Per ogni domanda: dropdown **yes / no / partial / unknown** + note opzionali
5. Submit → GRACE:
   - Calcola **risk_score** (0-100, weighted sum)
   - Deriva **risk_tier**: 0-40 critical / 41-60 high / 61-80 medium / 81-100 low
   - Chiama Claude per generare un **AI summary** qualitativo (strengths / risks / next step)

**Best practice**:
- Per vendor con tier `critical` o `high`: contratto deve essere revisionato legalmente, considera audit on-site
- Per tier `low`: documentazione automatica sufficiente, revisione tra 24 mesi
- Il campo **last_assessed_at** drive la KPI "Due for reassessment" (default soglia: 365 giorni)

---

### 3.9. 📜 Policies — lifecycle e acknowledgment

**Quando usarla**: per pubblicare nuove policy aziendali e raccogliere conferma di lettura dai dipendenti (compliance training base).

**Due tab nella stessa pagina**:

**📚 Library** (vista admin):
- Crei una policy: titolo, versione, summary, content in **Markdown** (full editor), effective_date, review_date, owner, status (draft / active / superseded / retired), linked controls
- Assegni la policy a uno o più utenti via input comma-separated (es. `alice@demo, bob@demo, carol@demo`)
- Vedi il count di pending acknowledgments per ciascuna policy

**✅ My Acknowledgments** (vista utente):
- Imposti l'utente di prova (es. `alice@demo`)
- Vedi la lista delle policy pending per quell'utente
- Apri la policy, leggi il contenuto, inserisci una optional signature note, clicchi **✅ Accept this policy**
- Acknowledged history in fondo (collapsable)

**Pattern operativo**: lo usi quando aggiorni un Code of Conduct, una Acceptable Use Policy, una Data Protection Notice. Hai traccia di chi ha letto e quando — buono per audit.

---

### 3.10. 🚨 Incidents — incident management con countdown GDPR

**Quando usarla**: appena qualcosa va storto.

**Severity scale**: low / medium / high / critical

**Category**: security_breach / data_loss / system_outage / policy_violation / third_party / other

**Magia automatica**:
- Se crei un incident con `severity ∈ {high, critical}` E `category ∈ {security_breach, data_loss}`:
  - GRACE imposta automaticamente `breach_notification_required = true`
  - Calcola `regulatory_deadline = reported_at + 72h` (GDPR Art.33)
  - Mostra un **banner rosso** con countdown
- Se la deadline passa senza notification: tag **🔴 OVERDUE**
- Se < 24h alla deadline: tag **⏰ DUE SOON**

**Stati**: open → investigating → contained → resolved → closed

**Campi compilabili durante il lifecycle**:
- `impact_assessment` (cosa è successo, scope)
- `root_cause` (post mortem)
- `remediation` (cosa è stato fatto per non farlo ricapitare)
- `linked_controls`, `linked_findings` (collegamento ad altri moduli)
- `resolved_at`, `breach_notified_at` (timestamps)

**MTTR KPI** (Mean Time To Resolution): GRACE calcola la media dei tempi (closed_at - reported_at) per gli incident chiusi. Metrica da Board.

---

## 4. Workflow end-to-end — i 5 casi d'uso più comuni

### 4.1. "Devo certificarmi ISO 27001:2022 entro 6 mesi"

**Stato iniziale**: hai policy vecchie, nessun risk register, vago set di evidenze.

**Sequenza in GRACE**:
1. **📚 Framework Library** → apri ISO 27001:2022, leggi i 93 controlli, identifica i top 20 priority
2. **📊 Gap Analysis** → carica policy esistenti, runni assessment contro ISO 27001
3. **🔍 Finding Registry** → filtri `severity=critical` → hai la lista lavori prioritari
4. **📝 Document Generation** → generi le policy mancanti (es. Information Security Policy, Acceptable Use, Incident Response Plan)
5. **🎲 Risk Management** → popoli il risk register coi rischi che emergono dai finding
6. **📜 Policies** → pubblichi le policy e raccogli acknowledgments
7. **📊 Gap Analysis** → re-run dopo 30/60/90 giorni per misurare progresso
8. **🛡 Governance Dashboard** → coverage score sale → quando ≥ 85% sei pronto per audit esterno

### 4.2. Audit annuale: documentation pack per il certification body

1. **📊 Gap Analysis** → run completo aggiornato sui framework di scope
2. **🔍 Finding Registry** → tutti i finding in stato `resolved` o `closed` con evidence link
3. **📜 Policies** → tutte attive, last_review_date recente
4. **🚨 Incidents** → lista incidents anno corrente con root cause e remediation
5. **🤝 Vendor Risk** → tutti i critical/high con last_assessed_at < 12 mesi
6. **📝 Document Generation** → genera Statement of Applicability con cross-reference
7. Esporta tutto in PDF (Generate Assessment Report da Gap Analysis + export del Risk Register manuale per ora)

### 4.3. Onboarding nuovo fornitore cloud

1. **🤝 Vendor Risk** → + Add Vendor (nome, contatti)
2. **📋 Assess** → questionario standard
3. Se risk_tier = `critical/high` → torna al fornitore con la lista delle red flag (il vendor card mostra l'AI summary che evidenzia i gap)
4. **📜 Policies** → assegna al fornitore (utente esterno) la policy "Third Party Information Security Requirements"
5. **🎲 Risk Management** → registra il rischio "Third party data processor — [VendorName]" con linked controls a ISO27001:2022:A.5.23 e GDPR:Art.28
6. Set re-assessment a 12 mesi

### 4.4. Data breach: incident response in tempo reale

**Minuto 0-15**: detection
1. **🚨 Incidents** → + Report Incident: title, severity=critical, category=security_breach, reported_by, impact_assessment iniziale
2. GRACE calcola regulatory_deadline = +72h, alza il flag breach_notification_required, banner rosso
3. Status = `investigating`

**Ora 0-24**: contenimento
4. Update incident: impact_assessment dettagliato, status = `contained`

**Ora 24-72**: notifica + remediation
5. Compila root_cause, remediation; quando hai notificato l'autorità (es. Garante per GDPR), set `breach_notified_at`

**Settimana successiva**: lesson learned
6. **🎲 Risk Management** → nuovo rischio "Recurrence of [breach type]"
7. **📊 Gap Analysis** → run mirato sui controlli che hanno fallito
8. **📜 Policies** → aggiorna l'Incident Response Plan con learnings

### 4.5. Onboarding di un nuovo dipendente in HR

1. **📜 Policies** → assegna 5 policy "starter" all'user `nuovodipendente@company`
2. Lui apre GRACE (con il suo demo user impostato), tab **✅ My Acknowledgments**, legge e accetta ciascuna
3. Tu vedi nel back office (Library tab) le policy assigned con stato = `acknowledged` + timestamp + signature note

---

## 5. Funzionalità trasversali (advanced)

### 5.1. Cross-framework mapping (lazy)

**Dove**: pulsante "🔗 Show cross-framework impact" sotto ogni finding nel Registry.
**Cosa fa**: la **prima volta** chiama Claude per calcolare i controlli equivalenti negli altri 9 framework attivi. Cache permanente in DB.
**Costo demo**: ~$2-5 di Claude API per pre-warmare l'intero catalogo (530+ controlli × 9 framework target). Comando manuale:
```bash
docker compose exec grace-backend python tools/precompute_mappings.py
```

### 5.2. Multi-lingua (EN / IT)

- Toggle EN/IT in alto a destra
- L'interfaccia cambia istantaneamente
- I **finding generati** da Claude sono nella lingua impostata al momento dell'assessment
- I finding già generati vengono **tradotti lazy** al primo click (cache permanente)

### 5.3. File supportati

| Estensione | Parser | Note |
|------------|--------|------|
| PDF | PyMuPDF | OCR non incluso (solo PDF testuali) |
| DOCX, DOC | docx2txt | Mantiene il testo, non gli stili |
| TXT | nativo | UTF-8 |
| XLSX | openpyxl | Tutti i fogli, formato tab-separated |
| CSV | stdlib | BOM-aware, UTF-8 |

### 5.4. Synthetic dataset per demo

Se ti serve popolare GRACE con dati finti per una demo:
```bash
docker compose exec grace-backend python tools/synth_assessments.py \
  --upload --framework iso27001_2022 --count 5
```
Genera 5 documenti sintetici **filigranati come "fictional"**, li carica, runna gap analysis. Pronto per screenshot.

---

## 6. Best practice & anti-pattern

### Best practice

- **Ridurre la rumorosità del registry**: usa Ask GRACE per le domande esplorative, Gap Analysis solo quando vuoi finding registrati
- **Cross-framework prima del fix**: prima di pianificare la remediation, espandi sempre il pannello cross-framework — potresti chiudere 5 gap con 1 azione invece di 1
- **Granularità degli assessment**: 1 documento = 1 Gap Analysis. Non concatenare 10 file in una sola run — il segnale si perde
- **Pre-warm dei mapping**: prima di una demo o di un audit, lancia `precompute_mappings.py` per evitare attese durante la presentazione

### Anti-pattern (cose da NON fare)

- ❌ Usare GRACE come unico repository di evidenze (non è un DMS — usa SharePoint / GDrive per i file, e linka l'URL)
- ❌ Fare un'unica Gap Analysis "monstre" su 50 documenti — i finding si confondono, la dashboard diventa illegibile
- ❌ Non controllare l'output di Document Generation prima di pubblicarlo — è una bozza, non un testo legale finale
- ❌ Lasciare incident in stato `open` per mesi — usa `accepted_risk` o `dismissed` se non li gestisci più

---

## 7. Limitazioni note del prototype

| Funzionalità | Stato | Roadmap |
|--------------|-------|---------|
| Single demo user (no SSO) | Voluto | Entra ID / SAML in Fase 2 |
| Evidence storage cloud (S3/Azure Blob) | Solo SQLite locale | Fase 2 |
| Continuous monitoring (control testing automatico) | Manuale | Fase 2 (APScheduler) |
| Approval workflow multi-step su policy | Single-step (accept/reject) | Fase 3 |
| API key per integrazioni esterne (XSOAR, Slack) | Endpoint solo da UI | Fase 2 |
| RBAC granulare | Assente | Fase 2 |

Il **core engine** (gap analysis, document generation, cross-framework mapping, risk register, vendor risk, policy lifecycle, incident management) è **production-grade per logica**, prototype-grade per infrastruttura. La migrazione a PostgreSQL + Azure AI Foundry è documentata in CLAUDE.md ed è una sostituzione di connection string + minor adapter changes, non una riscrittura.

---

## 8. Quick reference — shortcut mentali

| Hai bisogno di... | Vai su... |
|-------------------|-----------|
| Capire un controllo | 📚 Framework Library → Explain with Claude |
| Domanda libera, no record | 🤖 Ask GRACE |
| Audit con traccia | 📊 Gap Analysis |
| Triage giornaliero | 🔍 Finding Registry |
| Vista del manager | 🛡 Governance Dashboard |
| Scrivere una policy | 📝 Document Generation |
| Registro rischi | 🎲 Risk Management |
| Nuovo fornitore | 🤝 Vendor Risk |
| Pubblicare policy | 📜 Policies |
| Incident in corso | 🚨 Incidents |

---

## 9. Hai un problema? Hai un'idea?

GRACE è un prototype attivo. Se trovi bug, edge case, miglioramenti UX, riportali sul tracker GitHub. La filosofia di sviluppo è: **piccoli commit, fix veloci, niente debt accumulato**.

Buon lavoro.

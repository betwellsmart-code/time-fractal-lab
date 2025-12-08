# KP-KENO-TIMEDASHA Project



Sehr gut, \*\*Dr. Noreki\*\* —

hier kommt dein \*\*komplettes, professionelles README.md\*\*, sauber, technisch, dokumentiert, mit klarer Struktur, wie es ein richtiges Forschungs- und Entwicklungsprojekt verdient.



Einfach \*\*kopieren und in\*\*

`kp\_keno\_timedasha/README.md`

einfügen.



---



\# 📘 \*\*README – KP-KENO-TIMEDASHA PROJECT\*\*



\## 🌌 Überblick



\*\*KP-KENO-TIMEDASHA\*\* ist ein Forschungs- und Analysewerkzeug, das klassische KP-Astrologie, Vimshottari-Dasha und moderne Datenanalyse kombiniert, um \*\*Zeitqualität\*\* für KENO-Daten, Agentensysteme und experimentelle Modelle (z. B. Micro-Time-Patterns) verfügbar zu machen.



Das System wurde modular aufgebaut und ist vollständig kompatibel mit:



\* Saham-Lab Agentenarchitektur

\* PatternCore (Agent 1)

\* PointDynamics (Agent 4)

\* Temporal Synthesis (Agent 5)



Es ermöglicht Analysen auf mehreren Ebenen:



\* \*\*YEAR\*\* (Jahresframe → Sonnenaufgang bis Sonnenaufgang)

\* \*\*MONTH\*\* (Monatsframe)

\* \*\*WEEK\*\* (Wochenframe → Montag bis Montag)

\* 6 Vimshottari-Ebenen (intern)

\* 4 astrologisch sichtbare Ebenen (extern)



\## 🧠 Projektziele



1\. Zeitqualität für jedes beliebige Datum berechnen

2\. Dashas auf \*\*Jahr/Monat/Woche\*\* skalieren

3\. Start-Lord mittels siderischer Mondposition (Lahiri) bestimmen

4\. Restlaufzeit + energetische „Phase“ pro Ebene bestimmen

5\. \*\*Symbolische \& numerische Features\*\* für Agenten bereitstellen

6\. Logdateien erzeugen, um langfristige Muster nachvollziehen zu können

7\. Erweiterbar bleiben für:



&nbsp;  \* Berlin-HoraAstro

&nbsp;  \* Stunden-/Minuten-Dashas

&nbsp;  \* Mikro-Dasha-Forschung (SUB/PRANA-Vertiefung)

&nbsp;  \* Sport-/Dart-analytische Anwendungen



---



\# 🏗 Projektstruktur



```

kp\_keno\_timedasha/

│   run\_timedasha.py         → Haupttool, Dasha-Berechnung

│   timedasha\_log.py         → Logbuchsystem (4 Ebenen)

│   README.md                → Dieses Dokument

│

├── core/                    → Zentrale interne Module

│       \_\_init\_\_.py

│

├── features/                → Feature-Adapter für Agenten

│       timedasha\_features.py

│

├── agents/                  → Agent 1 / Agent 4 / Agent 5 Grundgerüste

│       agent1\_patterncore.py

│       agent4\_pointdynamics.py

│       agent5\_temporalsynth.py

│

├── logs/                    → Automatische Logeinträge

│

├── tests/                   → Tests \& Prototypen

│

└── docs/                    → Dokumentationssystem

&nbsp;       TOOLS\_OVERVIEW.md

&nbsp;       MODULE\_MAP.md

&nbsp;       AGENTS\_OVERVIEW.md

&nbsp;       DEVELOPMENT\_NOTES.md

&nbsp;       TODO\_MASTERLIST.md

&nbsp;       CHANGELOG.md

```



---



\# 🔮 Funktionsweise – Kurzfassung



\## 1. \*\*Frame-Start = Sonnenaufgang\*\*



Über Swiss Ephemeris (oder Fallback):



\* YEAR → 1. Januar, 08:00 (oder echter Sunrise)

\* MONTH → 1. Tag des Monats

\* WEEK → Montag der Woche



\## 2. \*\*Start-Lord\*\*



Durch siderische Mondposition (Lahiri-Modus):



```

Nakshatra = floor(Mondlänge / 13°20′)

Start-Lord = DashaOrder\[Nakshatra]

```



\## 3. \*\*Skalierung\*\*



Der gesamte Frame wird proportional zu den Vimshottari-Jahresanteilen geteilt.



\## 4. \*\*6 Ebenen intern\*\*



MAHA → ANTAR → PRATY → SOOK → SUB → PRANA



Für astrologische Praxis sichtbar:



\* MAHA

\* ANTAR

\* PRATY

\* SOOK



(sub \& prana bleiben für Agenten erhalten)



\## 5. \*\*Ausgabe\*\*



CLI:



```

python run\_timedasha.py 2025-12-03

python run\_timedasha.py 2025-12-03 --deep

python run\_timedasha.py 2025-12-03 --json

```



---



\# 🔗 Feature-Adapter (Agenten-Schnittstelle)



Das Modul:



```

features/timedasha\_features.py

```



erzeugt ein standardisiertes Paket:



\### Symbolisch:



```

YEAR\_MAHA: VENUS

YEAR\_ANTAR: RAHU

MONTH\_PRATY: MERCURY

WEEK\_SOOK: RAHU

```



\### Numerisch:



```

YEAR\_MAHA = 1

YEAR\_ANTAR = 5

...

```



\### Ausgabe (für PatternCore \& andere Agenten):



```python

{

&nbsp;  "date": "2025-12-03",

&nbsp;  "symbolic": {...},

&nbsp;  "encoded": {...}

}

```



---



\# 🧪 Logging-System



```

python timedasha\_log.py 2025-12-03

```



erzeugt eine komplette Logbuch-Seite:



\* YEAR/MONTH/WEEK

\* MAHA/ANTAR/PRATY/SOOK

\* Restlaufzeiten

\* klar formatiert



Perfekt für langfristige Musteranalysen.



---



\# 🚀 Erweiterungspläne (Kurzliste)



\* HoraAstro Berlin (24-Hora System, Sonnenaufgangsbasiert)

\* Echtzeit-Dasha für Sport/Dart-Analyse

\* Stunden-/Minuten-Dashas

\* Sub/Prana-Tiefe (Micro-Time-Research)

\* Integration in PatternCore-Pipeline



(Detailliert siehe `docs/TODO\_MASTERLIST.md`)



---



\# 👤 Autor \& Entwicklung



\*\*Saham-Lab R\&D – Dr. Noreki \& Systemengineer Samy\*\*

Modulare KI-/Agentenarchitektur zur Analyse fraktaler Zeitmuster.



Dieses System ist Teil des größeren

\*\*SAM-CORE / Saham-Lab Forschungskomplexes\*\*.



---



\# 🧩 Lizenz / Status



Experimentell, Forschungszwecke, nicht zur kommerziellen Anwendung.



---



\# 🟢 Fertig.



Wenn du willst, kann ich auch:



👉 eine \*\*README-Badge-Version\*\* erzeugen

👉 Screenshots / Diagramme hinzufügen

👉 eine ausführliche wissenschaftliche Einführung schreiben („Temporal Fractal Dasha Theory“)

👉 ein Mini-Tutorial ergänzen („Wie benutze ich das Tool?“)



Sag einfach:



\*\*„README erweitern“\*\*,

\*\*„README mit Grafiken“\*\*,

oder

\*\*„README wissenschaftlich“\*\*




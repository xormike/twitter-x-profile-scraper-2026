# OSM Kleinort-Extraktor

Vollautomatische Pipeline zur Extraktion von Ortsnamen aus [OpenStreetMap](https://www.openstreetmap.org)-Daten — komplett offline, ohne API-Schlüssel.

Das Programm lädt Kartendaten herunter, schneidet einen beliebigen Ausschnitt aus, analysiert ihn und exportiert alle gefundenen Orte (Weiler, Dörfer, Stadtteile usw.) in eine übersichtliche Excel-Tabelle.

---

## Inhaltsverzeichnis

- [Voraussetzungen](#voraussetzungen)
- [Einmalige Einrichtung](#einmalige-einrichtung)
- [Verwendung](#verwendung)
- [Bounding Box ermitteln](#bounding-box-ermitteln)
- [Ausgabe](#ausgabe-xlsx)
- [Unterstützte Regionen](#unterstützte-regionen)
- [Download-Verhalten](#download-verhalten)
- [Dateistruktur](#dateistruktur)
- [RAM-Empfehlung](#ram-empfehlung)
- [Häufige Probleme](#häufige-probleme)

---

## Voraussetzungen

Folgende Programme müssen einmalig installiert werden, bevor das Tool gestartet werden kann:

### 1. Python

Python ist die Programmiersprache, in der das Tool geschrieben ist.

1. Installer herunterladen: [https://www.python.org/downloads/](https://www.python.org/downloads/) → **„Download Python 3.x.x"**
2. Installer ausführen
3. Wichtig: Den Haken bei **„Add Python to PATH"** setzen, bevor auf „Install Now" geklickt wird
4. Installation abschließen

> Python 3.9 oder neuer wird empfohlen. Die aktuellste Version von der Website ist immer eine gute Wahl.

---

### 2. Miniconda (Python-Umgebung)

Miniconda ist eine schlanke Python-Distribution, die alle nötigen Werkzeuge mitbringt und Pakete sauber voneinander trennt.

**Wichtig:** Miniconda unbedingt **nur für den aktuellen Benutzer** installieren — nicht systemweit. Das vermeidet Berechtigungsprobleme beim späteren Installieren von Paketen.

1. Installer herunterladen: [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html) → **Windows → Miniconda3 Windows 64-bit**
2. Installer ausführen
3. Beim Schritt „Installation Type" unbedingt **„Just Me (recommended)"** wählen — **nicht** „All Users"
4. Installationspfad so lassen wie vorgeschlagen (z. B. `C:\Users\DeinName\miniconda3`)
5. Haken bei „Add Miniconda3 to PATH" kann gesetzt bleiben

> **Warum nicht systemweit?** Eine systemweite Installation landet unter `C:\ProgramData\` und erfordert Admin-Rechte für jede Paketinstallation. Bei einer Benutzer-Installation unter `C:\Users\...` funktioniert alles ohne Administrator.

---

### 3. osmium-tool (Werkzeug zum Verarbeiten von Kartendateien)

`osmium-tool` ist ein Kommandozeilenprogramm zum Ausschneiden und Konvertieren von OpenStreetMap-Dateien. Es wird über Miniconda installiert.

**Anaconda Prompt öffnen** (Windows-Suche → „Anaconda Prompt") und folgenden Befehl ausführen:

```
conda install -c conda-forge osmium-tool
```

Die Installation kann einige Minuten dauern. Einmalig ausführen — danach nie wieder nötig.

---

### 4. Python-Pakete

Das Programm benötigt folgende Python-Bibliotheken:

| Paket | Zweck |
|-------|-------|
| `osmnx` | Auslesen und Analysieren von OSM-Daten |
| `pandas` | Datenverarbeitung und Tabellenoperationen |
| `openpyxl` | Excel-Dateien (.xlsx) erstellen |
| `tqdm` | Fortschrittsbalken beim Download |

**Fehlende Pakete werden beim ersten Programmstart automatisch installiert.** Falls die automatische Installation fehlschlägt, können sie manuell in der Anaconda Prompt nachinstalliert werden:

```
conda install -c conda-forge osmnx --solver=classic
pip install pandas openpyxl tqdm
```

> **Hinweis zu `--solver=classic`:** Der Flag stellt sicher dass Conda kompatible Paketversionen findet, auch wenn ein alternativer Solver (libmamba) installiert oder fehlerhaft konfiguriert ist.

> **Hinweis zu `pathlib`:** Die Python-Standardbibliothek `pathlib` (wird intern für sichere Pfadverarbeitung verwendet, auch bei Pfaden mit Leerzeichen) ist bereits in Python 3.4+ enthalten und muss **nicht** extra installiert werden.

---

## Einmalige Einrichtung — Zusammenfassung

```
Schritt 1:  Miniconda installieren  →  "Just Me" auswählen
Schritt 2:  Anaconda Prompt öffnen
Schritt 3:  conda install -c conda-forge osmium-tool
Schritt 4:  Fertig — ab jetzt nur noch start.bat doppelklicken
```

---

## Verwendung

1. Projektordner irgendwo auf dem PC ablegen (z. B. `Dokumente\osm-extraktor\`)
2. **`start.bat` doppelklicken** — ein Terminalfenster öffnet sich
3. Das Programm führt Schritt für Schritt durch den gesamten Ablauf:

```
────────────────────────────────────────────────────────────
  1/5 · Region auswählen
────────────────────────────────────────────────────────────
Nummer aus der Liste wählen (z. B. 1 für Bayern)

────────────────────────────────────────────────────────────
  2/5 · PBF-Datei
────────────────────────────────────────────────────────────
Vorhandene PBF-Dateien auf dem System werden automatisch
gefunden und zur Auswahl angeboten — oder automatischer
Download mit Fortschrittsbalken.

────────────────────────────────────────────────────────────
  3/5 · Bounding Box
────────────────────────────────────────────────────────────
Browser öffnet sich automatisch → Region einzeichnen →
4 Koordinaten kopieren → ins Terminal einfügen.
Ein Popup-Fenster erinnert an das richtige Kopierformat.

────────────────────────────────────────────────────────────
  4/5 · Ausschneiden & Konvertieren
────────────────────────────────────────────────────────────
Läuft automatisch (kann je nach Größe einige Minuten dauern)

────────────────────────────────────────────────────────────
  5/5 · Analyse & Export
────────────────────────────────────────────────────────────
XLSX-Tabelle wird erstellt und automatisch geöffnet
```

---

## Bounding Box ermitteln

Eine Bounding Box ist ein rechteckiger Kartenausschnitt, der durch zwei Koordinatenpaare (Südwest- und Nordost-Ecke) definiert wird. Das Programm öffnet die Webseite automatisch.

**Schritt-für-Schritt:**

1. Der Browser öffnet automatisch [boundingbox.klokantech.com](https://boundingbox.klokantech.com)
2. Gewünschte Region auf der Karte einzeichnen (Rechteck aufziehen)
3. **Unten links das Format auf `CSV` umstellen** — nicht `MARC` oder andere Formate!
4. Die 4 angezeigten Zahlen kopieren (sehen so aus: `11.360232,48.061602,11.722837,48.248220`)
5. Ins Terminal einfügen und Enter drücken

> Ein Windows-Popup erscheint automatisch 3 Sekunden nach dem Browser-Start als Erinnerung ans richtige Format.

> Das Format ist immer: `min_längengrad, min_breitengrad, max_längengrad, max_breitengrad`
> Beispiel München: `11.360232,48.061602,11.722837,48.248220`

---

## Ausgabe (XLSX)

Die erzeugte Excel-Datei liegt im Unterordner `daten/` und enthält 3 Tabellenblätter:

| Blatt | Inhalt |
|-------|--------|
| **Orte nach Typ** | Gruppiert nach Ortstyp, mit farbigen Abschnittsköpfen |
| **Alphabetisch** | Alle Orte von A–Z sortiert |
| **Statistik** | Anzahl pro Ortstyp |

**Spalten in den Ortslisten:**

| Spalte | Beschreibung |
|--------|-------------|
| Nr. | Laufende Nummer |
| Name | Ortsname laut OSM |
| Ortstyp (DE) | Deutscher Begriff (z. B. „Weiler", „Dorf") |
| Ortstyp (OSM) | Originalbegriff aus OSM (z. B. „hamlet", „village") |
| Gemeinde | Zugehörige Gemeinde (sofern in OSM eingetragen) |

**Erfasste Ortstypen:**

| OSM-Tag | Deutsch |
|---------|---------|
| `hamlet` | Weiler |
| `village` | Dorf |
| `town` | Kleinstadt |
| `suburb` | Stadtteil |
| `quarter` | Stadtviertel |
| `neighbourhood` | Nachbarschaft |
| `borough` | Stadtbezirk |
| `isolated_dwelling` | Einzelgehöft |
| `locality` | Flurname |

---

## Unterstützte Regionen

Das Programm enthält vordefinierte Download-Links für folgende Regionen:

**Deutschland:** Bayern, Baden-Württemberg, Berlin, Brandenburg, Bremen, Hamburg, Hessen, Mecklenburg-Vorpommern, Niedersachsen, Nordrhein-Westfalen, Rheinland-Pfalz, Saarland, Sachsen, Sachsen-Anhalt, Schleswig-Holstein, Thüringen

**Österreich:** Gesamtösterreich

**Schweiz:** Gesamtschweiz

**Weitere Europa:** Italien, Frankreich, Spanien, Polen, Tschechien

Für jede andere Region der Welt kann unter „Eigene URL eingeben" ein direkter Link von [download.geofabrik.de](https://download.geofabrik.de) eingegeben werden.

---

## Download-Verhalten

Das Programm erkennt automatisch bereits vorhandene PBF-Dateien — durchsucht werden:

- der `daten/`-Unterordner im Programmverzeichnis
- das Programmverzeichnis selbst
- der Download-Ordner des Benutzers
- Laufwerk D:\ (falls vorhanden)

Gefundene Dateien werden als nummerierte Liste angeboten und können direkt wiederverwendet werden, ohne erneut herunterzuladen.

**Bei einem fehlgeschlagenen oder unvollständigen Download** erscheinen drei Optionen:

1. Automatisch erneut versuchen
2. Datei manuell herunterladen — der Browser öffnet sich direkt mit dem Geofabrik-Link. Nach dem Download einfach Enter drücken; das Programm sucht dann automatisch nach der neuen Datei und zeigt sie zur Auswahl an — kein manuelles Eintippen eines Pfades nötig.
3. Abbrechen

Das Programm prüft außerdem die Dateigröße nach dem Download (Abgleich mit der erwarteten Größe vom Server) und erkennt so unvollständige Downloads zuverlässig, auch bei instabiler Internetverbindung.

---

## Dateistruktur

```
osm-extraktor/
├── start.bat          ← Hier starten (Doppelklick)
├── main.py            ← Hauptprogramm
├── README.md          ← Diese Datei
└── daten/             ← Wird automatisch erstellt
    ├── bavaria-latest.osm.pbf    ← Heruntergeladene Rohdaten
    ├── mein_ausschnitt.osm.pbf   ← Ausgeschnittener Bereich
    ├── mein_ausschnitt.osm       ← Konvertierte OSM-Datei
    └── kleinorte_Bayern_mein_ausschnitt.xlsx  ← Ergebnis
```

> Die `.osm.pbf`- und `.osm`-Dateien können nach Abschluss gelöscht werden — nur die `.xlsx` ist das eigentliche Ergebnis. Die großen PBF-Dateien (Bayern z. B. ~1 GB) können für spätere Abfragen wiederverwendet werden — das Programm erkennt sie beim nächsten Start automatisch.

---

## RAM-Empfehlung

Der Schritt „Konvertieren" (PBF → OSM) ist speicherintensiv, da die gesamte Datei dekomprimiert wird:

| Ausschnittgröße | PBF-Dateigröße | RAM-Bedarf |
|-----------------|---------------|------------|
| Kleines Gebiet (~10 km Radius) | < 10 MB | 2–4 GB |
| Landkreis | ~20–80 MB | 4–8 GB |
| Bundesland (z. B. Bayern) | ~800 MB | 8–16 GB |

Für große Bundesländer empfiehlt es sich, nur den benötigten Ausschnitt zu verwenden und nicht das gesamte Bundesland zu konvertieren.

---

## Häufige Probleme

**„osmium nicht gefunden"**
→ Anaconda Prompt öffnen und `conda install -c conda-forge osmium-tool` ausführen. Darauf achten dass die Anaconda Prompt und nicht die normale CMD verwendet wird.

**„EnvironmentNotWritableError"**
→ Miniconda wurde systemweit unter `C:\ProgramData\` installiert. Entweder die Anaconda Prompt als Administrator öffnen, oder Miniconda neu installieren mit der Option „Just Me".

**osmnx lässt sich nicht installieren / ImportError bei shapely**
→ In der Anaconda Prompt ausführen: `conda install -c conda-forge osmnx --solver=classic`. Der Flag `--solver=classic` vermeidet Versionskonflikte zwischen osmnx und shapely, die auf manchen Systemen auftreten.

**Keine Orte gefunden**
→ Die Bounding Box prüfen. Häufiger Fehler: Das Format war nicht auf `CSV` gestellt, sondern auf `MARC` oder `DublinCore` — dann haben die Koordinaten ein anderes Format.

**Download bricht ab / Datei zu klein**
→ Das Programm erkennt unvollständige Downloads automatisch anhand der Dateigröße und bietet an, erneut zu versuchen oder die Datei manuell herunterzuladen. Bei instabiler Verbindung einfach die manuelle Option wählen und die Datei über den Browser laden — danach Enter drücken, das Programm findet die Datei automatisch.

**Fehlende Gemeinde-Spalte**
→ Die Gemeindezugehörigkeit wird direkt aus OSM gelesen. Nicht alle Orte haben dieses Feld in OSM eingetragen — leere Zellen sind normal.

---

## Technischer Hintergrund

Das Programm kombiniert drei Werkzeuge:

- **osmium-tool** — hochperformantes C++-Programm zum Verarbeiten von OSM-Binärdateien (`.pbf`)
- **osmnx** — Python-Bibliothek zum Lesen und Analysieren von OSM-XML-Daten
- **pathlib** — Python-Standardbibliothek für betriebssystemunabhängige Pfadverarbeitung (behandelt Leerzeichen in Pfaden automatisch korrekt)

Die Datenquelle ist [Geofabrik](https://www.geofabrik.de), die täglich aktuelle OSM-Exporte für alle Regionen der Welt bereitstellt — kostenlos und ohne Registrierung.

---

## Lizenz

Dieses Tool ist für den persönlichen und nicht-kommerziellen Gebrauch gedacht.
Die verwendeten Kartendaten stammen von OpenStreetMap und stehen unter der [ODbL-Lizenz](https://www.openstreetmap.org/copyright).

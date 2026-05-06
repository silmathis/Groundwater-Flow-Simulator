# 🌳 Git Workflow Guide

Dieses Dokument erklärt, wie man mit Branches arbeitet und diese wieder merged.

## Branch erstellen und wechseln

```bash
# Neue Branch erstellen und direkt wechseln
git checkout -b feature/mein-feature-name

# Oder mit neuerer Syntax:
git switch -c feature/mein-feature-name
```

**Tipp:** Verwende aussagekräftige Namen wie:
- `feature/neue-funktion`
- `fix/bug-behebung`
- `docs/dokumentation-update`

## Änderungen committen

```bash
# Alle Änderungen zum Staging hinzufügen
git add .

# Oder nur spezifische Dateien
git add path/to/file.py

# Mit aussagekräftiger Nachricht committen
git commit -m "Feature XY implementiert"
```

## Branch zum Remote pushen

```bash
# Erste Push: -u setzt Tracking
git push -u origin feature/mein-feature-name

# Weitere Pushes
git push
```

## Branch auf den aktuellen Stand von main bringen

Wenn dein aktueller Branch die neuesten Änderungen aus `main` bekommen soll, ist das der übliche Ablauf:

### Variante 1: Rebase auf main
```bash
# Erst die neuesten Remote-Infos holen
git fetch origin

# Aktuellen Branch auf main neu aufbauen
git rebase origin/main
```

### Variante 2: Merge mit main
```bash
# Erst die neuesten Remote-Infos holen
git fetch origin

# main in den aktuellen Branch mergen
git merge origin/main
```

**Tipp:**
- `rebase` hält die Historie sauberer, kann aber bei bereits gepushten Branches ein Force-Push nötig machen.
- `merge` ist einfacher, erzeugt dafür meist einen zusätzlichen Merge-Commit.

## Branch mergen

### 1. Zurück zur Hauptbranch
```bash
git checkout main
# oder: git switch main
```

### 2. Aktuelle Änderungen holen (optional aber empfohlen)
```bash
git pull origin main
```

### 3. Branch mergen
```bash
git merge feature/mein-feature-name
```

### 4. Zum Remote pushen
```bash
git push origin main
```

## Branch löschen

### Lokal löschen
```bash
# Erst zur anderen Branch wechseln (z.B. main)
git checkout main

# Dann die Branch löschen (nur wenn gemerged)
git branch -d feature/mein-feature-name

# Oder erzwingen (auch wenn nicht gemerged)
git branch -D feature/mein-feature-name
```

### Auch auf Remote löschen
```bash
# Wenn bereits gepusht wurde:
git push origin --delete feature/mein-feature-name
```

**Tipp:** Eine frisch erstellte Branch, die noch nicht gepusht wurde, kann einfach lokal gelöscht werden!

## Überblick behalten

```bash
# Alle lokalen Branches sehen
git branch

# Alle Branches (lokal + remote)
git branch -a

# Aktuellen Status checken
git status
```

## Bei Merge-Konflikten

Wenn Git automatisches Mergen nicht kann:

1. **Konflikt-Dateien öffnen** und Konflikte manuell auflösen
2. **Aufgelöste Dateien staged:** `git add .`
3. **Merge abschließen:** `git commit -m "Merge feature/... mit main"`
4. **Pushen:** `git push origin main`

---

**Fragen?** Schau in die Git-Dokumentation oder frag im Team nach! 

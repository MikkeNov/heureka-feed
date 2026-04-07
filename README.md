# Heureka Feed Generator

Automaticky generuje Heureka XML feed z Google Merchant Center feedu pro [drevnikovesteny.cz](https://www.drevnikovesteny.cz).

## Jak to funguje

- GitHub Actions workflow se spouští každé 4 hodiny (a při push na main)
- Skript `convert.py` stáhne GMC feed a převede ho na Heureka XML formát
- Výsledný feed se uloží do `docs/heureka_feed.xml` a servíruje přes GitHub Pages

## Aktivace GitHub Pages

1. Jdi do **Settings → Pages**
2. **Source**: Deploy from a branch
3. **Branch**: `main`, folder: `/docs`
4. Ulož

## URL feedu

```
https://{username}.github.io/heureka-feed/heureka_feed.xml
```

## Ruční spuštění

```bash
gh workflow run update-feed.yml
```

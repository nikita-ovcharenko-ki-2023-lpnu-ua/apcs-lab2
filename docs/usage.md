# Інструкція з використання

## Встановлення інструментів (Linux Mint 22 / Ubuntu 24.04)
```bash
sudo add-apt-repository -y ppa:kicad/kicad-10.0-releases
sudo apt update && sudo apt install -y --no-install-recommends kicad
# Freerouting CLI (нативна збірка, Java не потрібна)
mkdir -p ~/.local/opt/freerouting && cd ~/.local/opt/freerouting
curl -LO https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-cli-2.5.0-linux-x64.tar.gz
tar xzf freerouting-cli-2.5.0-linux-x64.tar.gz && ./freerouting-cli --help
```

## Запуск агента
### VS Code + GitHub Copilot
1. `git switch -c feature/<назва> develop`, `code .`
2. Copilot Chat → агент **pcb-engineer** → `/build-board fullName="Прізвище Ім'я По батькові"`.

### Claude Code
```bash
claude
> /build-board fullName="Прізвище Ім'я По батькові"
```

### Окремі команди
| Команда | Що робить |
|---|---|
| `/gen-params fullName="…"` | GUID і параметри |
| `/create-library` | символи й футпринти |
| `/create-schematic` | схема + ERC |
| `/create-pcb` | плата і розміщення |
| `/route` | трасування |
| `/fab` | DRC, Gerber, зображення |
| `/check` | перевірка без змін |

## Локальна перевірка
```bash
python3 .github/agent-tools/check.py                 # усі групи, exit code 0 = PASS
python3 .github/agent-tools/check.py --only pcb,routing
```
У гілці `develop` (до `/build-board`) групи `params` … `fab` очікувано `FAIL`.

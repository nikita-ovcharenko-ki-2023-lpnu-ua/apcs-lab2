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

<!-- agent:build:start -->
## Відтворення плати без агента
```bash
python3 tools/params.py "Прізвище Ім'я По батькові"   # params/board.json
python3 tools/library.py                               # hardware/lib/
python3 tools/schematic.py                             # hardware/lab2.kicad_sch
python3 tools/pcb.py                                   # hardware/lab2.kicad_pcb (розміщення)
python3 tools/route.py                                 # трасування (Freerouting)
python3 tools/fab.py                                   # ERC/DRC, output/gerbers, output/images
./ci.sh                                                # те саме, що виконує GitHub Actions
```
Відкрити в KiCad: `kicad hardware/lab2.kicad_pro`. Для переробки розміщення —
видалити доріжки на платі (`/create-pcb` і `/route` не чіпають розведену плату).
<!-- agent:build:end -->

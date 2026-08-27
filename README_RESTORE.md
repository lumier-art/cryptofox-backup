# CRYPTOFOX — Backup & Restore

## Як зберегти на GitHub

1. Відкрий https://github.com/gigavers3?tab=repositories
2. Створи новий репозиторій (наприклад, `cryptofox-backup`)
3. Завантаж туди файли з папки `~/.openclaw/workspace/`

## Файли для бекапу

| Файл | Призначення |
|------|-------------|
| MEMORY.md | Контекст і прогрес |
| SOUL.md | Особистість (Druckenmiller) |
| AGENTS.md | Інструкції |
| config.json | ACP конфігурація |
| cryptofox-backup.tar.gz | Архів всіх файлів |

## Як відновити

```bash
# 1. Склонувати репозиторій
git clone https://github.com/gigavers3/cryptofox-backup.git
cd cryptofox-backup

# 2. Скопіювати файли в робочу директорію
cp * /home/node/.openclaw/workspace/

# 3. Налаштувати ACP
acp configure
acp agent use 01a02f4c-3e1b-792b-b0d0-2c3317370414
```

Важливо: ACP токен треба буде оновити через `acp configure` — ти клікаєш посилання.
Підписант уже затверджений на dashboard, новий додавати не треба.
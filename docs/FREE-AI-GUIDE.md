# Как создать игру на Unity, используя только бесплатные нейросети

Полный стек 2026 года под ваш проект «Мастера Снов: Возрождение».
Ничего платного. Для РФ указаны сервисы без VPN.

## Сводная таблица: чем что делать

| Задача | Лучший бесплатный | Запасной | Лимит |
|---|---|---|---|
| Код C# / Unity | **DeepSeek** (deepseek.com) | GigaChat, Qwen | практически без лимита, без VPN |
| Промпт-инжиниринг | **Claude free / ChatGPT free** | Gemini free | 30–50 сообщений в день |
| 2D-арт (спрайты, фоны) | **Kandinsky 5.0** (fusionbrain.ai) | Шедеврум, Leonardo (150 токенов/день) | без лимита, понимает русский |
| 3D-модели | **Luma Genie** (lumalabs.ai) | Meshy (100 кред./мес, CC BY) | щедрый free для прототипа |
| Ретопология/правка 3D | **Blender** (бесплатно, не ИИ) | Hunyuan3D (локально) | без лимита |
| Музыка | **Suno** (suno.com) | Udio (10/день), Riffusion | 50 кредитов/день = ~10 треков |
| Звуки (SFX) | **ChipTone/sfxr** (не ИИ, бесплатны) | ElevenLabs free | без лимита |
| Озвучка RU | **Silero** (гитхаб, бесплатно) | GigaChat TTS | без лимита |
| Анимация | **Mixamo** (adobe.com/mixamo) | UniRig (MIT) | бесплатно, автorig |
| Идеи/баланс | любая LLM free | — | — |

## Шаг 1. Установка (1 час)

1. **Unity Hub** → unity.com/download → Personal-лицензия (бесплатна при доходе < $200K)
2. **Unity 2022.3 LTS** + модули: Android Build Support, OpenJDK, SDK/NDK
3. **Visual Studio Community** (бесплатно) + workload «Разработка игр на Unity»
4. **DeepSeek** → chat.deepseek.com — регистрация бесплатна, VPN не нужен, лучший бесплатный кодер
5. **Kandinsky** → fusionbrain.ai — безлимитный ИИ-арт, промпты на русском
6. **Suno** → suno.com — 10 музыкальных треков в день бесплатно

## Шаг 2. Код — DeepSeek + ваш промпт

В проекте уже есть два готовых документа для LLM:
```
android-game-llm-prompt.md   ← системный промпт агента-разработчика
PROJECT-HANDOFF.md           ← контекст проекта для любой LLM
```

**Как работать:** вставьте оба документа в DeepSeek (или Claude/ChatGPT free), дальше пишите задачи обычным текстом. DeepSeek понимает Unity/C# на уровне платных моделей.

**Пример запроса:**
> Прочитай промпт и PROJECT-HANDOFF. Добавь систему гильдий: интерфейс, данные, сохранение.

Получите полный код с файлами → копируете в Unity → тестируете.

## Шаг 3. Арт — Kandinsky / Leonardo (2D)

**Приём из проекта (уже работает):** просите ИИ рисовать персонажа на **фиолетовом (#FF00FF) фоне**, потом скрипт `tools/build_demo_art.py` автоматически вырезает фон заливкой от краёв → прозрачный PNG → готовый спрайт для Unity.

```
Промпт для Kandinsky (на русском!):
"Милый мультипликационный игровой персонаж в стиле AFK Arena: каменный голем-страж,
тело из серо-зелёных валунов со светящимися зелёными рунами, маленькие глаза,
полный рост, вид сбоку, на чистом фиолетовом (#FF00FF) фоне, без тени, без земли"
```

**Обработка:** положите PNG в `prototype/art/raw/` → запустите:
```bash
python3 tools/build_demo_art.py  # вырежет фон + сожмёт
```
Готовые спрайты кладёте в Unity (`Assets/Sprites/`).

**Для фонов** (лес, пустыня, снег) — те же сервисы, горизонтальные полосы, тот же приём.

## Шаг 4. 3D-модели — Luma Genie / Meshy

1. **Luma Genie** (lumalabs.ai/genie) — text-to-3D бесплатно, экспорт GLB → импорт в Unity
2. **Meshy** (meshy.ai) — 100 кредитов/мес бесплатно (≈10 моделей), экспорт FBX с PBR-текстурами. Лицензия CC BY — указать «Models by Meshy.ai» в кредитах
3. Для персонажей: генерируете на Luma → ретопология в Blender → rig на Mixamo → анимации готовые (бег/атака/смерть) → FBX в Unity

## Шаг 5. Музыка — Suno

```
Промпт для Suno:
"epic fantasy orchestral, dreamy atmosphere, mobile RPG soundtrack,
loopable, 120 bpm, ethereal choirs, mystical"
```
10 треков в день — за неделю наберёте полный саундтрек (меню/бой/босс/победа/поражение).

## Шаг 6. Собираем всё в Unity

В проекте `unity-project/README-SETUP.md` — пошаговая сборка трёх сцен. Код и контент готовы (253 ассета). Дальше:

1. Копируете `Assets/` из репозитория в Unity-проект
2. Спрайты из `prototype/art/proc/` (уже прозрачные) → `Assets/Sprites/`
3. Музыку из Suno → `Assets/Audio/`
4. Сцены по README-SETUP (Boot → Home → Battle)
5. Build → APK → на телефон

## Бюджет: 0 ₽

| Инструмент | Цена |
|---|---|
| Unity Personal | 0 ₽ |
| Visual Studio Community | 0 ₽ |
| DeepSeek | 0 ₽ (без VPN) |
| Kandinsky / Шедеврум | 0 ₽ (без VPN, без лимита) |
| Luma Genie / Meshy free | 0 ₽ |
| Suno free | 0 ₽ |
| Blender / Mixamo | 0 ₽ |
| **Итого** | **0 ₽** |

## Ограничения free-стека (честно)

- **Meshy**: ~10 моделей/мес (для 5 героев и 10 врагов хватит на 1–2 месяца)
- **Suno**: 10 треков/день (качество чуть ниже платного, но для инди — достаточно)
- **DeepSeek**: иногда «думает» дольше ChatGPT, но код пишет сопоставимо
- **Kandinsky**: чуть слабее Midjourney в детализации, но понимает русский и безлимитен
- **Коммерческое использование**: Kandinsky — да; Suno free — нет (только некоммерческое, для релиза нужен план); Meshy free — CC BY (указать в кредитах)

## Быстрый старт (за один вечер)

```bash
# 1. Форк/клон репозитория
git clone https://github.com/samagon90/stunning-octo-pancake.git

# 2. Открыть PROJECT-HANDOFF.md → вставить в DeepSeek вместе с промптом

# 3. Сгенерировать 1 героя в Kandinsky → положить в prototype/art/raw/
python3 tools/build_demo_art.py

# 4. Открыть prototype/index.html → игра работает

# 5. Для Unity: прочитать unity-project/README-SETUP.md
```

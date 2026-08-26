# Dream Masters Revival — настройка проекта в Unity

Возрождение «Мастеров Снов» (Mechanist Games, 2015): онлайн ARPG + ККИ для Android.
Контент (герои, умения, враги, 15 уровней, синергии, каталог, конфиг) **уже сгенерирован**
в `Assets/Resources/DreamMasters` — в редакторе ничего создавать не нужно.
Дизайн: `game-design/GDD.md`. Досье по оригиналу: `research/mastera-snov-issledovanie.md`.
Сервер: `docs/FIREBASE-SETUP.md` (включается одной строкой в GameConfig).

---

## Шаг 1. Проект

1. Unity Hub → **New Project** → **3D (URP)** → Unity **2022.3 LTS**, имя `DreamMastersRevival`.
2. **File → Build Settings → Android → Switch Platform**.
3. Скопируйте **всю папку `Assets`** из этого репозитория в проект (вместе с `.meta`!).

## Шаг 2. Настройки Android

**Edit → Project Settings → Player:**
- **Other Settings:** Scripting Backend **IL2CPP**; Target Architectures **ARM64**; Minimum API Level **24**.
- **Resolution and Presentation:** Orientation **Portrait**.
- При запросе импортировать **TextMesh Pro** — соглашайтесь (Essentials).

## Шаг 3. Сцены (3 штуки, добавить в Build Settings по порядку)

### 0. `Boot`
Пустой объект `Bootstrap` → компоненты: **GameManager** + **PoolManager** + **BootFlow** + **AudioManager**.
В поле **Config** GameManager перетащите `Assets/Resources/DreamMasters/GameConfig`.
Звук (8 SFX + эмбиент-луп) уже в `Assets/Resources/Audio` — грузится автоматически.

### 1. `Home` (хаб: меню, кампания, коллекция, отряд, призыв, магазин, арена, чат)
1. **GameObject → UI → Canvas**: Canvas Scaler = Scale With Screen Size, **1920×1080** (ландшафт), Match 0.5. На Canvas — **SafeAreaFitter** и **UiClickBinder** (клик-звук на все кнопки).
2. Под Canvas панели (Anchor stretch, все выключены кроме Menu):
   - `Menu` — приветствие (Text), кнопки: Кампания / Коллекция / Отряд / Призыв / Магазин / **Арена** / **Чат** / Выход → компонент **MainMenuUI** связать всё.
   - `Campaign` — назад + заголовок/описание мира + полоса миров (LayoutGroup) + список уровней (LayoutGroup) → **CampaignMapUI** (`worldsStrip`, `levelsContainer`). Кнопки-префабы опциональны (fallback есть).
   - `Collection` — назад + контейнер (**Grid Layout Group**) → **CollectionUI**; внутри панели `HeroDetail` (заголовок, статы, статус, кнопки: Уровень/Звезда/Ранг/Пробуждение + 4 умения, Закрыть) → **HeroDetailUI**. Карточка-префаб опциональна (fallback есть).
   - `Team` — назад + 4 кнопки-слота + подсказка → **TeamEditorUI**.
   - `Summon` — назад + 2 кнопки тяги + текст результата → **SummonUI**.
   - `Shop` — назад + 2 кнопки обмена + статус → **ShopUI**.
   - `Arena` — назад + рейтинг + 2 таба (Арена/Колизей): у Арены 3 кнопки боёв с подписями противников; у Колизея — статус дня и 3 кнопки боёв → **ArenaUI**.
   - `Chat` — назад + лог (Text в Viewport со ScrollRect) + InputField + кнопка «Отправить» → **ChatUI**.
   - `Settings` — назад + InputField имени + 2 Slider (музыка/звук) + Toggle (персонализация рекламы) + кнопка «Политика» + метка версии → **SettingsUI**.
3. Сверху панель валют (Text ×5) → **CurrenciesBarUI**.
4. `LoadingOverlay` (Image во весь экран + Text) — выключена; ссылку в MainMenuUI.
5. **Туториал-оверлей**: панель поверх всего (Text страницы + счётчик + Image с fillAmount для прогресса удержания + кнопка «Далее») → **TutorialUI**. Показывается сам при первом входе; скип — зажать экран на 5 секунд (пасхалка оригинала).
6. **Слоты будущей рекламы** (включать не нужно — оживут после SDK, см. docs/ADS-SETUP.md): панели с компонентом `NativeAdSlotView` в Menu / Shop / BattleResult.

### 2. `Battle`
1. Plane (масштаб 3) + Directional Light. Камера: pos (0,12,−14), rot (55,0,0).
2. Пустой `BattleRoot` → компоненты: **BattleManager**, **WaveController**, **BattleSceneBootstrap**, **BattleFxBinder**.
3. 4 пустых объекта `Spawn1..4` (z≈−8, x=−3..3) → в `playerSpawnPoints` BattleManager.
4. UI Canvas (+SafeArea): джойстик (**VirtualJoystick**), нижняя панель (**BattleHUD**: 4 кнопки героев, 4 кнопки умений с Image-fill, Авто, ×2, метка волны), панель итога (**BattleResultUI**: заголовок, награды, «Продолжить», «Ещё раз»).

## Шаг 4. Запуск (Play Mode)

1. Откройте `Boot` → Play: загрузится Home → «Пробуждайся, Мастер!»
2. Кампания → 9 миров снов: мир 1 «Первый сон» — 15 уровней; уровень 1 — **сюжетный проигрыш** (канон),
   15-й — Повелитель Мрака; миры 2–9 открываются зачисткой предыдущего. На 15-м уровне миров 2–9 —
   **Мастер сна (босс), который после победы присоединяется к отряду** (Юнь, Нюйва, Зевс, Шаман,
   Трипитака, Электра, Тетра, Лян). Персонажи — процедурные модели (тело/голова/оружие/корона), не капсулы.
3. Уровень 2 — уже победимый; после победы награды падают в профиль, следующий уровень открывается.
4. Коллекция → тап по Эшу → прокачка: уровень за пыль (в магазине 5000 золота → 2500 пыли),
   звёзды за 80 осколков, ранги за 6 рун. Призыв: тяга за осколки/кристаллы — новые герои (14 всего).
5. Отряд: тап по слоту — смена героя, синергии (Эш+Чейни +20% АТК и др.) применяются в бою сразу.
6. Арена: авто-бои за рейтинг; Колизей — реальный бой против команды противника (до 3 поражений в день).
7. Чат: мир-эфир локально; после деплоя сервера — общий чат всех игроков.

## Шаг 5. Сборка APK

**File → Build Settings** → все 3 сцены → **Build And Run** (телефон с USB-отладкой).
Проверить: сворачивание в бою → пауза и автосейв; вырезы экрана не перекрывают UI.

## Шаг 6. Сервер (когда будете готовы)

`docs/FIREBASE-SETUP.md`: `firebase deploy` → скопировать URL в `GameConfig.apiBaseUrl`.
Игра сама перейдёт с локальной заглушки на гибридные сейвы + серверные награды.

---

## Архитектура (кратко)

| Папка | Что внутри |
|---|---|
| `Scripts/Core` | GameManager (жизненный цикл Android), PoolManager, SceneLoader, BootFlow, BattleLaunch |
| `Scripts/Data` | ScriptableObject-контент: герои, умения, враги, уровни, синергии, каталог |
| `Scripts/Progress` | профиль, валюты (+реген энергии), коллекция героев (уровни/звёзды/ранги/пробуждение) |
| `Scripts/Battle` | бой: менеджер, юниты, урон, волны, умения, FX-биндер, bootstrap сцены |
| `Scripts/Services` | ISave/INetwork/IAd + реализации: локально, REST/облако, заглушки |
| `Scripts/UI` | HUD, джойстик, SafeArea, меню, кампания, коллекция, отряд, призыв, магазин |
| `Resources/DreamMasters` | **готовый контент** (70 ассетов: 6 героев, 24 умения, 18 врагов, 15 уровней) |
| `functions/`, `docs/` | сервер Cloud Functions + инструкция |

## Что дальше (итерации GDD)
- Мир 1 — играбелен; миры 2–9 = копирование паттерна уровней + темы.
- Колизей/Арена (поля профиля готовы, функция `/arenaOpponents` готова).
- Замена капсул на модели (у EnemyData/HeroData есть `viewPrefab`/`portrait`).
- Нативная реклама после стабилизации: `IAdService` + слоты уже размечены в UI.

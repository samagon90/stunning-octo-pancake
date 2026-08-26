# Firebase: подключение сервера (итерация 3 из GDD)

Клиент уже готов к сети: в `Assets/Scripts/Services` лежат `RestApiClient`,
`HybridSaveService` (сейвы: локально + облако) и `RestNetworkService` (награды боёв,
арена). Никаких Firebase SDK в Unity не нужно — работаем через REST к Cloud Functions.
Игра офлайн-совместима: нет сети — играем и сохраняемся локально, сеть появилась — синк.

## Шаги

1. **Проект Firebase:** [console.firebase.google.com](https://console.firebase.google.com) → Create project → `dream-masters-revival`.
2. **Firestore:** Build → Firestore Database → Create (production mode, регион `europe-west`).
3. **Cloud Functions:** на компьютере:
   ```bash
   npm install -g firebase-tools
   firebase login
   cd unity-project
   firebase init   # выбрать Functions + Firestore, существующий проект, Node 20
   firebase deploy --only functions
   ```
4. **Получить URL** функций: Console → Functions → например
   `https://us-central1-dream-masters-revival.cloudfunctions.net/profile`.
5. **Включить в игре:** Unity → `Assets/Resources/DreamMasters/GameConfig.asset` →
   поле **Api Base Url** = база URL без имени функции (например
   `https://us-central1-dream-masters-revival.cloudfunctions.net`).
   Всё: `GameManager` сам переключит сейвы на гибридные, сеть — на REST.
6. **Проверка:** запусти бой с победой → в Firestore появится документ `profiles/<anonymousId>`.

## Что сервер делает сейчас
| Функция | Метод | Назначение |
|---|---|---|
| `/profile?accountId=` | GET/POST | Облачное сохранение профиля (JSON) |
| `/battleResult` | POST | Валидация итога боя → сервер решает награду (античит) |
| `/arenaOpponents?rating=` | GET | Подбор противников арены ±100 рейтинга |
| `/chat` | GET/POST | Общий чат игроков (последние 50 сообщений) |

## Правила безопасности
- Прямая запись в Firestore от клиента запрещена (`firestore.rules`) — всё через функции.
- Ключи API не хранятся в клиенте и репозитории (см. `.gitignore`).
- `profileVersion` в профиле — защита старых игроков при обновлениях (урок оригинала).

## Итерация 4 (дальше)
- Аккаунты: анонимный auth Firebase + привязка Google Play Games.
- Колизей/Арена: оборонительные команды, рейтинг, награды за пороги (3 поражения/день —
  поля уже в профиле: `colosseumDay`, `colosseumLossesToday`).
- Чат: Firestore realtime listeners.

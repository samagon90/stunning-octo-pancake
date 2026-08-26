# Нативная реклама (AdMob) — подключение ПОСЛЕ релиза

По GDD §9 монетизация включается, когда игра стабильна и удерживает игроков.
Проект уже готов: интерфейс `IAdService`, слоты UI (`NativeAdSlotView`), тумблер
персонализации в настройках (`Profile.adsPersonalized`), заглушка `NullAdService`.

## Чек-лист подключения (когда решите)

1. **Аккаунт AdMob** → создать приложение (Android) → создать блок **Native Advanced**.
   Для разработки использовать тестовые ID (`ca-app-pub-3940256099942544/2247696110`).
2. **Импорт плагина:** Unity → Package Manager → Install by name/git →
   `com.google.ads.mobile` (Google Mobile Ads Unity Plugin, актуальный релиз).
3. **Символ компиляции:** Edit → Project Settings → Player → Other Settings →
   Scripting Define Symbols → добавить **`DMR_ADMOB`** (файл `AdMobService.cs` оживёт,
   до этого момента он не тянет SDK и не ломает билд).
4. **App ID:** Assets → Google Mobile Ads → Settings → App ID.
5. **Включить сервис:** `GameManager.Awake` → заменить `new NullAdService()` на
   `new AdMobService("<NativeAdUnitId>")`.
6. **Слоты UI** (компонент `NativeAdSlotView` уже размечает места, включается сам):
   - Главное меню — `AdSlot.MainMenu`
   - Экран результатов боя — `AdSlot.BattleResult`
   - Магазин — `AdSlot.Shop`
   - Лента героев — `AdSlot.HeroFeed`
7. **Реализация нативной загрузки:** в `AdMobService.cs` блок `#if DMR_ADMOB` содержит
   TODO-каркас (NativeAd.LoadNativeAd → RegisterNativeAdSceneObject). Ориентир —
   документация Google: Native Ads (Unity).

## Политики Google Play (обязательные)

- Пометка «Реклама» (AdChoices) на нативном блоке — обязательна.
- **Consent (GDPR/EEA):** перед первым запросом рекламы — UMP SDK / Consent Information;
   состояние «персонализация» брать из `Profile.adsPersonalized` (тумблер в настройках игры).
- Возрастной рейтинг стора согласовать с рекламой (у нас 12+ → без «взрослых» категорий).
- Не показывать рекламу на экране боя — только меню/результаты/магазин (уже размечено).

## Порядок включения (план)

1. Софт-лонч без рекламы → метрики D1/D7, стабильность (Crashlytics).
2.Retention ок → включаем нативную рекламу по чек-листу выше.
3. A/B: слоты MainMenu+BattleResult vs +Shop — смотреть удержание.

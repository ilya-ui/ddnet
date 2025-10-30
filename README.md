# Bank Admin App

Простое Android-приложение на Jetpack Compose, имитирующее панель администратора банка. После ввода правильного пароля (1691) администратор получает доступ к списку пользователей и может изменять их балансы.

## Возможности

- Экран входа с проверкой административного пароля.
- Список не-администраторов с отображением актуального баланса.
- Быстрое прибавление и вычитание средств с проверкой вводимого значения.
- Возможность выйти обратно на экран авторизации.

## Стек

- Kotlin
- Jetpack Compose
- Material 3

## Сборка APK

### Android Studio
1. Откройте директорию проекта в Android Studio.
2. Дождитесь окончания синхронизации Gradle.
3. Выберите **Build → Build Bundle(s) / APK(s) → Build APK(s)**.
4. Готовый `app-debug.apk` будет доступен в каталоге `app/build/outputs/apk/debug/`.

### Командная строка
1. Установите локально Gradle 8.1+ и Android SDK.
2. В корне репозитория выполните:
   ```bash
   gradle assembleDebug
   ```
3. Полученный APK ищите в `app/build/outputs/apk/debug/app-debug.apk`.

## Структура проекта

```
.
├── app
│   ├── build.gradle
│   ├── proguard-rules.pro
│   └── src/main
│       ├── AndroidManifest.xml
│       ├── java/com/example/bankadmin
│       │   ├── MainActivity.kt
│       │   └── ui/theme
│       │       ├── Color.kt
│       │       ├── Theme.kt
│       │       └── Type.kt
│       └── res/values
│           ├── strings.xml
│           └── themes.xml
├── build.gradle
├── settings.gradle
└── README.md
```

После сборки можно установить APK на устройство или эмулятор для тестирования функциональности.

# Empty Window Android App

This repository contains a minimal Android application that displays a completely empty window.

## Project structure

- `app/` – Android application module with the Kotlin activity and resources.
- `gradle/`, `gradlew`, `gradlew.bat` – Gradle wrapper for building the project.
- `artifacts/EmptyWindow-debug.apk` – Pre-built debug APK ready to install on a device or emulator.

## Building

To rebuild the APK locally, ensure that the Android SDK is installed and that the `ANDROID_SDK_ROOT` (or `ANDROID_HOME`) environment variable points to it, then run:

```bash
./gradlew assembleDebug
```

The resulting APK will appear at `app/build/outputs/apk/debug/app-debug.apk`.

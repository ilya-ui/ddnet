package com.example.bankadmin.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColorScheme = lightColorScheme(
    primary = RoyalBlue,
    onPrimary = Color.White,
    secondary = Emerald,
    onSecondary = Color.White,
    tertiary = EmeraldDark,
    background = SoftGray,
    onBackground = Charcoal,
    surface = Color.White,
    onSurface = Charcoal
)

private val DarkColorScheme = darkColorScheme(
    primary = RoyalBlueDark,
    onPrimary = Color.White,
    secondary = EmeraldDark,
    onSecondary = Color.White,
    tertiary = Emerald,
    background = Color(0xFF121212),
    onBackground = Color.White,
    surface = Color(0xFF1D1D1D),
    onSurface = Color.White
)

@Composable
fun BankAdminTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}

package com.example.telegramproxy

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.telegramproxy.ui.theme.TelegramProxyTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            val viewModel: MainViewModel = viewModel()
            val uiState = viewModel.uiState.collectAsStateWithLifecycle()

            TelegramProxyTheme {
                MainScreen(
                    uiState = uiState.value,
                    onTokenChange = viewModel::updateToken,
                    onStartPolling = viewModel::startPolling,
                    onStopPolling = viewModel::stopPolling,
                    onRefresh = viewModel::refreshOnce,
                    onSendReply = viewModel::sendReply,
                    onClearStatus = viewModel::clearStatusMessage,
                    onClearError = viewModel::clearErrorMessage
                )
            }
        }
    }
}

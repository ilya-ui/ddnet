package com.example.telegramproxy

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import java.util.LinkedHashMap
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainViewModel(
    private val service: TelegramService = TelegramService(),
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO
) : ViewModel() {

    private val _uiState = MutableStateFlow(MainUiState())
    val uiState: StateFlow<MainUiState> = _uiState.asStateFlow()

    private val messagesCache = LinkedHashMap<Long, TelegramMessage>()

    private var pollingJob: Job? = null
    private var lastUpdateId: Long? = null
    private var activeToken: String? = null

    fun updateToken(token: String) {
        _uiState.update { it.copy(token = token) }
    }

    fun startPolling() {
        val token = _uiState.value.token.trim()
        if (token.isEmpty()) {
            _uiState.update { it.copy(errorMessage = "Укажите токен бота") }
            return
        }

        activeToken = token

        if (_uiState.value.isPolling) {
            return
        }

        _uiState.update { it.copy(isPolling = true, statusMessage = "Получение сообщений запущено") }

        pollingJob = viewModelScope.launch {
            fetchUpdatesOnce(showLoading = true)
            while (isActive) {
                delay(POLLING_INTERVAL_MS)
                fetchUpdatesOnce()
            }
        }
    }

    fun stopPolling() {
        if (pollingJob == null) return
        stopPollingInternal()
        _uiState.update { it.copy(isPolling = false, statusMessage = "Получение сообщений остановлено") }
    }

    fun refreshOnce() {
        val token = _uiState.value.token.trim()
        if (token.isEmpty()) {
            _uiState.update { it.copy(errorMessage = "Укажите токен бота") }
            return
        }
        activeToken = token
        viewModelScope.launch {
            fetchUpdatesOnce(showLoading = true)
        }
    }

    fun sendReply(target: TelegramMessage, messageText: String) {
        val text = messageText.trim()
        if (text.isEmpty()) {
            _uiState.update { it.copy(errorMessage = "Введите текст ответа") }
            return
        }

        val currentToken = (activeToken ?: _uiState.value.token).trim()
        if (currentToken.isEmpty()) {
            _uiState.update { it.copy(errorMessage = "Укажите токен бота") }
            return
        }
        activeToken = currentToken

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            val result = withContext(ioDispatcher) {
                service.sendMessage(currentToken, target.chatId, text)
            }
            result.fold(
                onSuccess = {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            statusMessage = "Ответ отправлен"
                        )
                    }
                },
                onFailure = { error ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = error.message ?: "Не удалось отправить сообщение"
                        )
                    }
                }
            )
        }
    }

    fun clearStatusMessage() {
        _uiState.update { it.copy(statusMessage = null) }
    }

    fun clearErrorMessage() {
        _uiState.update { it.copy(errorMessage = null) }
    }

    private suspend fun fetchUpdatesOnce(showLoading: Boolean = false) {
        val token = activeToken ?: return
        if (showLoading) {
            _uiState.update { it.copy(isLoading = true) }
        }
        val offset = lastUpdateId?.plus(1)
        val result = withContext(ioDispatcher) { service.getUpdates(token, offset) }
        result.fold(
            onSuccess = { updates ->
                if (updates.isNotEmpty()) {
                    lastUpdateId = updates.maxOf { it.updateId }
                    val (newCount, orderedMessages) = appendMessages(updates)
                    _uiState.update { state ->
                        state.copy(
                            messages = orderedMessages,
                            isLoading = false,
                            statusMessage = if (showLoading) {
                                if (newCount > 0) {
                                    "Получено новых сообщений: $newCount"
                                } else {
                                    "Свежих сообщений нет"
                                }
                            } else {
                                state.statusMessage
                            },
                            errorMessage = null
                        )
                    }
                } else if (showLoading) {
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            statusMessage = "Свежих сообщений нет"
                        )
                    }
                } else {
                    _uiState.update { it.copy(isLoading = false) }
                }
            },
            onFailure = { error ->
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        errorMessage = error.message ?: "Не удалось получить обновления"
                    )
                }
                stopPollingInternal()
            }
        )
    }

    private fun appendMessages(updates: List<TelegramMessage>): Pair<Int, List<TelegramMessage>> {
        var newMessages = 0
        for (message in updates) {
            if (!messagesCache.containsKey(message.updateId)) {
                newMessages++
            }
            messagesCache[message.updateId] = message
        }
        if (messagesCache.size > MAX_CACHED_MESSAGES) {
            val trimmed = messagesCache.values
                .sortedByDescending { it.dateEpochSeconds }
                .take(MAX_CACHED_MESSAGES)
            messagesCache.clear()
            for (msg in trimmed) {
                messagesCache[msg.updateId] = msg
            }
        }
        val ordered = messagesCache.values.sortedByDescending { it.dateEpochSeconds }
        return newMessages to ordered
    }

    private fun stopPollingInternal() {
        pollingJob?.cancel()
        pollingJob = null
        _uiState.update { it.copy(isPolling = false) }
    }

    companion object {
        private const val POLLING_INTERVAL_MS = 4_000L
        private const val MAX_CACHED_MESSAGES = 200
    }
}

data class MainUiState(
    val token: String = "",
    val isPolling: Boolean = false,
    val isLoading: Boolean = false,
    val messages: List<TelegramMessage> = emptyList(),
    val statusMessage: String? = null,
    val errorMessage: String? = null
)

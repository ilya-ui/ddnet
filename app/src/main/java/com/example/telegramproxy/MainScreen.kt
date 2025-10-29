package com.example.telegramproxy

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Divider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun MainScreen(
    uiState: MainUiState,
    onTokenChange: (String) -> Unit,
    onStartPolling: () -> Unit,
    onStopPolling: () -> Unit,
    onRefresh: () -> Unit,
    onSendReply: (TelegramMessage, String) -> Unit,
    onClearStatus: () -> Unit,
    onClearError: () -> Unit
) {
    val snackbarHostState = remember { SnackbarHostState() }
    val replyDialogState = remember { ReplyDialogState() }

    LaunchedEffect(uiState.statusMessage) {
        val message = uiState.statusMessage
        if (!message.isNullOrBlank()) {
            snackbarHostState.showSnackbar(message)
            onClearStatus()
        }
    }

    LaunchedEffect(uiState.errorMessage) {
        val message = uiState.errorMessage
        if (!message.isNullOrBlank()) {
            snackbarHostState.showSnackbar(message)
            onClearError()
        }
    }

    replyDialogState.targetMessage?.let { target ->
        ReplyDialog(
            target = target,
            state = replyDialogState,
            onDismiss = { replyDialogState.close() },
            onSend = { text ->
                onSendReply(target, text)
                replyDialogState.close()
            }
        )
    }

    Scaffold(
        snackbarHost = { SnackbarHost(hostState = snackbarHostState) }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            TokenInputSection(
                token = uiState.token,
                onTokenChange = onTokenChange,
                isPolling = uiState.isPolling,
                onStartPolling = onStartPolling,
                onStopPolling = onStopPolling,
                onRefresh = onRefresh
            )

            if (uiState.isLoading) {
                LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
            }

            MessagesSection(
                messages = uiState.messages,
                onReplyRequested = { message -> replyDialogState.open(message) }
            )
        }
    }
}

@Composable
private fun TokenInputSection(
    token: String,
    onTokenChange: (String) -> Unit,
    isPolling: Boolean,
    onStartPolling: () -> Unit,
    onStopPolling: () -> Unit,
    onRefresh: () -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        OutlinedTextField(
            value = token,
            onValueChange = onTokenChange,
            label = { Text(text = stringResource(id = R.string.token_placeholder)) },
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            if (isPolling) {
                Button(onClick = onStopPolling) {
                    Text(text = stringResource(id = R.string.stop_polling))
                }
            } else {
                Button(onClick = onStartPolling) {
                    Text(text = stringResource(id = R.string.start_polling))
                }
            }
            OutlinedButton(onClick = onRefresh) {
                Text(text = stringResource(id = R.string.refresh))
            }
        }
    }
}

@Composable
private fun MessagesSection(
    messages: List<TelegramMessage>,
    onReplyRequested: (TelegramMessage) -> Unit
) {
    Column(modifier = Modifier.fillMaxSize()) {
        Text(
            text = stringResource(id = R.string.messages_header),
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.SemiBold
        )
        Spacer(modifier = Modifier.height(8.dp))
        Divider()
        Spacer(modifier = Modifier.height(8.dp))

        if (messages.isEmpty()) {
            Text(
                text = stringResource(id = R.string.no_messages),
                style = MaterialTheme.typography.bodyMedium
            )
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(messages) { message ->
                    MessageCard(
                        message = message,
                        onReplyRequested = onReplyRequested
                    )
                }
            }
        }
    }
}

@Composable
private fun MessageCard(
    message: TelegramMessage,
    onReplyRequested: (TelegramMessage) -> Unit
) {
    val formatter = rememberDateFormatter()

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = message.chatTitle,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold
            )
            Text(
                text = "От: ${message.senderName}",
                style = MaterialTheme.typography.bodyMedium
            )
            if (message.text.isNotBlank()) {
                Text(
                    text = message.text,
                    style = MaterialTheme.typography.bodyLarge,
                    maxLines = 4,
                    overflow = TextOverflow.Ellipsis
                )
            } else {
                Text(
                    text = "[Содержимое сообщения недоступно]",
                    style = MaterialTheme.typography.bodyMedium
                )
            }
            Text(
                text = formatter.format(Date(message.dateEpochSeconds * 1000)),
                style = MaterialTheme.typography.bodySmall
            )
            Row(horizontalArrangement = Arrangement.End, modifier = Modifier.fillMaxWidth()) {
                TextButton(onClick = { onReplyRequested(message) }) {
                    Text(text = stringResource(id = R.string.reply))
                }
            }
        }
    }
}

@Composable
private fun ReplyDialog(
    target: TelegramMessage,
    state: ReplyDialogState,
    onDismiss: () -> Unit,
    onSend: (String) -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(text = stringResource(id = R.string.dialog_reply_title))
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(text = "Чат: ${target.chatTitle}")
                OutlinedTextField(
                    value = state.replyText.value,
                    onValueChange = { state.replyText.value = it },
                    label = { Text(text = stringResource(id = R.string.dialog_reply_hint)) },
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    val text = state.replyText.value.trim()
                    if (text.isNotEmpty()) {
                        onSend(text)
                    }
                }
            ) {
                Text(text = stringResource(id = R.string.send))
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(text = stringResource(id = R.string.cancel))
            }
        }
    )
}

@Composable
private fun rememberDateFormatter(): SimpleDateFormat {
    return remember {
        SimpleDateFormat("dd.MM.yyyy HH:mm", Locale.getDefault())
    }
}

private class ReplyDialogState {
    var targetMessage: TelegramMessage? = null
        private set
    val replyText = mutableStateOf("")

    fun open(message: TelegramMessage) {
        targetMessage = message
        replyText.value = ""
    }

    fun close() {
        targetMessage = null
        replyText.value = ""
    }
}

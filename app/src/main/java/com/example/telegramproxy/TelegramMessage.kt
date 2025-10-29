package com.example.telegramproxy

data class TelegramMessage(
    val updateId: Long,
    val messageId: Long,
    val chatId: Long,
    val chatTitle: String,
    val senderName: String,
    val text: String,
    val dateEpochSeconds: Long
)

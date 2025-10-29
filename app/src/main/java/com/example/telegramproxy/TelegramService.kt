package com.example.telegramproxy

import java.io.IOException
import java.util.concurrent.TimeUnit
import okhttp3.FormBody
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject

class TelegramService(
    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(35, TimeUnit.SECONDS)
        .writeTimeout(35, TimeUnit.SECONDS)
        .build()
) {

    fun getUpdates(token: String, offset: Long?): Result<List<TelegramMessage>> {
        return runCatching {
            val url = buildString {
                append("https://api.telegram.org/bot")
                append(token)
                append("/getUpdates")
                val params = mutableListOf("timeout=10")
                if (offset != null) {
                    params.add("offset=$offset")
                }
                append('?')
                append(params.joinToString("&"))
            }

            val request = Request.Builder()
                .url(url)
                .get()
                .build()

            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    throw IOException("Код ошибки Telegram API: ${response.code}")
                }

                val bodyString = response.body?.string() ?: throw IOException("Пустой ответ от Telegram")
                parseUpdates(bodyString)
            }
        }
    }

    fun sendMessage(token: String, chatId: Long, text: String): Result<Unit> {
        return runCatching {
            val url = "https://api.telegram.org/bot$token/sendMessage"
            val requestBody = FormBody.Builder()
                .add("chat_id", chatId.toString())
                .add("text", text)
                .build()

            val request = Request.Builder()
                .url(url)
                .post(requestBody)
                .build()

            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    throw IOException("Код ошибки Telegram API: ${response.code}")
                }

                val bodyString = response.body?.string() ?: throw IOException("Пустой ответ от Telegram")
                val json = JSONObject(bodyString)
                if (!json.optBoolean("ok")) {
                    val description = json.optString("description", "Неизвестная ошибка Telegram API")
                    throw IOException(description)
                }
            }
        }
    }

    private fun parseUpdates(bodyString: String): List<TelegramMessage> {
        val json = JSONObject(bodyString)
        if (!json.optBoolean("ok")) {
            val description = json.optString("description", "Неизвестная ошибка Telegram API")
            throw IOException(description)
        }
        val resultArray = json.optJSONArray("result") ?: return emptyList()
        val messages = mutableListOf<TelegramMessage>()
        for (i in 0 until resultArray.length()) {
            val updateObject = resultArray.optJSONObject(i) ?: continue
            val updateId = updateObject.optLong("update_id")
            val messageObject = updateObject.optJSONObject("message")
                ?: updateObject.optJSONObject("edited_message")
                ?: updateObject.optJSONObject("channel_post")
                ?: updateObject.optJSONObject("edited_channel_post")
                ?: continue

            parseMessage(updateId, messageObject)?.let(messages::add)
        }
        return messages
    }

    private fun parseMessage(updateId: Long, messageObject: JSONObject): TelegramMessage? {
        val chatObject = messageObject.optJSONObject("chat") ?: return null
        val chatId = chatObject.optLong("id")
        if (chatId == 0L) return null
        val chatTitle = resolveChatTitle(chatObject)

        val fromObject = messageObject.optJSONObject("from")
        val senderName = resolveSenderName(fromObject)

        val text = when {
            messageObject.has("text") -> messageObject.optString("text", "")
            messageObject.has("caption") -> messageObject.optString("caption", "")
            else -> ""
        }

        val dateEpochSeconds = messageObject.optLong("date", System.currentTimeMillis() / 1000)

        return TelegramMessage(
            updateId = updateId,
            messageId = messageObject.optLong("message_id", updateId),
            chatId = chatId,
            chatTitle = chatTitle,
            senderName = senderName,
            text = text,
            dateEpochSeconds = dateEpochSeconds
        )
    }

    private fun resolveChatTitle(chat: JSONObject): String {
        val type = chat.optString("type")
        return when (type) {
            "private" -> {
                val firstName = chat.optString("first_name").takeIf { it.isNotBlank() }
                val lastName = chat.optString("last_name").takeIf { it.isNotBlank() }
                val username = chat.optString("username").takeIf { it.isNotBlank() }
                val fullName = listOfNotNull(firstName, lastName).joinToString(" ").ifBlank { null }
                fullName ?: username?.let { "@$it" } ?: chat.optLong("id").takeIf { it != 0L }?.toString()
                ?: "Чат ${chat.optLong("id")}".trim()
            }
            else -> {
                val title = chat.optString("title").takeIf { it.isNotBlank() }
                val username = chat.optString("username").takeIf { it.isNotBlank() }
                title ?: username?.let { "@$it" } ?: chat.optLong("id").takeIf { it != 0L }?.toString()
                ?: "Чат ${chat.optLong("id")}".trim()
            }
        }
    }

    private fun resolveSenderName(from: JSONObject?): String {
        if (from == null) return "Неизвестный пользователь"
        val firstName = from.optString("first_name").takeIf { it.isNotBlank() }
        val lastName = from.optString("last_name").takeIf { it.isNotBlank() }
        val username = from.optString("username").takeIf { it.isNotBlank() }
        val fullName = listOfNotNull(firstName, lastName).joinToString(" ").ifBlank { null }
        return fullName ?: username?.let { "@$it" } ?: "Неизвестный пользователь"
    }
}

package com.example.bankadmin

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
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
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardOptions
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.example.bankadmin.ui.theme.BankAdminTheme

private const val ADMIN_PASSWORD = "1691"

private val initialUsers = listOf(
    User(id = 0, name = "Администратор", balance = 5000, isAdmin = true),
    User(id = 1, name = "Алиса", balance = 3200),
    User(id = 2, name = "Борис", balance = 1750),
    User(id = 3, name = "Катя", balance = 2680),
    User(id = 4, name = "Марк", balance = 4100)
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            BankAdminTheme {
                BankAdminApp()
            }
        }
    }
}

data class User(
    val id: Int,
    val name: String,
    val balance: Int,
    val isAdmin: Boolean = false
)

@Composable
fun BankAdminApp() {
    var isAuthenticated by rememberSaveable { mutableStateOf(false) }
    val users = remember {
        mutableStateListOf<User>().apply { addAll(initialUsers) }
    }

    if (isAuthenticated) {
        AdminDashboard(
            users = users,
            onLogout = { isAuthenticated = false },
            onUpdateBalance = { userId, delta ->
                val index = users.indexOfFirst { it.id == userId }
                if (index >= 0) {
                    val user = users[index]
                    if (!user.isAdmin) {
                        users[index] = user.copy(balance = user.balance + delta)
                    }
                }
            }
        )
    } else {
        LoginScreen(onLoginSuccess = { isAuthenticated = true })
    }
}

@Composable
fun LoginScreen(onLoginSuccess: () -> Unit) {
    var password by rememberSaveable { mutableStateOf("") }
    var errorMessage by rememberSaveable { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "Добро пожаловать",
            style = MaterialTheme.typography.headlineMedium
        )
        Spacer(modifier = Modifier.height(24.dp))
        OutlinedTextField(
            value = password,
            onValueChange = {
                password = it
                errorMessage = null
            },
            label = { Text(text = "Пароль администратора") },
            singleLine = true,
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions.Default.copy(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(16.dp))
        Button(
            onClick = {
                if (password == ADMIN_PASSWORD) {
                    errorMessage = null
                    onLoginSuccess()
                } else {
                    errorMessage = "Неверный пароль"
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(text = "Войти")
        }
        errorMessage?.let { message ->
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = message,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.error
            )
        }
    }
}

@Composable
fun AdminDashboard(
    users: List<User>,
    onLogout: () -> Unit,
    onUpdateBalance: (userId: Int, delta: Int) -> Unit
) {
    val nonAdminUsers = users.filter { !it.isAdmin }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Управление счетами",
                style = MaterialTheme.typography.headlineSmall
            )
            TextButton(onClick = onLogout) {
                Text(text = "Выйти")
            }
        }
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            items(nonAdminUsers, key = { it.id }) { user ->
                UserCard(
                    user = user,
                    onUpdateBalance = { delta -> onUpdateBalance(user.id, delta) }
                )
            }
        }
    }
}

@Composable
fun UserCard(
    user: User,
    onUpdateBalance: (delta: Int) -> Unit
) {
    var amountText by remember { mutableStateOf("") }
    var errorMessage by remember { mutableStateOf<String?>(null) }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(text = user.name, style = MaterialTheme.typography.titleMedium)
            Text(text = "Баланс: ${user.balance} ₽", style = MaterialTheme.typography.bodyLarge)
            OutlinedTextField(
                value = amountText,
                onValueChange = { value ->
                    amountText = value.filter { it.isDigit() }
                    if (errorMessage != null) {
                        errorMessage = null
                    }
                },
                label = { Text(text = "Сумма операции") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                supportingText = {
                    if (errorMessage != null) {
                        Text(
                            text = errorMessage!!,
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                },
                modifier = Modifier.fillMaxWidth()
            )
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Button(
                    onClick = {
                        val amount = amountText.toIntOrNull()
                        if (amount == null || amount <= 0) {
                            errorMessage = "Введите положительное число"
                        } else {
                            onUpdateBalance(amount)
                            amountText = ""
                            errorMessage = null
                        }
                    },
                    modifier = Modifier.weight(1f)
                ) {
                    Text(text = "Добавить")
                }
                Button(
                    onClick = {
                        val amount = amountText.toIntOrNull()
                        if (amount == null || amount <= 0) {
                            errorMessage = "Введите положительное число"
                        } else {
                            onUpdateBalance(-amount)
                            amountText = ""
                            errorMessage = null
                        }
                    },
                    modifier = Modifier.weight(1f)
                ) {
                    Text(text = "Вычесть")
                }
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
fun LoginPreview() {
    BankAdminTheme {
        LoginScreen(onLoginSuccess = {})
    }
}

@Preview(showBackground = true)
@Composable
fun AdminPreview() {
    BankAdminTheme {
        AdminDashboard(
            users = initialUsers,
            onLogout = {},
            onUpdateBalance = { _, _ -> }
        )
    }
}

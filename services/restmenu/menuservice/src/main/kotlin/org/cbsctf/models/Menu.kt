package org.cbsctf.models

import org.bson.codecs.pojo.annotations.BsonId
import org.bson.internal.UuidHelper
import java.security.SecureRandom
import kotlin.streams.asSequence

data class MenuItem(
    val name: String,
    val price: Double,
    val description: String,
    val image: String? = null,
)

data class MenuCategory(
    val name: String,
    val items: List<MenuItem>,
)

data class Menu(
    @BsonId
    val id: String? = null,
    val name: String,
    val userId: String,
    val categories: List<MenuCategory> = emptyList(),
    val shared: Boolean = false,
    var shareToken: String = generateShareToken(16),
    var markdown: String? = null,
)

fun generateShareToken(tokenSize: Long): String {
    val alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    val sr = SecureRandom()

    return (1..tokenSize).map {
        alpha[sr.nextInt(alpha.length)]
    }.joinToString("")
}

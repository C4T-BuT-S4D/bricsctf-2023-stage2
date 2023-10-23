package org.cbsctf.models

import org.bson.codecs.pojo.annotations.BsonId

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
    var markdown: String? = null,
)

package org.cbsctf.dto

import kotlinx.serialization.Serializable

@Serializable
data class MenuItemDto(
    val name: String,
    val price: Double,
    val description: String,
    val image: String? = null,
)

@Serializable
data class MenuCategoryDto(
    val name: String,
    val items: List<MenuItemDto>,
)

@Serializable
data class MenuDto(
    var id: String,
    val name: String,
    val categories: List<MenuCategoryDto> = emptyList(),
    val author: String,
    val shared: Boolean = false,
    val markdown: String? = null,
)

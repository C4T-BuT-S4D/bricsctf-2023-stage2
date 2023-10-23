package org.cbsctf.dto

import kotlinx.serialization.Serializable

@Serializable
data class CreateMenuRequest(
    val name: String,
)

@Serializable
data class UpdateMenuRequest(
    val menu: MenuDto,
)

@Serializable
data class AuthRequest(
    val username: String,
    val password: String,
)

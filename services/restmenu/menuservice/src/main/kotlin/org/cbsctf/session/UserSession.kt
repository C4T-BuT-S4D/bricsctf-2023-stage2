package org.cbsctf.session

import io.ktor.server.auth.*
import kotlinx.serialization.Serializable

@Serializable
data class UserSession(
    val id: String,
    val username: String,
) : Principal

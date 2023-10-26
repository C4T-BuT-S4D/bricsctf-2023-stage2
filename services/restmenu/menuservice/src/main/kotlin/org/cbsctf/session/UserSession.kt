package org.cbsctf.session

import io.ktor.server.auth.*

data class UserSession(
    val id: String,
    val username: String,
) : Principal

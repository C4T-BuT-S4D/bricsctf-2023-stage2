package org.cbsctf.converter

import org.cbsctf.dto.UserDto
import org.cbsctf.models.User

fun User.toDto() = UserDto(id = id.toString(), username = username, password = password)

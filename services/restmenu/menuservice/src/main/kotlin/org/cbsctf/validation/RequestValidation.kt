package org.cbsctf.validation

import io.ktor.server.plugins.requestvalidation.*
import org.cbsctf.dto.AuthRequest
import org.cbsctf.dto.CreateMenuRequest
import org.cbsctf.dto.MenuDto
import org.cbsctf.dto.UpdateMenuRequest
import java.net.URI
import java.net.URISyntaxException

fun isAlphaNumeric(string: String): Boolean {
    return string.all { it.isLetter() || it.isDigit() }
}

fun isValidName(name: String): Boolean {
    val allowed = setOf(',', '.', '!', '-', '_')
    return name.all { it.isLetter() || it.isDigit() || it.isWhitespace() || allowed.contains(it) }
}

fun isValidItem(name: String): Boolean {
    val allowed = setOf(',', '.', '!', '-', '_', '(', ')', '=')
    return name.all { it.isLetter() || it.isDigit() || it.isWhitespace() || allowed.contains(it) }
}

fun isValidImage(img: String?): Boolean {
    try {
        img?.let { URI(it) } ?: return true
    } catch (exc: URISyntaxException) {
        return false
    }
    return true
}

fun validateAuthRequest(request: AuthRequest): ValidationResult {
    if (request.username.length < 8) {
        return ValidationResult.Invalid("Username must be at least 8 characters long")
    }
    if (!isAlphaNumeric(request.username)) {
        return ValidationResult.Invalid("Username should be alphanumeric")
    }
    if (request.password.length < 8) {
        return ValidationResult.Invalid("Password must be at least 8 characters long")
    }
    return ValidationResult.Valid
}

fun validateMenuRequest(menu: MenuDto): ValidationResult {
    if (!isValidName(menu.name)) {
        return ValidationResult.Invalid("Menu name should be valid")
    }
    if (menu.categories.any { !isValidName(it.name) }) {
        return ValidationResult.Invalid("Category name should be valid")
    }
    for (category in menu.categories) {
        if (category.items.any { !isValidItem(it.name) }) {
            return ValidationResult.Invalid("Item name should be valid")
        }
        if (category.items.any { !isValidItem(it.description) }) {
            return ValidationResult.Invalid("Item description should be valid")
        }
        if (category.items.any { it.price <= 0 }) {
            return ValidationResult.Invalid("Item price should be positive")
        }
        if (category.items.any { !isValidImage(it.image) }) {
            return ValidationResult.Invalid("Item image should be valid relative URI")
        }
    }

    return ValidationResult.Valid
}

fun configureValidators(cfg: RequestValidationConfig) {
    cfg.validate<AuthRequest> { request ->
        validateAuthRequest(request)
    }
    cfg.validate<CreateMenuRequest> { request ->
        if (isValidName(request.name)) {
            ValidationResult.Valid
        } else {
            ValidationResult.Invalid("Menu name should be valid")
        }
    }
    cfg.validate<UpdateMenuRequest> { request ->
        validateMenuRequest(request.menu)
    }
}

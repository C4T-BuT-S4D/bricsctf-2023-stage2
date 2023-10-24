package org.cbsctf.routes

import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.server.sessions.*
import org.cbsctf.dto.AuthRequest
import org.cbsctf.service.UserService
import org.cbsctf.session.UserSession

fun Routing.auth(userService: UserService) {
    post("/signup") {
        val authRequest = call.receive<AuthRequest>()
        userService.findUser(authRequest.username)?.let {
            call.respond(Error("User already exists"))
        } ?: run {
            userService.createUser(authRequest.username, authRequest.password).let {
                call.sessions.set(UserSession(it.id, it.username))
                call.respond(it)
            }
        }
    }
    post("/login") {
        val authRequest = call.receive<AuthRequest>()
        userService.login(authRequest.username, authRequest.password)?.let {
            call.sessions.set(UserSession(it.id, it.username))
            call.respond(it)
        } ?: call.respond(Error("Invalid username or password"))
    }
}

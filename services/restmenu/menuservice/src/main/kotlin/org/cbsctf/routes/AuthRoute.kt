package org.cbsctf.routes

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.auth.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.server.sessions.*
import org.cbsctf.dto.AuthRequest
import org.cbsctf.models.User
import org.cbsctf.service.UserService
import org.cbsctf.session.UserSession

fun Routing.auth(userService: UserService) {
    authenticate("auth-session", optional = true) {
        post("/api/logout") {
            call.sessions.clear<UserSession>()
            call.respond("Logged out")
        }

        get ("/api/user") {
            val userSession = call.principal<UserSession>() ?: run {
                call.respond(HttpStatusCode.OK)
                return@get
            }
            call.respond(userSession)
        }
    }

    post("/api/signup") {
        val authRequest = call.receive<AuthRequest>()
        userService.findUser(authRequest.username)?.let {
            call.respond(HttpStatusCode.Conflict, Error("User already exists"))
            return@post
        } ?: run {
            userService.createUser(authRequest.username, authRequest.password).let {
                call.sessions.set(UserSession(it.id, it.username))
                call.respond(it)
            }
        }
    }
    post("/api/login") {
        val authRequest = call.receive<AuthRequest>()
        userService.login(authRequest.username, authRequest.password)?.let {
            call.sessions.set(UserSession(it.id, it.username))
            call.respond(it)
        } ?: call.respond(HttpStatusCode.PreconditionFailed, Error("Invalid username or password"))
    }
}

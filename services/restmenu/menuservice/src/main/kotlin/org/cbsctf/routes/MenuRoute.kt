package org.cbsctf.routes

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.auth.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import org.cbsctf.dto.CreateMenuRequest
import org.cbsctf.dto.UpdateMenuRequest
import org.cbsctf.service.MenuService
import org.cbsctf.session.UserSession

fun Routing.menu(menuService: MenuService) {
    authenticate("auth-session", optional = true) {
        get("/api/get/{menuId}") {
            val menuId = call.parameters["menuId"] ?: ""
            val userId = call.principal<UserSession>()?.id ?: ""
            val shareToken = call.request.queryParameters["shareToken"]

            menuService.getMenu(menuId, userId, shareToken)?.let {
                call.respond(it)
            } ?: run {
                call.respond(HttpStatusCode.NotFound, Error("Menu not found or you don't have access to it"))
            }
        }

        get("/api/render/{menuId}") {
            val menuId = call.parameters["menuId"] ?: ""
            val userId = call.principal<UserSession>()?.id ?: ""
            val shareToken = call.request.queryParameters["shareToken"]

            menuService.getMenu(menuId, userId, shareToken)?.let {
                call.respond(menuService.renderPDF(it))
            } ?: run {
                call.respond(HttpStatusCode.NotFound, Error("Menu not found or you don't have access to it"))
            }
        }
    }

    authenticate("auth-session", optional = false) {
        get("/api/get") {
            val userSession = call.principal<UserSession>() ?: error("Invalid session")
            call.respond(menuService.getMenusByUser(userSession.id))
        }

        post("/api/create") {
            val userSession = call.principal<UserSession>() ?: error("Invalid session")
            val createMenuRequest = call.receive<CreateMenuRequest>()
            call.respond(menuService.createMenu(userSession.id, createMenuRequest.name))
        }

        post("/api/update") {
            val userSession = call.principal<UserSession>() ?: error("Invalid session")

            val updatedMenuRequest = call.receive<UpdateMenuRequest>()
            val updatedMenu = updatedMenuRequest.menu

            val updated = menuService.updateMenu(updatedMenu, userSession.id) ?: run {
                call.respond(HttpStatusCode.NotFound, Error("Menu not found or you don't have access to it"))
                return@post
            }

            call.respond(updated)
        }

        post("/api/delete/{menuId}") {
            val menuId = call.parameters["menuId"] ?: ""
            val userSession = call.principal<UserSession>() ?: error("Invalid session")

            menuService.deleteMenu(menuId, userSession.id)
            call.respond(HttpStatusCode.OK)
        }
    }
}

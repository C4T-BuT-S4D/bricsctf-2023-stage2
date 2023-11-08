package org.cbsctf

import com.mongodb.client.MongoDatabase
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.auth.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.server.plugins.requestvalidation.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.server.sessions.*
import org.cbsctf.client.HttpRendererClient
import org.cbsctf.routes.auth
import org.cbsctf.routes.files
import org.cbsctf.routes.menu
import org.cbsctf.service.FileService
import org.cbsctf.service.MenuService
import org.cbsctf.service.UserService
import org.cbsctf.session.UserSession
import org.cbsctf.validation.configureValidators
import org.litote.kmongo.KMongo
import java.io.File

fun main(args: Array<String>) {
    io.ktor.server.netty.EngineMain.main(args)
}

fun Application.module() {
    configureSerialization()
    configureSessions()
    configureRouting(environment)
    configureValidations()
}

fun initDB(connection: String): MongoDatabase {
    val client = KMongo.createClient(connection)
    return client.getDatabase("restmenu")
}

fun Application.configureRouting(environment: ApplicationEnvironment) {
    val db = initDB(
        environment.config.propertyOrNull("db.connection")?.getString() ?: "mongodb://localhost:27017"
    )

    val userService = UserService(db)
    val fileService =
        FileService(
            environment.config.propertyOrNull("uploads.path")?.getString() ?: "/tmp/",
        )
    val menuService =
        MenuService(
            db,
            HttpRendererClient(
                environment.config.property("renderer.url").getString(),
            ),
        )

    routing {
        auth(userService)
        menu(menuService)
        files(fileService)
    }
}

fun Application.configureSerialization() {
    install(ContentNegotiation) {
        json()
    }
}

fun Application.configureValidations() {
    install(RequestValidation) {
        configureValidators(this)
    }
    install(StatusPages) {
        exception<RequestValidationException> { call, cause ->
            call.respond(HttpStatusCode.BadRequest, cause.reasons.joinToString())
        }
    }
}

fun Application.configureSessions() {
    install(Sessions) {
        cookie<UserSession>("user-session", directorySessionStorage(File("build/.sessions"))) {
        }
    }
    install(Authentication) {
        session<UserSession>("auth-session") {
            validate { session ->
                if (session.id.isNotEmpty()) {
                    session
                } else {
                    null
                }
            }
        }
    }
}

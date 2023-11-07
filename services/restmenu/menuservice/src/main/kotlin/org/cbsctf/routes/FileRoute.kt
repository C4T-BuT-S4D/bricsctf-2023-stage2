package org.cbsctf.routes

import io.ktor.http.*
import io.ktor.http.content.*
import io.ktor.server.application.*
import io.ktor.server.auth.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.Serializable
import org.cbsctf.service.FileService
import org.cbsctf.session.UserSession
import java.io.File

@Serializable
data class UploadFileResponse(
    val id: String,
)

@Serializable
data class UserFilesResponse(
    val files: List<String>,
)

fun Routing.files(fileService: FileService) {
    get("/api/file/{filename...}") {
        val filename = call.parameters.getAll("filename")?.joinToString("/") ?: error("Invalid filename")

        val f = File(
            fileService.getFilePath(
                filename,
            ),
        )
        if (f.exists()) {
            call.respondFile(f)
        } else {
            call.respond(HttpStatusCode.NotFound)
        }
    }

    authenticate("auth-session", optional = false) {
        post("/api/file/upload") {
            val userSession = call.principal<UserSession>() ?: error("Invalid session")

            val multipart = call.receiveMultipart()
            var filename = ""

            multipart.forEachPart { part ->
                when (part) {
                    is PartData.FileItem -> {
                        val originalName = part.originalFileName as String
                        val ext = originalName.substringAfterLast(".", "")
                        val fileBytes = part.streamProvider().readBytes()
                        filename = fileService.saveFileForUser(userSession.id, ext, fileBytes)
                    }

                    else -> {}
                }
                part.dispose()
            }

            call.respond(UploadFileResponse(filename))
        }

        get("/api/file") {
            val userSession = call.principal<UserSession>() ?: error("Invalid session")

            val files = fileService.getUserFiles(userSession.id)

            call.respond(UserFilesResponse(files))
        }
    }
}

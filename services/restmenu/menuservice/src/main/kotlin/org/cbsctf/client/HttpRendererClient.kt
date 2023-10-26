package org.cbsctf.client

import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.request.*
import io.ktor.http.*
import org.cbsctf.dto.MenuDto

class HttpRendererClient(private val rendererURL: String) : RendererClient {
    private val client = HttpClient(CIO)

    override suspend fun render(dto: MenuDto): ByteArray {
        val response =
            client.get(rendererURL) {
                url {
                    appendPathSegments("api", "render", dto.id)
                }
            }
        return response.body()
    }
}

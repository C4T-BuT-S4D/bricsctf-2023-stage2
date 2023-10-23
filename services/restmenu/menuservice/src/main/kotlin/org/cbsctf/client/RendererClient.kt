package org.cbsctf.client

import org.cbsctf.dto.MenuDto

interface RendererClient {
    suspend fun render(dto: MenuDto): ByteArray
}

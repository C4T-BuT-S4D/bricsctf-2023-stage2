package org.cbsctf.service

import java.io.File
import java.nio.file.Files
import kotlin.random.Random

class FileService(private val uploadRoot: String) {
    fun saveFileForUser(
        userId: String,
        extension: String,
        data: ByteArray,
    ): String {
        val newId = generateRandomFileName(extension)
        val relPath = "$userId/$newId"
        Files.createDirectories(File("$uploadRoot/$userId").toPath())
        val file = File("$uploadRoot/$relPath")
        file.writeBytes(data)
        return relPath
    }

    fun getUserFiles(userId: String): List<String> {
        return File("$uploadRoot/$userId").walk().filter { it.isFile }.map { "$userId/${it.name}" }.toList()
    }

    fun getFilePath(filename: String): String {
        return "$uploadRoot/$filename"
    }

    private fun generateRandomFileName(ext: String): String {
        return generateRandomString(10) + "." + ext
    }

    private fun generateRandomString(length: Int): String {
        val charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        val random = Random.Default
        return (1..length)
            .map { charset[random.nextInt(0, charset.length)] }
            .joinToString("")
    }
}

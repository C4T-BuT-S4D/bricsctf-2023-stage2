package org.cbsctf.service

import com.mongodb.client.MongoDatabase
import org.cbsctf.converter.toDto
import org.cbsctf.dto.UserDto
import org.cbsctf.models.User
import org.litote.kmongo.*

class UserService(db: MongoDatabase) {
    private val users = db.getCollection<User>()

    fun login(
        username: String,
        password: String,
    ): UserDto? {
        return users.findOne(and(User::username eq username, User::password eq password))?.toDto()
    }

    fun findUser(username: String): UserDto? {
        return users.findOne(User::username eq username)?.toDto()
    }

    fun createUser(
        username: String,
        password: String,
    ): UserDto {
        val user = User(username = username, password = password)
        return user.apply { users.insertOne(user) }.toDto()
    }
}

package org.cbsctf.models

import org.bson.codecs.pojo.annotations.BsonId
import org.litote.kmongo.Id

data class User(
    @BsonId
    val id: Id<User>? = null,
    val username: String,
    val password: String,
)

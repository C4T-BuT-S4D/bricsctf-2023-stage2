package org.cbsctf.service

import com.mongodb.client.MongoDatabase
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.response.*
import org.cbsctf.client.RendererClient
import org.cbsctf.converter.toDto
import org.cbsctf.converter.toModel
import org.cbsctf.dto.MenuDto
import org.cbsctf.models.Menu
import org.cbsctf.routes.Error
import org.litote.kmongo.*

class MenuService(db: MongoDatabase, client: RendererClient) {
    private val menus = db.getCollection<Menu>()
    private val rendererClient = client

    fun getMenu(
        id: String,
        userId: String,
        shareToken: String? = null,
    ): MenuDto? {
        return menus.findOneById(id)
            ?.takeIf { it.userId == userId || it.shared || it.shareToken == shareToken.orEmpty() }?.toDto()
    }

    fun createMenu(
        uId: String,
        name: String,
    ): MenuDto {
        val menu = Menu(name = name, userId = uId)
        menu.markdown = generateMarkdown(menu)
        return menu.apply { menus.insertOne(menu) }.toDto()
    }

    fun updateMenu(updatedMenu: MenuDto, uid: String): MenuDto? {
        val existingMenu = this.getMenu(updatedMenu.id, uid) ?: return null
        val menu = updatedMenu.toModel()
        menu.shareToken = existingMenu.shareToken
        menu.markdown = generateMarkdown(menu)
        return menu.apply { menu.id?.let { menus.updateOneById(it, menu) } }.toDto()
    }

    fun deleteMenu(
        id: String,
        userId: String,
    ) {
        val menuId = menus.findOneById(id)?.takeIf { it.userId == userId }?.id ?: return
        menus.deleteOneById(menuId)
    }

    fun getMenusByUser(userId: String): List<MenuDto> {
        return menus.find(Menu::userId eq userId).toList().map { it.toDto() }
    }

    suspend fun renderPDF(menuDto: MenuDto): ByteArray {
        return this.rendererClient.render(menuDto)
    }

    private fun generateMarkdown(menu: Menu): String {
        val sb = StringBuilder()
        sb.append("${menu.name}\n")
        sb.append("=".repeat(menu.name.length) + "\n\n")
        for (category in menu.categories) {
            sb.append("${category.name}\n")
            sb.append("-".repeat(category.name.length) + "\n\n")
            for (item in category.items) {
                sb.append("**${item.name}** — ${item.price}\n\n")
                sb.append("${item.description}\n\n")
                if (item.image != null) {
                    sb.append("![${item.name}](${generateMenuItemImage(item.image)})\n\n")
                }
            }
        }
        return sb.toString()
    }

    private fun generateMenuItemImage(image: String): String {
        return "file/$image"
    }
}

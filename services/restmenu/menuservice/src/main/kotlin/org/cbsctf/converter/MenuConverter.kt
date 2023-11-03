package org.cbsctf.converter

import org.cbsctf.dto.MenuCategoryDto
import org.cbsctf.dto.MenuDto
import org.cbsctf.dto.MenuItemDto
import org.cbsctf.models.Menu
import org.cbsctf.models.MenuCategory
import org.cbsctf.models.MenuItem

fun Menu.toDto() =
    MenuDto(
        id = id.toString(),
        name = name,
        author = userId,
        shared = shared,
        markdown = markdown,
        shareToken = shareToken,
        categories =
            categories.map { category ->
                MenuCategoryDto(
                    name = category.name,
                    items =
                        category.items.map { item ->
                            MenuItemDto(
                                name = item.name,
                                price = item.price,
                                description = item.description,
                                image = item.image,
                            )
                        },
                )
            },
    )

fun MenuDto.toModel() =
    Menu(
        id = id,
        name = name,
        userId = author,
        shared = shared,
        markdown = markdown,
        shareToken = shareToken,
        categories =
            categories.map { category ->
                MenuCategory(
                    name = category.name,
                    items =
                        category.items.map { item ->
                            MenuItem(
                                name = item.name,
                                price = item.price,
                                description = item.description,
                                image = item.image,
                            )
                        },
                )
            },
    )

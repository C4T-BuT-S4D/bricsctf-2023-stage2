package org.cbs.renderer.repository;

import org.cbs.renderer.dto.Menu;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface MenuRepository extends MongoRepository<Menu, String> {
}

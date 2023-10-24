package org.cbs.renderer.service;

import org.cbs.renderer.repository.MenuRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
@Qualifier("open")
public class OpenRendererService implements RendererService {
    private static final Logger logger = LoggerFactory.getLogger(OpenRendererService.class);
    private final MenuRepository menuRepository;
    private final MenuRenderer menuRenderer;

    @Autowired
    OpenRendererService(MenuRepository menuRepository,
                        MenuRenderer menuRenderer) {
        this.menuRepository = menuRepository;
        this.menuRenderer = menuRenderer;
    }

    @Override
    public Optional<byte[]> render(String id) throws Exception {
        var maybeCard = menuRepository.findById(id);
        // I hate java checked exception.
        if (maybeCard.isPresent()) {
            var card = maybeCard.get();
            return Optional.of(menuRenderer.render(card));
        }
        return Optional.empty();
    }
}

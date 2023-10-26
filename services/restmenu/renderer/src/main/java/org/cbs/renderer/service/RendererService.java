package org.cbs.renderer.service;

import java.util.Optional;


public interface RendererService {
    Optional<byte[]> render(String id) throws Exception;
}

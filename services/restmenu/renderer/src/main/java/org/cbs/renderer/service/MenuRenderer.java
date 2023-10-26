package org.cbs.renderer.service;

import org.cbs.renderer.dto.Menu;

public interface MenuRenderer {
    byte[] render(Menu menu) throws Exception;
}

  
# -*- coding: utf-8 -*-
import glfw
import OpenGL.GL as gl

import imgui

from imgui.integrations.glfw import GlfwRenderer

import ctypes
from mpv import MPV, MpvRenderContext, OpenGlCbGetProcAddrFn

def main():
    imgui.create_context()
    ctx,player,window = impl_glfw_init()
    impl = GlfwRenderer(window)


    _   = gl.glGenFramebuffers(1)
    fbo = gl.glGenFramebuffers(1)
    playbackPos = (0,)
    volume = (0,)

    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)


    texture = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
    
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

    gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, texture, 0)

    gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)


    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        imgui.new_frame()

        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):

                clicked_quit, selected_quit = imgui.menu_item(
                    "Quit", 'Cmd+Q', False, True
                )

                if clicked_quit:
                    exit(1)

                imgui.end_menu()
            imgui.end_main_menu_bar()

        imgui.begin("Video window", True, flags=imgui.WINDOW_NO_SCROLLBAR)

        w,h = imgui.core.get_content_region_available()
        w=int(max(w,0))
        h=int(max(h-80,0))

        imgui.text("Filename: {}".format(player.filename))
        imgui.text("{0:.2f}s/{1:.2f}s ({2:.2f}s remaining)".format(player.time_pos,player.duration,player.playtime_remaining))

        if ctx.update() and w>0 and h>0:
          gl.glBindTexture(gl.GL_TEXTURE_2D, texture);
          gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, w, h, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None);
          ctx.render(flip_y=False, opengl_fbo={'w': w, 'h': h, 'fbo': fbo})
        imgui.image(fbo, w, h)

        changed, values = imgui.slider_float(
            "Playback Percentage", *playbackPos,
            min_value=0.0, max_value=100.0,
            format="%.0f",
            power=1.0
        )

        if changed:
          player.command('seek',values,'absolute-percent')
          playbackPos = (values,)
        else:
          playbackPos = (player.percent_pos,)
          


        changed, values = imgui.slider_float(
            "Volume", *volume,
            min_value=0.0, max_value=100.0,
            format="%.0f",
            power=1.0
        )

        if changed:
          player.volume = values
          volume = (values,)
        else:
          volume = (player.volume,)


        imgui.end()

        gl.glClearColor(0., 0., 0., 1.)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)


    player.terminate()
    impl.shutdown()
    glfw.terminate()


def impl_glfw_init():
    width, height = 1280, 720
    window_name = "minimal ImGui/GLFW3/pythonMPV example"

    if not glfw.init():
        print("Could not initialize OpenGL context")
        exit(1)

    # OS X supports only forward-compatible core profiles from 3.2
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(
        int(width), int(height), window_name, None, None
    )
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        exit(1)

    def get_process_address(_, name):
        print(name)
        address = glfw.get_proc_address(name.decode('utf8'))
        return ctypes.cast(address, ctypes.c_void_p).value

    proc_addr_wrapper = OpenGlCbGetProcAddrFn(get_process_address)

    ctx = None
    mpv = MPV(log_handler=print, loglevel='debug')
    

    ctx = MpvRenderContext(mpv, 'opengl', opengl_init_params={'get_proc_address': proc_addr_wrapper})

    
    mpv.play('sample.mp4')
    mpv.volume=0

    return ctx,mpv,window


if __name__ == "__main__":
    main()
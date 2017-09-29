class RendererFactory():
    @classmethod
    def create_OpenGL_renderer_from_scene(cls, scene):
        from .OpenGL.OpenGLRenderer import OpenGLRenderer 
        return OpenGLRenderer(scene);

    @classmethod
    def create_PovRay_renderer_from_scene(cls, scene):
        from .PovRay.PovRayRenderer import PovRayRenderer
        return PovRayRenderer(scene);

    @classmethod
    def create_Mitsuba_renderer_from_scene(cls, scene):
        from .Mitsuba.MitsubaRenderer import MitsubaRenderer
        return MitsubaRenderer(scene);


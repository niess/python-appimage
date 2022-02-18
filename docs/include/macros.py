import os

def define_env(env):
    """Custom filters and macros"""

    def format_attributes(*args, **kwargs):
        """Format HTML attributes"""
        if args:
            cls, id_ = [], None
            for arg in args:
                if arg[0] == ".":
                    cls.append(arg[1:])
                elif arg[0] == "#":
                    id_ = arg[1:]
                else:
                    raise ValueError(f"Invalid attribute ({arg})")

            if cls:
                try:
                    kwargs["class"] += " " + " ".join(cls)
                except KeyError:
                    kwargs["class"] = " ".join(cls)

            if id_:
                kwargs["id"] = id_

        if kwargs:
            attr = []
            for k, v in kwargs.items():
                attr.append(f"{k} = \"{v}\"")
            attr = " ".join(attr)
        else:
            attr = ""

        return attr


    @env.filter
    def attr(text, *args, **kwargs):
        """Add HTML attributes to a text using a <span>"""

        attr = format_attributes(*args, **kwargs)

        return f"<span {attr} markdown=\"1\">{text}</span>"


    @env.filter
    def cls(text, *args):
        """Add HTML class(es) to a text using a <span>"""

        cls = " ".join(args)

        return f"<span class=\"{cls}\" marckdown=\"1\">{text}</span>"


    @env.filter
    def id(text, id_):
        """Add HTML id to a text using a <span>"""

        return f"<span id=\"{id_}\" markdown=\"1\">{text}</span>"


    @env.filter
    def url(raw):
        """Wrap a raw URL with a link"""

        return f"[{raw}]({raw})"


    @env.macro
    def begin(*args, **kwargs):
        """Start a new HTML <div>"""

        attr = format_attributes(*args, **kwargs)

        return f"<div {attr} markdown=\"1\">"


    @env.macro
    def end(comment=None):
        """End an HTML <div>"""

        return "</div>"


    @env.macro
    def importjs(name):
        """Import a JavaScript script"""

        current = "/" + env.page.url
        relpath = os.path.relpath("/js", start=current)

        return f"<script src=\"{relpath}/{name}.js\" defer></script>"

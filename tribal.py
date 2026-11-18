"""Earth patterns in the spirit of mud cloth and old clay vessels: dots, chevrons,
short strokes and rings, drawn slightly unevenly so they read as made by hand.
Returned as CSS background images (data URIs)."""
from urllib.parse import quote


def _uri(svg):
    return 'url("data:image/svg+xml,' + quote(svg, safe=" =:/,.-()") + '")'


def strip(color="#B06F4F", opacity=.6):
    """A narrow band, repeated across the page width: a fine line, and between its
    breaks a small triangle, three short strokes, a diamond and a ring with a dot."""
    c = color
    s = (f"<svg xmlns='http://www.w3.org/2000/svg' width='120' height='16' viewBox='0 0 120 16'>"
         f"<g fill='none' stroke='{c}' stroke-width='1' stroke-linecap='round' stroke-linejoin='round' opacity='{opacity}'>"
         "<path d='M0 8 H8 M22 8 H30 M52 8 H60 M72 8 H80 M98 8 H106 M118 8 H120'/>"
         "<path d='M11 11 L15 4.6 L19 11 Z'/>"
         "<path d='M37 4.5 V11.5 M41 4.5 V11.5 M45 4.5 V11.5'/>"
         "<path d='M66 3.8 L70 8 L66 12.2 L62 8 Z'/>"
         "<circle cx='92' cy='8' r='3.6'/>"
         "</g>"
         f"<g fill='{c}' opacity='{opacity}'><circle cx='92' cy='8' r='1'/><circle cx='86' cy='8' r='.9'/><circle cx='112' cy='8' r='.9'/></g></svg>")
    return _uri(s)


def cloth(color="#FBEDE3", opacity=.13):
    """A loose mud cloth field for large surfaces."""
    c = color
    s = (f"<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120'>"
         f"<g fill='none' stroke='{c}' stroke-width='1.6' stroke-linecap='round' opacity='{opacity}'>"
         "<path d='M8 14 h16 M36 13.4 h16 M64 14.3 h16 M92 13.8 h16'/>"
         "<path d='M14 40 l6 7 l6 -7 M50 40.5 l6 7 l6 -7.2 M86 40 l6 7.2 l6 -7'/>"
         "<circle cx='30' cy='78' r='7'/><circle cx='90' cy='80' r='7'/>"
         "<path d='M54 72 l12 12 M66 72 l-12 12'/>"
         "<path d='M8 104 h16 M36 104.6 h16 M64 103.8 h16 M92 104.3 h16'/>"
         "</g>"
         f"<g fill='{c}' opacity='{opacity}'>"
         "<circle cx='30' cy='78' r='1.6'/><circle cx='90' cy='80' r='1.6'/>"
         "<circle cx='12' cy='62' r='1.4'/><circle cx='48' cy='61' r='1.4'/><circle cx='72' cy='62' r='1.4'/><circle cx='108' cy='61' r='1.4'/>"
         "</g></svg>")
    return _uri(s)

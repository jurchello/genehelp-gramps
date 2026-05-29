#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2026 Yurii Liubymyi <jurchello@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#

"""Plugin registration for the GeneHelp gramplet."""

register(
    GRAMPLET,
    id="Genehelp",
    name="GeneHelp",
    description=_("Send selected Gramps records to GeneHelp as an online request."),
    status=STABLE,
    version="0.10.0",
    fname="Genehelp.py",
    height=380,
    detached_width=620,
    detached_height=620,
    expand=True,
    gramplet="GeneHelpGramplet",
    gramplet_title="GeneHelp",
    gramps_target_version="6.0",
    navtypes=[
        "Media",
        "Note",
        "Repository",
        "Citation",
        "Source",
        "Place",
        "Event",
        "Family",
        "Person",
    ],
    include_in_listing=True,
    help_url="Genehelp",
)

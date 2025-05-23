/*-Update content according to release metadata */
$.getJSON("https://api.github.com/repos/niess/python-appimage/releases").done(function(data) {

    /* Unpack release metadata */
    const releases = []
    for (const datum of data) {
        if (!datum.name.startsWith("Python")) continue;
        var full_version = undefined;
        const assets = [];
        for (const asset of datum.assets) {
            if (asset.name.endsWith(".AppImage")) {
                /* Parse AppImage metadata */
                const tmp0 = asset.name.split("manylinux")
                const tag = tmp0[1].slice(0,-9);
                const tmp1 = tag.split(/_(.+)/, 2);
                var linux = undefined;
                var arch = undefined;
                if (tmp1[0] == "") {
                    const tmp3 = tmp1[1].split("_");
                    linux = tmp3[0] + "_" + tmp3[1];
                    if (tmp3.length == 3) {
                        arch = tmp3[2];
                    } else {
                        arch = tmp3[2] + "_" + tmp3[3];
                    }
                } else {
                    linux = tmp1[0];
                    arch = tmp1[1];
                }
                const tmp2 = tmp0[0].split("-", 3);
                const python = tmp2[1] + "-" + tmp2[2];
                assets.push({
                    name: asset.name,
                    url: asset.browser_download_url,
                    python: python,
                    linux: linux,
                    arch: arch
                });

                if (full_version === undefined) {
                    const index = asset.name.indexOf("-");
                    full_version = asset.name.slice(6, index);
                }
            }
        }

        releases.push({
            version: datum.name.slice(7),
            full_version: full_version,
            assets: assets,
            url: datum.html_url
        });
    }

    /* Sort releases */
    releases.sort(function(a, b) {
        const tmpa = a.version.split(".")
        const tmpb = b.version.split(".")
        a0 = Number(tmpa[0])
        a1 = Number(tmpa[1])
        b0 = Number(tmpb[0])
        b1 = Number(tmpb[1])

        if (a0 != b0) {
            return a0 - b0;
        } else {
            return a1 - b1;
        }
    });

    /* Generate the releases list */
    {
        const elements = []
        for (const release of releases) {
            elements.push(`<a href="${release.url}">${release.version}</a>`)
        }
        $("#append-releases-list").html(
            " The available Python versions are " +
            elements.slice(0, -1).join(", ") +
            " and " +
            elements[elements.length - 1] +
            "."
        );
    }

    /* Detect the host architecture */
    var host_arch = undefined;
    {
        var re = /Linux +(?<arch>[a-z0-9_]+)/g;
        const result = re.exec(navigator.userAgent);
        if (result) {
            host_arch = result.groups.arch;
            if (host_arch == "x64") {
                host_arch = "x86_64";
            }
        }
    }

    /* Strip blocks of whitespaces, e.g. at line start */
    function stripws (s) { return s.replace(/  +/g, ""); }

    /* Utility function for setting an inline code */
    function set_inline (selector, code) {
        $(selector).children().html(stripws(code));
    }

    /* Utility function for setting a code snippet */
    function set_snippet (selector, code) {
        $(selector).children().children().html(stripws(code));
    }

    /* Generate the examples */
    var suggested_appimage = undefined;
    {
        const release = releases[releases.length - 1];
        const arch = (host_arch === undefined) ? "x86_64" : host_arch;
        var asset = undefined;
        for (const a of release.assets) {
            if (a.arch == arch) {
                if (asset == undefined) {
                    asset = a;
                } else if (Number(a.linux) > Number(asset.linux)) {
                    asset = a;
                }
            }
        }
        suggested_appimage = asset;

        const pattern  = "download";
        const i = asset.url.indexOf(pattern) + pattern.length;
        const url0 = asset.url.slice(0, i);
        const url1 = asset.url.slice(i + 1);
        set_snippet("#basic-installation-example", `\
            wget ${url0}\\
            /${url1}

            chmod +x ${asset.name}</code></pre>
        `);

        $("#example-full-version").text(release.full_version);
        $("#example-python-tag").text(asset.python);
        $("#example-linux-tag").text("manylinux" + asset.linux);
        $("#example-arch-tag").text(asset.arch);

        set_snippet("#basic-installation-example-symlink", `\
            ln -s ${asset.name} python${release.version}
        `);

        set_inline("#basic-installation-example-execution",
            `./python${release.version}`
        );

        set_snippet("#site-packages-example", `\
            ./python${release.version} -m pip install numpy
        `);

        set_snippet("#site-packages-example-target", `\
            ./python${release.version} -m pip install --target=$(pwd)/packages numpy
        `);

        set_inline("#user-isolation-example",
            `./python${release.version} -s`
        );

        set_snippet("#venv-example", `\
            ./python${release.version} -m venv /path/to/new/virtual/environment
        `);

        const appdir = asset.name.slice(0, -8) + "AppDir";

        set_snippet("#advanced-installation-example", `\
            ./${asset.name} --appimage-extract

            mv squashfs-root ${appdir}

            ln -s ${appdir}/AppRun python${release.version}
        `);

        set_snippet("#repackaging-example", `\
            wget https://github.com/AppImage/AppImageKit/releases/download/continuous/\\
            appimagetool-x86_64.AppImage

            chmod +x appimagetool-x86_64.AppImage

            ./appimagetool-x86_64.AppImage \\
                ${appdir} \\
                ${asset.name}
        `);
    }


    function badge (asset, pad) {
        const colors = {
            aarch64: "d8dee9",
            i686: "81a1c1",
            x86_64: "5e81ac"
        };
        const python = asset.python.split("-")[1];
        const arch = asset.arch.replace("_", "__");
        var color = colors[asset.arch];
        if (color === undefined) {
            color = "red";
        }

        const img = `<img src="https://img.shields.io/badge/${python}-${arch}-${color}" alt="${asset.arch}">`

        if (pad) {
            return `<a href=${asset.url}>${img}</a>`;
        } else {
            return `<a href=${asset.url}><span class="smaller-appimage-badge">${img}</span></a>`;
        }
    }

    /* Generate the download links summary */
    {
        /* Find all Linux tags */
        function unique (arr) {
            var u = {}, a = [];
            for(var i = 0, l = arr.length; i < l; ++i){
                if(!u.hasOwnProperty(arr[i])) {
                    a.push(arr[i]);
                    u[arr[i]] = 1;
                }
            }
            return a;
        }

        const all_linuses = [];
        for (const release of releases) {
            for (const asset of release.assets) {
                all_linuses.push(asset.linux);
            }
        }
        const linuses = unique(all_linuses);

        /* Build the table header */
        const html = [];
        html.push("<table class=\"appimages-summary-table\"><thead><tr><th></th>");
        for (const linux of linuses) {
            html.push(`<th>Manylinux ${linux}</th>`);
        }
        html.push("</tr></thead>");

        /* Build the table rows */
        html.push("<tbody>");
        for (const release of releases) {
            html.push(`<tr><td>Python ${release.version}</td>`)
            for (linux of linuses) {
                const candidates = [];
                for (asset of release.assets) {
                    if (asset.linux == linux) {
                        candidates.push(badge(asset, true));
                    }
                }
                if (candidates.length > 0) {
                        html.push(
                            "<td><table class=\"appimages-summary-table-inner\"><tbody><tr><td>" +
                            candidates.join("</td></tr><tr><td>")  +
                            "</td></tr></tbody></table></td>"
                        );
                } else {
                        html.push("<td>&empty;</td>");
                }
            }
            html.push(`</tr>`)
        }
        html.push("</tbody>");
        html.push("<caption>Summary of available Python AppImages.</caption>");
        html.push("</table>");

        const element = $("#appimages-download-links");
        element.html(html.join("\n"));
    }

    /* Suggest an AppImage */
    if (host_arch != undefined) {
        const main = $("#suggest-appimage-download").children().first();
        main.attr("class", "admonition tip");
        const children = main.children();
        children.first().text("Tip");
        children.eq(1).html(stripws(`\
            According to your browser, your system is an ${host_arch} Linux.
            Therefore, we recommend that you download an ${host_arch} AppImage
            with Manylinux ${suggested_appimage.linux} compatibility. For
            example, ${badge(suggested_appimage, false)}.
        `));
    }

    /* Perform the syntaxic highlighting */
    hljs.highlightAll();
});

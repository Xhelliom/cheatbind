{
  description = "Wayland keyboard shortcuts overlay";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;
      in {
        packages.default = python.pkgs.buildPythonApplication {
          pname = "cheatbind";
          version = "0.1.2";
          src = ./.;
          format = "pyproject";

          nativeBuildInputs = with python.pkgs; [
            setuptools
            wheel
          ];

          buildInputs = [
            pkgs.gtk4
            pkgs.gtk4-layer-shell
            pkgs.gobject-introspection
          ];

          propagatedBuildInputs = with python.pkgs; [
            pygobject3
          ];

          nativeCheckInputs = with python.pkgs; [
            pytest
          ];

          checkPhase = ''
            pytest tests/
          '';

          preFixup = ''
            gappsWrapperArgs+=(
              --prefix GI_TYPELIB_PATH : "${pkgs.lib.makeSearchPath "lib/girepository-1.0" [
                pkgs.gtk4
                pkgs.gtk4-layer-shell
              ]}"
              --set GSK_RENDERER cairo
            )
          '';

          meta = with pkgs.lib; {
            description = "Wayland keyboard shortcuts overlay — parses compositor config and displays a styled cheatsheet";
            homepage = "https://github.com/Xhelliom/cheatbind";
            license = licenses.mit;
            platforms = platforms.linux;
            maintainers = [];
          };
        };

        devShells.default = pkgs.mkShell {
          packages = [
            (python.withPackages (ps: [
              ps.pygobject3
              ps.pytest
            ]))
            pkgs.gtk4
            pkgs.gtk4-layer-shell
            pkgs.gobject-introspection
          ];
        };
      }
    );
}

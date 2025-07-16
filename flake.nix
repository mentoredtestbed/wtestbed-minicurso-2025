{
  description = "Python environment with PyYAML for Ansible inventory management";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonWithPackages = pkgs.python3.withPackages (ps: with ps; [
          pyyaml
          pandas
          numpy
          scikit-learn
          tqdm
          matplotlib
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonWithPackages
            git
          ];

          shellHook = ''
            echo "Python development environment ready!"
            echo "Use 'python' to run your scripts."
          '';
        };

        packages.default = pythonWithPackages;
      }
    );
}
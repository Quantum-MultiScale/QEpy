#!/usr/bin/env bash
# Local terminal: source tools/wheels/arch_env.sh
# CI Environment: Automatically sourced by GitHub Actions

OS_NAME=$(uname -s)
# Allow CI to pass TARGET_ARCH, otherwise use local architecture
export TARGET_ARCH=${TARGET_ARCH:-$(uname -m)}

export LIBMBD_C_API=0

if [[ "$OS_NAME" == "Linux" ]]; then
    export FFLAGS="-fPIC -fallow-argument-mismatch"
    
elif [[ "$OS_NAME" == "Darwin" ]]; then
    export FFLAGS="-fPIC -fallow-argument-mismatch -ff2c -fno-second-underscore"
    export CPP="gcc -E"
    export LDFLAGS="-headerpad_max_install_names"
    
    if [[ "${TARGET_ARCH}" == "arm64" ]]; then
        export CFLAGS="-fPIC -arch arm64"
        export QE_INSTALL_FLAGS="--host=host"
        export build_alias="arm-apple-darwin20.0.0"
        export host_alias="x86_64-unknown-linux-gnu"
    fi
fi

echo "=== QEpy environment loaded (OS: $OS_NAME, Arch: $TARGET_ARCH) ==="

if [[ "$GITHUB_ACTIONS" == "true" ]]; then
    echo "Detecting GitHub Actions... Setting up CIBW environments."

    if [[ "$OS_NAME" == "Darwin" ]]; then
        # scipy action -->
          if [[ "${BLAS_VARIANT}" == "accelerate" ]]; then
            echo CIBW_CONFIG_SETTINGS=\"setup-args=-Dblas=accelerate\" >> "$GITHUB_ENV"

            # Builds with Accelerate only target macOS>=14.0
            CIBW_ENV="CIBW_ENVIRONMENT_MACOS=MACOSX_DEPLOYMENT_TARGET=14.0 INSTALL_OPENBLAS=false"

            if [[ "${TARGET_ARCH}" == "arm64" ]]; then
              # use preinstalled gfortran for Accelerate builds
              ln -s $(which gfortran-13) gfortran
              export PATH=$PWD:$PATH
              echo "PATH=$PATH" >> "$GITHUB_ENV"
              CIBW_ENV+=" INSTALL_GFORTRAN=false"
            else
              # x64_64. Can't use preinstalled fortran because it targets macOS15
              # Setting INSTALL_GFORTRAN=true causes the cibw_before_build script to install gfortran
              CIBW_ENV+=" INSTALL_GFORTRAN=true"
              CIBW_ENV+=" SDKROOT=$(xcrun --sdk macosx --show-sdk-path)"
            fi
          else
            CIBW_ENV="CIBW_ENVIRONMENT_MACOS=PKG_CONFIG_PATH=$PWD/.openblas \
              MACOSX_DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET}" \
              SDKROOT=$(xcrun --sdk macosx --show-sdk-path) \
              INSTALL_GFORTRAN=true"
          fi
        # scipy action <--
        CIBW_ENV+=" tddft=${tddft}"
        CIBW_ENV+=" LIBMBD_C_API=${LIBMBD_C_API}"
        CIBW_ENV+=" FFLAGS='${FFLAGS}'"
        CIBW_ENV+=" CPP='${CPP}'"
        CIBW_ENV+=" LDFLAGS='${LDFLAGS}'"
        
        if [[ "${TARGET_ARCH}" == "arm64" ]]; then
            CIBW_ENV+=" CFLAGS='${CFLAGS}'"
            CIBW_ENV+=" QE_INSTALL_FLAGS='${QE_INSTALL_FLAGS}'"
            CIBW_ENV+=" build_alias=${build_alias}"
            CIBW_ENV+=" host_alias=${host_alias}"
        fi
        echo "$CIBW_ENV" >> "$GITHUB_ENV"
        # Repair wheel logic using delocate
        PREFIX="DYLD_LIBRARY_PATH=\"\$(dirname \$(gfortran --print-file-name libgfortran.dylib))\""
        CIBW_REPAIR="$PREFIX delocate-wheel -v \$EXCLUDE --require-archs {delocate_archs} -w {dest_dir} {wheel}"
        echo "CIBW_REPAIR_WHEEL_COMMAND_MACOS=$CIBW_REPAIR" >> "$GITHUB_ENV"

    elif [[ "$OS_NAME" == "Linux" ]]; then
        CIBW_ENV="CIBW_ENVIRONMENT_LINUX="
        CIBW_ENV+=" INSTALL_OPENBLAS=false"
        CIBW_ENV+=" LIBMBD_C_API=${LIBMBD_C_API}"
        CIBW_ENV+=" tddft=${tddft}"
        CIBW_ENV+=" FFLAGS='${FFLAGS}'"
        echo "$CIBW_ENV" >> "$GITHUB_ENV"
    fi
fi

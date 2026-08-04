from collections import OrderedDict
import json
import numpy as np
import os
import re
import tempfile
import urllib.error
import urllib.request
import warnings
from pathlib import Path
from typing import Iterable, Sequence

from .core import env

KSPP_GITHUB_REPO = "Quantum-MultiScale/KSPP"
KSPP_GITHUB_BRANCH = "main"
KSPP_GITHUB_RAW = f"https://raw.githubusercontent.com/{KSPP_GITHUB_REPO}/{KSPP_GITHUB_BRANCH}"
KSPP_GITHUB_API = f"https://api.github.com/repos/{KSPP_GITHUB_REPO}/contents"
KSPP_DEFAULT_TABLE = "ultrasoft/gbrv-v1.5"
KSPP_DEFAULT_XC = "PBE"
KSPP_DEFAULT_ACCURACY = "standard"
KSPP_DEFAULT_FORMAT = "upf"

KSPP_CONFIG_KEYS = frozenset({
    "manual",
    "table",
    "xc",
    "accuracy",
    "fmt",
    "cache_dir",
    "search_paths",
    "offline",
    "update_ecuts",
})


def pop_kspp_config(kwargs: dict) -> dict:
    """Remove KSPP configuration keys from *kwargs* and return them."""
    config = {}
    for key in list(kwargs):
        if key not in KSPP_CONFIG_KEYS:
            continue
        value = kwargs.pop(key)
        if key in {"offline", "update_ecuts"}:
            if value:
                config[key] = True
        elif value is not None and value is not False:
            config[key] = value
    return config


class KSPPNotFoundError(FileNotFoundError):
    """Raised when no KSPP pseudopotential can be resolved for an element."""


def _kspp_default_cache_dir() -> Path:
    env_path = os.environ.get("QEPY_PP_CACHE")
    if env_path:
        return Path(env_path).expanduser()
    return Path.home() / ".cache" / "qepy" / "kspp"


def _kspp_normalize_symbol(symbol: str) -> str:
    sym = str(symbol).strip()
    if len(sym) == 1:
        return sym.upper()
    return sym[0].upper() + sym[1:].lower()


def _kspp_atomic_mass(symbol: str) -> float:
    try:
        from ase.data import atomic_masses, atomic_numbers

        return float(atomic_masses[atomic_numbers[symbol]])
    except Exception:
        return 1.0


def _kspp_fortran_path(path: Path | str) -> str:
    return f"'{Path(path).resolve()}/'"


def _kspp_unique_symbols(symbols: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for sym in symbols:
        key = _kspp_normalize_symbol(sym)
        if key not in seen:
            seen.add(key)
            unique.append(key)
    return unique


def _kspp_float_attr(text: str, name: str) -> float | None:
    match = re.search(rf'{name}="([^"]+)"', text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _kspp_str_attr(text: str, name: str) -> str | None:
    match = re.search(rf'{name}="([^"]+)"', text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def _kspp_bool_attr(text: str, name: str) -> bool:
    value = _kspp_str_attr(text, name)
    return value is not None and value.upper() in {"T", "TRUE", ".TRUE."}


def _read_upf_cutoffs(path: Path | str) -> dict[str, float]:
    """Read suggested ``ecutwfc`` / ``ecutrho`` (Ry) from a UPF file."""
    text = Path(path).read_text(errors="ignore")
    ecutwfc = _kspp_float_attr(text, "wfc_cutoff")
    ecutrho = _kspp_float_attr(text, "rho_cutoff")

    match = re.search(
        r"Suggested minimum cutoff for wavefunctions:\s*([\d.]+)",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        ecutwfc = float(match.group(1))
    match = re.search(
        r"Suggested minimum cutoff for charge density:\s*([\d.]+)",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        ecutrho = float(match.group(1))

    if ecutwfc is None and ecutrho is None:
        header = re.search(r"<PP_HEADER\b([^>]*)/?>", text, flags=re.IGNORECASE)
        if header is None:
            block = re.search(r"<PP_HEADER>(.*?)</PP_HEADER>", text, flags=re.DOTALL | re.IGNORECASE)
            if block:
                lines = [line.strip() for line in block.group(1).splitlines() if line.strip()]
                if len(lines) >= 8:
                    try:
                        ecutwfc = float(lines[7].split()[0])
                        ecutrho = float(lines[7].split()[1])
                    except (IndexError, ValueError):
                        pass

    pseudo_type = ""
    match = re.search(r'pseudo_type="([^"]+)"', text, flags=re.IGNORECASE)
    if match:
        pseudo_type = match.group(1).strip().upper()
    elif re.search(r"^\s*\S+\s+Ultrasoft", text, flags=re.MULTILINE | re.IGNORECASE):
        pseudo_type = "US"

    is_ultrasoft = _kspp_bool_attr(text, "is_ultrasoft")
    is_paw = _kspp_bool_attr(text, "is_paw")
    if pseudo_type == "US" or pseudo_type == "PAW":
        is_ultrasoft = True
    if pseudo_type == "PAW":
        is_paw = True

    if (ecutwfc is None or ecutwfc <= 0) and ecutrho and ecutrho > 0:
        if pseudo_type == "NC":
            # PseudoDojo ONCV UPFs store the wfc hint (Ha) in rho_cutoff.
            ecutwfc = 2.0 * ecutrho
            ecutrho = None

    dual = 8.0 if (is_ultrasoft or is_paw) else 4.0
    if ecutwfc and ecutwfc > 0 and (ecutrho is None or ecutrho <= 0):
        ecutrho = dual * ecutwfc

    cutoffs: dict[str, float] = {}
    if ecutwfc and ecutwfc > 0:
        cutoffs["ecutwfc"] = ecutwfc
    if ecutrho and ecutrho > 0:
        cutoffs["ecutrho"] = ecutrho
    return cutoffs


def _max_upf_cutoffs(paths: Iterable[Path | str]) -> dict[str, float]:
    merged: dict[str, float] = {}
    for path in paths:
        for key, value in _read_upf_cutoffs(path).items():
            merged[key] = max(merged.get(key, 0.0), value)
    return merged


def _sync_ecuts_from_upf(
    qe_options: dict,
    upf_paths: Iterable[Path | str],
    *,
    update_ecuts: bool = False,
) -> dict[str, float]:
    """Warn or update QE cutoffs using UPF suggestions."""
    suggested = _max_upf_cutoffs(upf_paths)
    if not suggested:
        return suggested

    system = qe_options.setdefault("&system", {})
    for key in ("ecutwfc", "ecutrho"):
        if key not in suggested:
            continue
        current = system.get(key)
        try:
            current_val = float(current) if current is not None else None
        except (TypeError, ValueError):
            current_val = None

        if current_val is None:
            if update_ecuts:
                system[key] = suggested[key]
            continue

        if current_val + 1e-8 < suggested[key]:
            warnings.warn(
                f"KSPP: user {key}={current_val} Ry is below the pseudopotential "
                f"suggestion ({suggested[key]} Ry).",
                stacklevel=3,
            )
            if update_ecuts:
                system[key] = suggested[key]
    return suggested


class QEInput(object):
    """Input for QE

    Read/write the QE input file. The input `qe_options` or the output after reading an 
    input is a dictionary. There are two main types of QE input parameters : namelist and card.
    In `qe_options` namelist keys always start with '&',  and the value is a dictionary.
    Cards keys are the first line of the card, and the value is a list of strings.

    *e.g.* ::

        qe_options = {
            '&control' : {
                'calculation' : "'scf'",
                'nstep' : 50,
                },
            'k_points automatic' : ['1 1 1 0 0 0'],
            }

    .. note ::

        Nota bene: when the value of a namelist is a string (character), it needs to be enclosed 
        by quotation marks in addition to the usual string apostophies.


    Parameters
    ----------
    filename : str
        Name of QE input file
    qe_options: dict
        A dictionary with input parameters for QE to generate QE input file.
    """

    def __init__(self, filename = None, qe_options = None, atoms = None, ksppresolver = False, prog = 'pw', **kwargs):
        self.filename = filename
        self.atoms = atoms
        self.prog = prog
        self._kspp_config = {
            'manual': None,
            'table': None,
            'xc': None,
            'accuracy': None,
            'fmt': None,
            'cache_dir': None,
            'search_paths': None,
            'offline': False,
            'update_ecuts': False,
        }
        kspp_init = {}
        for key in tuple(self._kspp_config):
            if key in kwargs:
                kspp_init[key] = kwargs.pop(key)
        if isinstance(ksppresolver, QEInput.KSPPResolver):
            self._kspp_resolver = ksppresolver
            self._kspp_enabled = True
        else:
            self._kspp_resolver = None
            self._kspp_enabled = bool(ksppresolver)

        if qe_options is None:
            qe_options = {}

        if self.filename is not None :
            self.qe_options = self.read_qe_input(self.filename, **kwargs)
            self.qe_options = self.update_options(options=qe_options, qe_options = self.qe_options)
        else :
            self.qe_options = qe_options

        if self._kspp_enabled:
            if kspp_init:
                self.ksppresolver(apply=False, **kspp_init)
            if self.atoms is not None:
                self.ksppresolver(apply=True)

    @property
    def kspp_enabled(self) -> bool:
        return self._kspp_enabled

    def _get_kspp_resolver(self) -> "QEInput.KSPPResolver":
        if self._kspp_resolver is None:
            cfg = {
                key: value
                for key, value in self._kspp_config.items()
                if value is not None and key not in {'manual', 'update_ecuts'}
            }
            if self._kspp_config.get('offline'):
                cfg['offline'] = True
            self._kspp_resolver = self.KSPPResolver(**cfg)
        return self._kspp_resolver

    def ksppresolver(
        self,
        *,
        symbols: Sequence[str] | None = None,
        apply: bool = True,
        resolver: "QEInput.KSPPResolver | None" = None,
        manual: dict[str, str] | None = None,
        table: str | None = None,
        xc: str | None = None,
        accuracy: str | None = None,
        fmt: str | None = None,
        cache_dir: Path | str | None = None,
        search_paths: Sequence[Path | str] | None = None,
        offline: bool | None = None,
        update_ecuts: bool | None = None,
    ) -> "QEInput":
        """Configure KSPP resolution and optionally fill ``qe_options``.

        Minimal::

            pwin = QEInput(qe_options=qe_options, atoms=atoms, ksppresolver=True)
            pw_driver = Driver(pwin)

        Advanced::

            pwin = QEInput(qe_options=qe_options, atoms=atoms, ksppresolver=True)
            pwin.ksppresolver(xc='LDA', offline=True, search_paths=[kspp_root])
        """
        config_changed = False
        for key, value in (
            ('manual', manual),
            ('table', table),
            ('xc', xc),
            ('accuracy', accuracy),
            ('fmt', fmt),
            ('cache_dir', cache_dir),
            ('search_paths', search_paths),
        ):
            if value is not None:
                self._kspp_config[key] = value
                config_changed = True
        if offline is not None:
            self._kspp_config['offline'] = offline
            config_changed = True
        if update_ecuts is not None:
            self._kspp_config['update_ecuts'] = update_ecuts
            config_changed = True

        self._kspp_enabled = True
        if resolver is not None:
            self._kspp_resolver = resolver
        elif config_changed:
            self._kspp_resolver = None

        if apply:
            species = symbols
            if species is None and self.atoms is not None:
                species = self.atoms.get_chemical_symbols()
            if species:
                self.apply_kspp(
                    self.qe_options,
                    species,
                    resolver=self._get_kspp_resolver(),
                    manual=self._kspp_config.get('manual'),
                    update_ecuts=self._kspp_config.get('update_ecuts', False),
                )
        return self

    class KSPPResolver:
        """Locate or download UPF files from the KSPP repository."""

        def __init__(
            self,
            table: str = KSPP_DEFAULT_TABLE,
            xc: str = KSPP_DEFAULT_XC,
            accuracy: str = KSPP_DEFAULT_ACCURACY,
            fmt: str = KSPP_DEFAULT_FORMAT,
            cache_dir: Path | str | None = None,
            search_paths: Sequence[Path | str] | None = None,
            offline: bool = False,
        ):
            self.table = table.strip("/")
            self.xc = xc.upper()
            self.accuracy = accuracy
            self.format = fmt
            self.cache_dir = Path(cache_dir or _kspp_default_cache_dir())
            self.search_paths = [Path(p) for p in (search_paths or [])]
            self.offline = offline
            self._listings: dict[str, frozenset[str]] = {}

        @property
        def listing_reldir(self) -> str:
            return f"{self.table}/{self.xc}/{self.accuracy}/{self.format}"

        @property
        def pseudo_dir(self) -> Path:
            return self.cache_dir / self.listing_reldir

        def resolve(self, symbol: str) -> Path:
            symbol = _kspp_normalize_symbol(symbol)
            local = self._find_local(symbol)
            if local is not None:
                return local

            filename = self._pick_filename(symbol)
            dest = self.pseudo_dir / filename
            if dest.is_file():
                return dest

            if self.offline:
                raise KSPPNotFoundError(
                    f"Pseudopotential for {symbol} not cached and offline mode is enabled "
                    f"({self.listing_reldir})"
                )

            self._download(filename, dest)
            return dest

        def resolve_for_symbols(self, symbols: Iterable[str]) -> dict[str, Path]:
            return {_kspp_normalize_symbol(sym): self.resolve(sym) for sym in symbols}

        def atomic_species_lines(
            self,
            symbols: Iterable[str],
            manual: dict[str, str] | None = None,
        ) -> list[str]:
            manual = manual or {}
            lines = []
            for symbol in symbols:
                key = _kspp_normalize_symbol(symbol)
                if key in manual:
                    filename = Path(manual[key]).name
                    if not (self.pseudo_dir / filename).is_file():
                        src = Path(manual[key])
                        if src.is_file():
                            dest = self.pseudo_dir / filename
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            if not dest.is_file():
                                dest.write_bytes(src.read_bytes())
                else:
                    filename = self.resolve(key).name
                mass = _kspp_atomic_mass(key)
                lines.append(f"{key:2s} {mass:12.6f} {filename}")
            return lines

        def _find_local(self, symbol: str) -> Path | None:
            filename = self._pick_filename(symbol, allow_remote=False)
            if filename is None:
                return None
            for base in self._candidate_bases():
                path = base / filename
                if path.is_file():
                    return path
            return None

        def _candidate_bases(self) -> Iterable[Path]:
            for base in self.search_paths:
                yield base / self.listing_reldir
            yield self.pseudo_dir

        def _pick_filename(self, symbol: str, allow_remote: bool = True) -> str | None:
            symbol = _kspp_normalize_symbol(symbol)
            files = self._list_files() if allow_remote else self._list_local_files()
            if not files:
                if allow_remote:
                    raise KSPPNotFoundError(
                        f"No files listed for {self.listing_reldir}"
                    )
                return None

            exact = (
                f"{symbol}.upf",
                f"{symbol}.UPF",
                f"{symbol.lower()}.upf",
                f"{symbol.lower()}.UPF",
            )
            for name in exact:
                if name in files:
                    return name

            prefix = f"{symbol.lower()}_"
            matches = sorted(name for name in files if name.lower().startswith(prefix))
            if matches:
                return matches[0]

            if allow_remote:
                raise KSPPNotFoundError(
                    f"No pseudopotential for {symbol} in {self.listing_reldir}"
                )
            return None

        def _list_local_files(self) -> frozenset[str]:
            names = set()
            for base in (*self.search_paths, self.pseudo_dir):
                for sub in (base / self.listing_reldir, base):
                    if sub.is_dir():
                        names.update(p.name for p in sub.iterdir() if p.is_file())
            return frozenset(names)

        def _list_files(self) -> frozenset[str]:
            if self.listing_reldir in self._listings:
                return self._listings[self.listing_reldir]

            local = self._list_local_files()
            if local and self.offline:
                self._listings[self.listing_reldir] = local
                return local

            url = f"{KSPP_GITHUB_API}/{self.listing_reldir}?ref={KSPP_GITHUB_BRANCH}"
            request = urllib.request.Request(
                url,
                headers={"Accept": "application/vnd.github+json", "User-Agent": "qepy"},
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    payload = json.load(response)
            except urllib.error.HTTPError:
                names = local
            else:
                remote = frozenset(
                    item["name"] for item in payload if item.get("type") == "file"
                )
                names = remote or local
            self._listings[self.listing_reldir] = names
            return names

        def _download(self, filename: str, dest: Path) -> None:
            dest.parent.mkdir(parents=True, exist_ok=True)
            url = f"{KSPP_GITHUB_RAW}/{self.listing_reldir}/{filename}"
            tmp = dest.with_suffix(dest.suffix + ".part")
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "qepy"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    tmp.write_bytes(response.read())
                tmp.replace(dest)
            except Exception:
                if tmp.exists():
                    tmp.unlink()
                raise

    @classmethod
    def apply_kspp(
        cls,
        qe_options: dict,
        symbols: Sequence[str],
        *,
        resolver: "QEInput.KSPPResolver | None" = None,
        manual: dict[str, str] | None = None,
        table: str | None = None,
        xc: str | None = None,
        accuracy: str | None = None,
        fmt: str | None = None,
        cache_dir: Path | str | None = None,
        search_paths: Sequence[Path | str] | None = None,
        offline: bool = False,
        update_ecuts: bool = False,
    ) -> dict:
        """Fill ``pseudo_dir`` and ``atomic_species`` in ``qe_options`` from KSPP."""
        if resolver is None:
            kwargs = {"offline": offline, "search_paths": search_paths}
            if table is not None:
                kwargs["table"] = table
            if xc is not None:
                kwargs["xc"] = xc
            if accuracy is not None:
                kwargs["accuracy"] = accuracy
            if fmt is not None:
                kwargs["fmt"] = fmt
            if cache_dir is not None:
                kwargs["cache_dir"] = cache_dir
            resolver = cls.KSPPResolver(**kwargs)

        manual = manual or {}
        species = _kspp_unique_symbols(symbols)
        qe_options.setdefault("&control", {})
        qe_options["&control"]["pseudo_dir"] = _kspp_fortran_path(resolver.pseudo_dir)
        qe_options["atomic_species"] = resolver.atomic_species_lines(species, manual=manual)
        if "&system" in qe_options:
            qe_options["&system"]["ntyp"] = len(qe_options["atomic_species"])

        upf_paths = []
        for symbol in species:
            key = _kspp_normalize_symbol(symbol)
            if key in manual:
                upf_paths.append(Path(manual[key]))
            else:
                upf_paths.append(resolver.resolve(key))
        _sync_ecuts_from_upf(qe_options, upf_paths, update_ecuts=update_ecuts)
        return qe_options

    def write_qe_input(self, filename, atoms = None, basefile = None, qe_options = {}, prog = 'pw', **kwargs):
        """Write the QE input file

        Parameters
        ----------
        filename : str
            The file name of output file
        atoms : ase.Atoms
            structure information with ase.Atoms
        basefile : str
            If set, will base on this file only update atomic information
        qe_options : dict
            Input parameters of QE
        """
        if basefile :
            options = qe_options
            qe_options = self.read_qe_input(basefile)
            qe_options = self.update_options(options=options, qe_options = qe_options, prog = prog)
        #
        atoms = atoms or self.atoms
        if not qe_options:
            qe_options = self.qe_options
        if prog == 'pw' and atoms is not None:
            if self._kspp_enabled:
                self.ksppresolver(symbols=atoms.get_chemical_symbols(), apply=True)
        if prog == 'pw' :
            if atoms is not None :
                qe_options = self.update_atoms(atoms, qe_options, prog=prog, **kwargs)
        if hasattr(filename, 'write'):
            fh = filename
        else :
            fh = open(filename, 'w')
        #
        if prog in ['list', 'lambda']:
            self.write_list(fh, qe_options=qe_options, **kwargs)
            return
        #
        options = QEOPTIONS.get(prog, {}).copy()
        options.update(qe_options)
        #
        for key, value in options.items() :
            if key.startswith('&'):
                fh.write(key.upper() + '\n')
                for k, v in value.items() :
                    if isinstance(v, str):
                        if v.startswith('"') or v.startswith("'"):
                            pass
                        else:
                            v = "'" + v + "'"
                    elif isinstance(v, bool):
                        if v :
                            v = '.true.'
                        else:
                            v = '.false.'
                    fh.write('   ' + k + ' = ' + str(v) + '\n')
                fh.write('/\n\n')
            else :
                l = key.split()
                l[0] = l[0].upper()
                key = ' '.join(l)
                fh.write(key + '\n')
                for v in value :
                    if isinstance(v, (list, tuple, set)):
                        v = ' '.join(map(str, v))
                    fh.write(str(v) + '\n')
                fh.write('\n')

        if not hasattr(filename, 'write'): fh.close()

    @staticmethod
    def write_list(filename, qe_options=[], **kwargs):
        if hasattr(filename, 'write'):
            fh = filename
        else :
            fh = open(filename, 'w')
        for v in qe_options:
            if isinstance(v, (list, tuple, set)):
                v = ' '.join(map(str, v))
            fh.write(str(v) + '\n')

        if not hasattr(filename, 'write'): fh.close()

    @classmethod
    def update_atoms(cls, atoms, qe_options, prog = 'pw', **kwargs):
        """update atomic information

        Parameters
        ----------
        atoms : ase.Atoms
            ase.Atoms has all atomic information in ASE units
        qe_options : dict
            Input parameters of QE
        """
        #
        if prog != 'pw' : return qe_options
        #
        if '&system' not in qe_options :
            qe_options['&system'] = {}
        qe_options['&system']['ibrav'] = 0
        qe_options['&system']['nat'] = len(atoms)
        ntyp = len(set(atoms.symbols))
        ntyp_old = len(qe_options.get('atomic_species', []))
        if ntyp > ntyp_old :
            raise ValueError("The number of 'ATOMIC_SPECIES' not fit the number of types of atoms.")
        qe_options['&system']['ntyp'] = ntyp_old
        # keys = [k.split()[0] for k in qe_options]
        keys = list(qe_options.keys())
        for key in keys :
            if key.startswith(('cell_parameters', 'atomic_positions')) :
                qe_options.pop(key, None)
        #
        key = 'cell_parameters angstrom'
        qe_options[key] = []
        for i in range(3):
            line = '{0[0]:.14f} {0[1]:.14f} {0[2]:.14f}'.format(atoms.cell[i])
            qe_options[key].append(line)
        #
        key = 'atomic_positions angstrom'
        qe_options[key] = []
        for s, p in zip(atoms.symbols, atoms.positions):
            line = '{0:4s} {1[0]:.14f} {1[1]:.14f} {1[2]:.14f}'.format(s, p)
            qe_options[key].append(line)
        #
        return qe_options

    @classmethod
    def update_options(cls, options = {}, qe_options = {}, **kwargs):
        """update options

        Use *options* to update *qe_options*

        Parameters
        ----------
        options : dict
            New options
        qe_options : dict
            QE options
        """

        options = options or {}
        qe_options = qe_options or {}
        keys = list(qe_options.keys())

        for k, v in options.items():
            k = k.lower()
            if k.startswith('&'):
                if k in qe_options :
                    qe_options[k].update(v)
                else :
                    qe_options[k] = v.copy()
            else :
                kc = k.split()[0]
                for item in keys :
                    if kc in item :
                        qe_options.pop(item)
                        break
                qe_options[k] = v
        # correct the qe_options
        for k, v in options.items():
            if 'cell_parameters' in k:
                qe_options['&system']['ibrav'] = 0
            elif 'atomic_positions' in k:
                qe_options['&system']['nat'] = len(v)
                ntyp = len(set([x.split()[0] for x in v]))
                ntyp_old = len(qe_options.get('atomic_species', []))
                if ntyp > ntyp_old :
                    raise ValueError("The number of 'ATOMIC_SPECIES' not fit the number of types of atoms.")
                qe_options['&system']['ntyp'] = ntyp_old
        return qe_options

    def read_qe_input(self, filename, **kwargs):
        """read the QE input file

        Parameters
        ----------
        filename : str
            file name of QE input file
        """
        options = {}
        with open(filename, 'r') as fr :
            fh = self.iter_lines(fr, sep='!', **kwargs)
            for line in fh :
                if line.startswith('&'):
                    options[line.split()[0].lower()] = self.read_namelist(fh, **kwargs)
                else :
                    fh.send(line)
                    break
            for line in fh :
                l = line.split()
                l[0] = l[0].lower()
                key = ' '.join(l)
                options[key] = self.read_card(fh, **kwargs)
        return options

    def read_namelist(self, fh, **kwargs):
        """read the namelist

        Parameters
        ----------
        fh : iter
            modified file handler
        """
        options = {}
        for line in fh :
            if line == '/' :
                break
            else :
                k, v = line.split('=')
                v = v.strip(',').strip()
                options[k.strip()] = self.string2value(v)
        else :
            raise ValueError("The namelist not closed with '/'.")
        return options

    @staticmethod
    def string2value(string):
        if string.startswith('"') or string.startswith("'"): # character
            v = string
        elif string[0] == '.': # logical
            s = string[1].lower()
            if s == 'f':
                v = False
            elif s == 't':
                v = True
            else:
                v = string
        else:
            try:
                v = int(string) # integer
            except Exception:
                try:
                    v = string.upper().replace('D','E')
                    v = float(v)
                except Exception:
                    v = string
        return v

    def read_card(self, fh, **kwargs):
        """read the card

        The comments lines which start with '#' will be kept. Here assuming if all the characters of first word
        are alphabet letters and length is greater than 6, this line will be next card.

        Parameters
        ----------
        fh : iter
            modified file handler
        """
        l = []
        for line in fh :
            a = line.split()[0].replace('_', '')
            if a.isalpha() and len(a) > 6 : # assuming only card name has more than 6 characters
                fh.send(line)
                break
            else :
                l.append(line)
        return l

    def iter_lines(self, fh, sep='!', **kwargs):
        """return the non-comment part of non-empty line

        `sep` is the comment characters. The comment line or empty line will be skip.
        If the line is mixed, only the front non-comment part will return.

        Parameters
        ----------
        fh : object
            file handler
        sep : str, list or tuple
            The delimiter string, multiple delimiters can given by a list
        """
        if isinstance(sep, (tuple, list)):
            seps = sep[1:]
            sep = sep[0]
        else :
            seps = []
        for line in fh:
            for s in seps :
                line = line.replace(s,sep)
            line = line.split(sep)[0].strip()
            if len(line) > 0 :
                line = yield line
                if line is not None :
                    yield line
                    yield line


# All QE namelist from 7.1
QEOPTIONS={
    "all_currents" : OrderedDict.fromkeys(
        ["&energy_current"], {}),
    "bands" : OrderedDict.fromkeys(
        ["&bands"], {}),
    "bgw2pw" : OrderedDict.fromkeys(
        ["&input_bgw2pw"], {}),
    "cp" : OrderedDict.fromkeys(
        ["&control", "&system", "&electrons", "&ions", "&cell", "&press_ai", "&wannier", "atomic_species"], {}),
    "cppp" : OrderedDict.fromkeys(
        ["&inputpp"], {}),
    "davidson" : OrderedDict.fromkeys(
        ["&lr_input", "&lr_dav"], {}),
    "dos" : OrderedDict.fromkeys(
        ["&dos"], {}),
    "dynmat" : OrderedDict.fromkeys(
        ["&input"], {}),
    "eels" : OrderedDict.fromkeys(
        ["&lr_input", "&lr_control"], {}),
    "hp" : OrderedDict.fromkeys(
        ["&inputhp"], {}),
    "importexport_binary" : OrderedDict.fromkeys(
        ["&inputpp"], {}),
    "kcw" : OrderedDict.fromkeys(
        ["&control", "&wannier", "&screen", "&ham"], {}),
    "lanczos" : OrderedDict.fromkeys(
        ["&lr_input", "&lr_control", "&lr_post"], {}),
    "ld1" : OrderedDict.fromkeys(
        ["&input", "&inputp", "&test"], {}),
    "magnons" : OrderedDict.fromkeys(
        ["&lr_input", "&lr_control"], {}),
    "matdyn" : OrderedDict.fromkeys(
        ["&input"], {}),
    "molecularpdos" : OrderedDict.fromkeys(
        ["&inputmopdos"], {}),
    "neb" : OrderedDict.fromkeys(
        ["&path"], {}),
    "ph" : OrderedDict.fromkeys(
        ["&inputph"], {}),
    "postahc" : OrderedDict.fromkeys(
        ["&input"], {}),
    "pp" : OrderedDict.fromkeys(
        ["&inputpp", "&plot"], {}),
    "projwfc" : OrderedDict.fromkeys(
        ["&projwfc"], {}),
    "pw" : OrderedDict.fromkeys(
        ["&control", "&system", "&electrons", "&ions", "&cell", "&fcp", "&rism", "atomic_species"], {}),
    "pw2bgw" : OrderedDict.fromkeys(
        ["&input_pw2bgw"], {}),
    "pwcond" : OrderedDict.fromkeys(
        ["&inputcond"], {}),
    "q2r" : OrderedDict.fromkeys(
        ["&input"], {}),
    "spectrum" : OrderedDict.fromkeys(
        ["&lr_input"], {}),
    "cetddft" : OrderedDict.fromkeys(
        ["&inputtddft"], {}),
    }


class QEOutput(object):
    """Parser of QE output. Usually not needed, but can be useful to access info from the QE output"""
    def __init__(self, fh = None, nat = None, **kwargs):
        self.fh = fh
        self.nat = nat
        self.kwargs = kwargs

    @classmethod
    def get_forces_all(cls, fh = None, nat = None, **kwargs):
        if fh is None and hasattr(cls, 'fh') : fh = cls.fh
        if fh is None : raise ValueError('Please give a output "fh"')
        if nat is None and hasattr(cls, 'nat') : nat = cls.nat
        if nat is None : raise ValueError('Please give number of atoms "nat"')
        if isinstance(fh, list) : fh = iter(fh)
        forces={}
        lstart = False
        for line in fh:
            if len(line.strip())<3: continue
            if 'Total force' in line: break
            if 'Forces acting' in line:
                lstart = True
                line=next(fh)
                key = 'total'
            elif lstart:
                l = list(line.split())
                key=l[1] if l[0]=='The' else l[0]
            if lstart:
                fs = []
                for i in range(nat):
                    line=next(fh)
                    f=list(map(float, line.split()[-3:]))
                    fs.append(f)
                forces[key.lower()] = np.asarray(fs)
        return forces

    @classmethod
    def get_stress_all(cls, fh = None, **kwargs):
        if fh is None and hasattr(cls, 'fh') : fh = cls.fh
        if fh is None : raise ValueError('Please give a output "fh"')
        if isinstance(fh, list) : fh = iter(fh)
        stress ={}
        lstart = False
        for line in fh:
            if len(line.strip())<3: continue
            if lstart and 'stress' not in line: break
            if 'total   stress' in line:
                lstart = True
                line=next(fh)
                key = 'total'
                l = list(line.split())
            elif lstart:
                l = list(line.split())
                key = l[0]
            if lstart:
                ss = []
                for i in range(3):
                    s=list(map(float, line.split()[-3:]))
                    ss.append(s)
                    line=next(fh)
                stress[key.lower()] = np.asarray(ss)
        return stress

    @classmethod
    def get_forces(cls, fh = None, nat = None, **kwargs):
        return cls.get_forces_all(fh=fh, nat=nat, **kwargs)['total']

    @classmethod
    def get_stress(cls, fh = None, **kwargs):
        return cls.get_stress_all(fh=fh, **kwargs)['total']


def set_logfile(logfile=None):
    """_initialize the QE output."""
    if hasattr(env['STDOUT'], 'close'): env['STDOUT'].close()
    if logfile in [None, False]:
        fileobj = None
    else :
        if logfile is True:
            fileobj = tempfile.NamedTemporaryFile('w+')
        elif hasattr(logfile, 'write'):
            fileobj = logfile
        else :
            fileobj = open(logfile, 'w+')
    env['LOGFILE'] = logfile
    env['STDOUT'] = fileobj
    return fileobj

def get_output():
    """Return the output of QE.

    It depends on the `logfile` of `set_logfile`.

      - None : return None.
      - str  : return all outputs.
      - True : It will return the output from last time.
    """
    fileobj = env['STDOUT']
    logfile = env['LOGFILE']
    if fileobj is not None :
        if logfile is True :
            fileobj.flush()
            fileobj.seek(0)
            lines = fileobj.readlines()
            fileobj.close()
            #
            set_logfile(logfile=True)
            #
            return lines
        else :
            fileobj.seek(0)
            return fileobj.readlines()
    else :
        return None

def set_input(inputfile=None):
    if hasattr(env['STDIN'], 'close'): env['STDIN'].close()
    if inputfile :
        if hasattr(inputfile, 'read'):
            fileobj = inputfile
        else :
            fileobj = open(inputfile, 'r')
        stdin = os.dup(0)
        os.dup2(fileobj.fileno(), 0)
        env['STDIN'] = fileobj
        env['STDIN_SAVE'] = stdin
    else:
        stdin = env['STDIN_SAVE']
        if stdin is not None :
            os.dup2(stdin, 0)
            os.close(stdin)

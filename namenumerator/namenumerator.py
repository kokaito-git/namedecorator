from typing import Any, Dict, Iterable, List, Optional, Tuple, Type, Union
# from kcolors.refs import * # pyright: ignore[]
from colors import * # no dinámicas pero así no tienes que instalar nada
import inspect
import re

#  TODO:
#  - Traducir las explicaciones


def _raise_contains_points(vname: str, varval: str, *, stack=1):
    """Lanza una excepción si name/ext contienen algun ."""
    if "." in varval:
        perr = _func_emsg(stack=stack + 1)
        raise ValueError(
            f"{perr} '{BGRAY}{vname}{END}' no puede contener puntos"
            f" '{BGRAY}.{END}'"
        )


def _raise_invalid_type(
    vname: str, varval: Any, requiredtypes: Tuple[Type, ...], *, stack=1
):
    """Lanza excepción si el tipo no se encuentra en la tupla"""
    if not isinstance(varval, requiredtypes):
        perr = _func_emsg(stack=stack + 1)
        rtypes_str = ", ".join([tp.__name__ for tp in requiredtypes])

        raise ValueError(
            f"{perr} el tipo de '{BGRAY}{vname}{END}' debe ser"
            f" '{BGRAY}{rtypes_str}{END}'."
        )


def _raise_invalid_elements(
    vname: str,
    varval: Iterable[Any],
    requiredtypes: Tuple[Type, ...],
    intensive: bool = False,
    *,
    stack=1,
):
    """Valida los tipos de los elementos en un iterable.
    Si `intensive=False`, solo valida el primer elemento."""

    # Si el iterable está vacío, no hacemos validación.
    iterator = iter(varval)
    try:
        if not intensive:
            first_element = next(iterator)
            _raise_invalid_type(
                f"{vname} (element: 0)",
                first_element,
                requiredtypes,
                stack=stack + 1,
            )
        else:
            for index, element in enumerate(iterator):
                _raise_invalid_type(
                    f"{vname} (element: {index})",
                    element,
                    requiredtypes,
                    stack=stack + 1,
                )
    except StopIteration:
        # Si el iterable está vacío, no hay nada que validar.
        pass


def _raise_contains_duplicates(
    vname: str,
    varval: Iterable[Any],
    *,
    stack=1,
):
    """Valida si un iterable contiene duplicados.
    Lanza una excepción si se encuentran duplicados.
    """
    seen = {}
    iterator = iter(varval)

    for index, element in enumerate(iterator):
        if element in seen:
            previous_index = seen[element]
            perr = _func_emsg(stack=stack + 1)
            msg = (
                f"{perr} el elemento '{BGRAY}{element}{END}' de {BGRAY}{vname}{END} "
                "está duplicado en las posiciones "
                f"'{BGRAY}{previous_index}{END}' y '{BGRAY}{index}{END}'."
            )
            raise ValueError(msg)
        seen[element] = index


def _raise_requires_one_char(vname: str, varval: str, *, stack=1):
    if not len(varval):
        perr = _func_emsg(stack=stack + 1)
        raise ValueError(
            f"{perr} '{BGRAY}{vname}{END}' debe tener al menos un carácter."
        )


def _raise_contains_digits(vname: str, varval: str, *, stack=1):
    """Lanza excepción si la string contiene digitos"""
    perr = _func_emsg(stack=stack + 1)
    if any(char.isdigit() for char in varval):
        raise ValueError(f"{perr} '{BGRAY}{vname}{END}' no debe contener dígitos.")


def _raise_min(vname: str, varval: int, min: int, *, stack=1):
    """Lanza excepción si no llegamos a un mínimo"""
    perr = _func_emsg(stack=stack + 1)
    if varval < min:
        raise ValueError(
            f"{perr} '{BGRAY}{vname}{END}' debe ser al menos '{min}'."
        )


def _raise_required_def(vname: str, varval: Any, defval: Any, *, stack=1):
    """Lanza excepción si no tiene ni valor ni un valor por defecto"""
    if varval is None and defval is None:
        perr = _func_emsg(stack=stack + 1)
        raise ValueError(
            f"{perr} se necesita un {BGRAY}{vname}{END} pero no se ha"
            f" proporcionado ni tiene un valor por defecto."
        )


def _func_emsg(*, stack: int = 1):
    """Función auxiliar que retorna una string con información de la función
    en la cual se va a producir un error."""

    caller_name = inspect.stack()[stack].function
    return f"{BRED}[!] Error en {caller_name}():{END}"


def _extract_name_ext(seqname: str) -> Optional[str]:
    """Extrae la extensión de un nombre, si es que la tiene"""
    pattern = r"^.*?[.](.*)$"

    match = re.match(pattern, seqname)
    if match:
        ext = match.group(1)
        return ext

    return None


class NameNumeratorException(Exception):
    def __init__(self, message: str = ""):
        super().__init__(message)

    def __str__(self):
        return super().__str__()


class NotPartOfSeq(NameNumeratorException):
    def __init__(self, seqname: str, message: str = "", *, stack=3):
        super().__init__(message)
        self.seqname = seqname
        self.stack = stack

    def __str__(self):
        # Llama al método _func_emsg desde la clase base
        return super().__str__()
        perr = _func_emsg(stack=self.stack)
        # return f"{self.args[0]}"


class NameNumerator:
    def __init__(
        self,
        separator: str = "_",
        enumerate_first: bool = False,
        from_zero: bool = False,
        min_numlen: int = 1,
        *,
        def_name: Optional[str] = None,
        def_ext: Optional[str] = None,
    ):
        """Establece las settings fijas que no se pueden cambiar:
        separator: un separador de mínimo un carácter para cuando haya que
          incluir la parte numérica.

        enumerate_first: indica si el primer nombre de la serie también
          debe de ser decorado (enumerado):
                (False) avatar2.png (True) avatar2_1.png

        from_zero: indica que el primer nombre decorado (ya sea le del indice 0
        o 1) debe empezar por 0.
            (False) avatar2_1.png (True) avatar2_0.png

        min_numlen: indica una longitud mínima de número, 0 y 1 no van a
          tener resultado porque la longitud mínima de un número siempre va a
          ser 1, así que debe usarse 2 en adelante para añadir ceros
            (0/1) avatar2_1.png, (2) avatar2_01.png, (3) avatar2_001.png

        Recomendación de settings: dejarlas tal cual están a menos que surjan
          necesidades especificas -> el primer nombre no será enumerado, el
          segundo si, empezará a partir de 1 y no agregará ceros adicionales.

        Valores por defecto opcionales:
            def_name: name por defecto, es requerido por casi todas las
              funciones. Si solo vas a trabajar con un nombre es buena idea
              establecerlo para no tener que indicarlo cada vez.

            def_ext: ext por defecto, ocurre lo mismo que con
             name, pero a diferencia de name ext no es obligatorio.
        """

        # Settings
        self._separator: str = self._get_separator(separator)
        self._enumerate_first: bool = self._get_enumerate_first(enumerate_first)
        self._from_zero: bool = self._get_from_zero(from_zero)
        self._min_numlen: int = self._get_min_numlen(min_numlen)

        # Optional def values
        self._def_name: Optional[str] = self._get_def_name(def_name)
        self._def_ext: Optional[str] = self._get_def_ext(def_ext)

    #  CAT: seqname
    def get_seqname(
        self,
        index: int,
        name: Optional[str] = None,
        ext: Optional[str] = None,
    ) -> str:
        """Obtiene el nombre que le correspondería al indice en la secuencia
        según las settings actuales."""

        # Validación de tipo y rango positivo
        self._validate_index(index)

        # Validación de tipo y valor por defecto
        name = self._get_name(name)
        ext = self._get_ext(ext)
        ext = "" if ext is None else f".{ext}"

        # Caso especial para el primer nombre que puede ir sin decoración
        if index == 0 and not self.enumerate_first:
            return f"{name}{ext}"

        # Sin importar el índice sacamos el número que le
        # corresponde
        if self.enumerate_first:
            number = index if self.from_zero else index + 1
        else:
            number = index - 1 if self.from_zero else index

        strnum = str(number).zfill(self.min_numlen)
        return f"{name}{self.separator}{strnum}{ext}"

    def seqname_to_index(
        self,
        seqname: str,
        *,
        name: Optional[str] = None,
        ext: Optional[str] = None,
    ) -> Optional[int]:
        """Si un nombre es parte de esta secuencia retorna su indice (desde 0 en
        adelante, y recuerda que este no tiene por qué corresponderse con la parte
        numérica del nombre), si no lo es retornara None."""
        # Validations and defaults
        _raise_invalid_type("seqname", seqname, (str,))
        name = self._get_name(name)
        ext = self._get_ext(ext)

        # Caso especial donde puede no haber numeración
        if seqname == self.get_seqname(0, name, ext):
            return 0

        # Extrae las partes, si cualquiera es None es porque no
        # se corresponde con un nombre de esta secuencia
        name_part, separator_part, number_part, suffix_part = (
            self.extract_seqname_parts(seqname)
        )
        if number_part is None:
            return None

        # Retorna el indice
        return self.number_to_index(number_part)

    def seqname_next(
        self,
        seqname: str,
        *,
        name: Optional[str] = None,
        ext: Optional[str] = None,
    ) -> Optional[int]:
        """Indica cual sería el seqname que le sigue a este nombre. Si el nombre
        indicado no forma parte de esta secuencia retornará None.

        return: retorna el indice, puedes obtener el nombre completo con
         get_seqname(indice, ...)
        """

        # Obtiene el indice, si no es parte de esta secuencia retornará None.
        # No solo obtiene el indice sino que reporta errores por nosotros
        seqname_index = self.seqname_to_index(seqname, name=name, ext=ext)
        if seqname_index is None:
            return None

        # Obtenemos indice siguiente
        next_index = seqname_index + 1

        return next_index

    def is_seqname(
        self,
        seqname: str,
        *,
        name: Optional[str] = None,
        ext: Optional[str] = None,
    ) -> bool:
        """Retorna true si el nombre forma parte de esta secuencia, sino false"""
        # Validations and defaults
        _raise_invalid_type("seqname", seqname, (str,))
        name = self._get_name(name)
        ext = self._get_ext(ext)

        # Caso especial donde puede no haber numeración
        if seqname == self.get_seqname(0, name, ext):
            return True
        name_part = self.extract_seqname_parts(seqname)

        return name_part is not None

    def extract_seqname_parts(
        self,
        seqname: str,
    ) -> Union[Tuple[str, str, str, str], Tuple[None, None, None, None]]:
        """Extrae las distintas partes de un nombre si es parte de esta secuencia,
        (name, separator, number, ext), si no lo es retornará false."""
        # Valida el tipo de name
        _raise_invalid_type("seqname", seqname, (str,))

        ext = _extract_name_ext(seqname)
        if ext is None:
            return None, None, None, None

        # Si el nombre tiene una ext la retira para poder aplicar el
        # regex al nombre sin la ext (-1 por el .)
        seqname = seqname[: -len(ext) + -1]

        # (1) cualquier n. de caracteres antes del separador
        # (2) el separador
        # (3) el numero
        # .. no hay más porque hemos recortado la ext antes
        pattern = rf"^(.*)({re.escape(self.separator)})(\d+)?$"
        match = re.search(pattern, seqname)
        if match:
            name = match.group(1)
            separator = match.group(2)
            number = match.group(3)
            assert (
                type(name) == str
                and type(separator) == str
                and type(number) == str
            ), "Las variables no son de tipo str"
            return name, separator, number, ext
        return None, None, None, None

    # CAT: Misc
    def number_to_index(self, number_part: str) -> int:
        """Obtiene el indice correspondiente a la parte numérica segun las
        settings de este objeto."""
        # Determina el indice a traves de number_part y los settings
        number = int(number_part)
        if self.enumerate_first:
            index = number if self.from_zero else number - 1
        else:
            index = number + 1 if self.from_zero else number
        return index

    def get_seqindexes(
        self,
        nlist: List[str],
        *,
        name: Optional[str] = None,
        ext: Optional[str] = None,
    ) -> List:
        """Retorna una lista ordenada de indices de los seqnames que aparecen en la
        lista. Esta función no reporta errores, ni por duplicados, ni por secuencias        rotas, por lo que también se suministran las funciones get_missing() y
        get_duplicates() que obtendrán esta información si la necesitas.
        """

        _raise_invalid_type("nlist", nlist, (list,))
        _raise_invalid_elements("nlist", nlist, (str,))

        seqindexes = []
        for anyname in nlist:
            index = self.seqname_to_index(anyname, name=name, ext=ext)
            if index is not None:
                seqindexes.append(index)
        return sorted(seqindexes)

    @staticmethod
    def get_missings(
        seqindexes: List[int],
    ) -> List[int]:
        """Si la lista (normalmente obtenida con get_seqindexes) tiene una secuencia
        rota retornará los indices que deberían estar y no están.

        [+] Si también quieres saber que elementos están duplicados, puedes utilizar
        puedes utilizar get_duplicates()
        """
        _raise_invalid_type("seqindexes", seqindexes, (list,))
        _raise_invalid_elements("seqindexes", seqindexes, (int,))

        ordered_seqindexes = sorted(seqindexes)
        range_list = list(range(len(ordered_seqindexes)))

        # Si las listas son iguales retorna una lista vacia
        if range_list == ordered_seqindexes:
            return []

        missing_indexes = []
        for index in range_list:
            if index not in ordered_seqindexes:
                missing_indexes.append(index)

        return missing_indexes

    @staticmethod
    def get_duplicates(seqindexes: List[int]) -> Dict[int, int]:
        """Si la lista (normalmente obtenida con get_seqindexes) contiene
        duplicados, retorna un diccionario con los elementos duplicados y su cuenta.
        Si la lista está bien, retornará un diccionario vacio.

        [+] Que la lista de indices contenga duplicados implica también que hay
        elementos faltantes. Por ejemplo, si la lista es [0,0] eso no solo implica
        que 0 está duplicado, sino que además falta 1, ya que la lista al ser de dos
        elementos debería ser [0, 1]. Esa información la puedes obtener con
        get_missing() que en este caso retornaría [1]
        """
        _raise_invalid_type("seqindexes", seqindexes, (list,))
        _raise_invalid_elements("seqindexes", seqindexes, (int,))
        count = {}
        for item in seqindexes:
            if item in count:
                count[item] += 1
            else:
                count[item] = 1

        # Filtrar solo los elementos con más de una aparición
        return {item: cnt for item, cnt in count.items() if cnt > 1}

    @staticmethod
    def any_duplicated(seqindexes: List[int]) -> bool:
        """Verifica si hay algún duplicado en la lista de índices.
        Retorna True si encuentra un duplicado, de lo contrario False.
        """
        _raise_invalid_type("seqindexes", seqindexes, (list,))
        _raise_invalid_elements("seqindexes", seqindexes, (int,))
        seen = set()
        for item in seqindexes:
            if item in seen:
                return True
            seen.add(item)
        return False

    @staticmethod
    def adjust_broken(seqindexes: List[int]):
        """Esta función sirve como ayuda para resolver un lista de seqindexes rota
        como por ejemplo [0,2,3], donde vemos que nos falta el indice 1. Lo que
        hará será retornarnos un diccionario con las posiciones a las que se
        aconseja mover los indices, quedando así en este caso: {0:0, 2:1, 3:2}

        [!] Si hay duplicados esta función lanzará una excepción.
            Puedes usar any_duplicated() para averiguar hay duplicados y en caso de
            haber duplicados uedes utilizar get_duplicates() para saber cuales son y
            tomar tus propias medidas.

            Una vez que tengas una lista sin duplicados, entonces podrás invocar a
            esta función."""

        _raise_invalid_type("seqindexes", seqindexes, (list,))
        _raise_invalid_elements("seqindexes", seqindexes, (int,))
        _raise_contains_duplicates("seqindexes", seqindexes)

        reordered_indexes = {}
        for new, old in enumerate(seqindexes):
            reordered_indexes[old] = new

        return reordered_indexes

    #  CAT: Properties
    @property
    def separator(self):
        return self._separator

    @property
    def enumerate_first(self) -> bool:
        return self._enumerate_first

    @property
    def from_zero(self) -> bool:
        return self._from_zero

    @property
    def min_numlen(self) -> int:
        return self._min_numlen

    @property
    def def_name(self) -> Optional[str]:
        """Retorna el valor por defecto o None"""
        return self._def_name

    @def_name.setter
    def def_name(self, value: Optional[str]):
        """Permite reasignar el nombre por defecto"""
        self._def_name = self._get_def_name(value)

    @property
    def def_ext(self) -> Optional[str]:
        """Retorna la extensión por defecto o None"""
        return self._def_ext

    @def_ext.setter
    def def_ext(self, value: Optional[str]):
        self._def_ext = self._get_def_ext(value)

    #  CAT: Private Methods
    def _get_name(self, name: Optional[str], *, stack=2):
        """Obtiene name o def_name"""
        vname = "name"
        _raise_required_def(vname, name, self._def_name, stack=stack)
        assert self._def_name is not None, ""

        # Si name no se ha indicado usamos def_name
        if name is None:
            return self._def_name

        _raise_invalid_type(vname, name, (str,))
        _raise_contains_points(vname, name, stack=stack)
        _raise_requires_one_char(vname, name, stack=stack)

        return name

    def _get_ext(self, ext: Optional[str], *, stack=2):
        """Obtiene ext o def_ext"""
        vname = "ext"

        # Si no hay ext retornamos def_ext que también puede se None
        if ext is None:
            return self._def_ext

        _raise_invalid_type(vname, ext, (str,))
        _raise_contains_points(vname, ext, stack=stack)
        _raise_requires_one_char(vname, ext, stack=stack)

        return ext

    @staticmethod
    def _validate_index(index: int, *, stack=2):
        """Válida que el indice sea mayor que cero así como su tipo de dato."""
        vname = "index"
        _raise_invalid_type(vname, index, (int,), stack=stack)
        _raise_min(vname, index, 0, stack=stack)

    @staticmethod
    def _get_separator(separator, *, stack=2):
        """Obtiene separator, usado por __init__ y posibles setters."""
        vname = "separator"
        _raise_invalid_type(vname, separator, (str,), stack=stack)
        _raise_requires_one_char(vname, separator, stack=stack)
        _raise_contains_points(vname, separator, stack=stack)
        _raise_contains_digits(vname, separator, stack=stack)
        return separator

    @staticmethod
    def _get_enumerate_first(enumerate_first, *, stack=2):
        """Obtiene enumerate_first, usado por __init__ y posibles setters."""
        vname = "enumerate_first"
        _raise_invalid_type(vname, enumerate_first, (bool,), stack=stack)
        return enumerate_first

    @staticmethod
    def _get_from_zero(from_zero, *, stack=2):
        """Obtiene from_zero, usado por __init__ y posibles setters."""
        vname = "from_zero"
        _raise_invalid_type(vname, from_zero, (bool,), stack=stack)
        return from_zero

    @staticmethod
    def _get_min_numlen(min_numlen, *, stack=2):
        """Obtiene min_numlen, usado por __init__ y posibles setters."""
        vname = "min_numlen"
        _raise_invalid_type(vname, min_numlen, (int,), stack=stack)
        _raise_min(vname, min_numlen, 0, stack=stack)
        return min_numlen

    @staticmethod
    def _get_def_name(def_name: Optional[str], *, stack=2):
        """Obitene def_name, usado por __init__ y posibles setters.
        Para obtener name/def_name utiliza _get_name."""
        vname = "def_name"
        # Se permite que sea None y en ese caso no hay nada que validar
        if def_name is None:
            return

        _raise_invalid_type(vname, def_name, (str,), stack=stack)
        _raise_contains_points(vname, def_name, stack=stack)
        _raise_requires_one_char(vname, def_name, stack=stack)
        return def_name

    @staticmethod
    def _get_def_ext(def_ext: Optional[str], *, stack=2):
        """Obtiene def_ext, usado por __init__ y posibles setters.
        Para obtener ext/def_ext usa _get_ext."""
        vname = "def_ext"
        # Se permite que sea None y en ese caso no hay nada que validar
        if def_ext is None:
            return

        _raise_invalid_type(vname, def_ext, (str,), stack=stack)
        _raise_contains_points(vname, def_ext, stack=stack)
        _raise_requires_one_char(vname, def_ext, stack=stack)
        return def_ext

    @staticmethod
    def _raise_not_seqname(seqname: str, *, stack=1):
        stack += 1
        perr = _func_emsg(stack=stack)
        raise NotPartOfSeq(
            seqname,
            f"{perr} '{BGRAY}{seqname}{END}' no forma parte de esta secuencia",
        )


#  INFO: Ejemplo de uso real

# Estoy haciendo un programa de backups que permite establecer categorías, ejemplo light para todo aquello que no sea muy pesado, y como no es muy pesado pues el usuario decide que quiere conservar hasta 10 backups de lo mismo. Para guardar las backups, he decidido que se almacenen en las siguientes carpetas:

# light.bak light_1.bak light_2.bak light_3.bak ...

# Por lo que voy a crear un NameDecorator que haga este trabajo por mi:
nd = NameNumerator(
    def_name="light",
    def_ext="bak",
)

# ¿Qué nombre de carpeta le correspondería a 0?
print(f"A 0 le corresponde {nd.get_seqname(0, "light", "bak")}")

# Pero como tenemos settings por defecto para name y ext no hace falta que
# indiquemos esos valores en ninguna función, se usarán si no los especificamos

nombres_validos = [nd.get_seqname(i) for i in range(10)]
print("Nombres válidos: ", nombres_validos)

# Vale, ya se como voy a poner de nombre a mis carpetas, pero digamos que yo
# quiero saber si hay alguna ya creada, le pasamos todos los nombres que hay
# en la carpeta para que nos diga cuales hay
nombres_en_la_carpeta = [
    "videoPrivado.mp4",
    "light_1.bak",
    "light.bak",
    "light_2.bak",
]

usados = nd.get_seqindexes(nombres_en_la_carpeta)
usados_list = [nd.get_seqname(i) for i in usados]
print(f"Se han usado estos nombres: {usados_list}")

# Tenemos los indices y como puedes ver hemos obtenido los nombres a traves de
# ellos. Digamos que quiero hacer una backup más, lo haríamos así.
if len(usados) < 10:
    print(
        f"{nd.get_seqname(len(usados))} está disponible para usar como carpeta de"
        f" backups"
    )

    # Creariamos la backup en tmp_light, y ahora vamos a asignarle el nombre que
    # le corresponde, pero para ello vamos a renombrar todos los demas:
    for i in reversed(usados):
        old_name = nd.get_seqname(i)
        new_name = nd.get_seqname(i + 1)
        print(f"renombrando {old_name} a {new_name} ... ")

    print(f"renombrando tmp_light a {nd.get_seqname(0)}")

# Y listo, ese sería el funcionamiento en un mundo maravilloso en el que no ocurren
# cosas malas. Ahora vamos a suponer que el usuario se come una carpeta.
nombres_en_la_carpeta = [
    "videoPrivado.mp4",
    "light_1.bak",
    "light_2.bak",
]
usados = nd.get_seqindexes(nombres_en_la_carpeta)
print(f"Veremos que algo no esta bien: {usados}")

missings = nd.get_missings(usados)
if missings:
    # Obtenemos los nombres faltantes y los imprimimos
    misings_str = f"{END},{BGRAY} ".join(nd.get_seqname(i) for i in missings)
    print(
        f"\n{BYELLOW}[!] Aviso{END}: Las siguientes carpetas deberían estar y no"
        f" están: '{BGRAY}{misings_str}{END}'"
    )
    print(f"\n Vamos a reordenar las carpetas primero ...")

    # Vamos a ayudarnos de NameDecorator para que nos ayude a ajustar los nombres
    solucion_propuesta = nd.adjust_broken(usados)
    for indice, nuevo_indice in solucion_propuesta.items():
        nombre = nd.get_seqname(indice)
        nuevo_nombre = nd.get_seqname(nuevo_indice)
    
        print(f" Renombrando carpeta {nombre} a {nuevo_nombre} ... ")
    
    # usados = solucion_propuesta.values()
    usados = range(len(usados))
    usados_list = [nd.get_seqname(i) for i in usados]

print(f"\nSe nos ha quedado así: {usados_list}")

# Y eso sería todo en cuanto al uso principal que yo voy a usar, adicionalmente
# hay funciones que son útiles para ciertas situaciones como cuando se permite
# que haya duplicados y se le pasan nombres duplicados, pero ahora que entiendes
# el proposito de la clase te dejo que lo investigues tu Zetaky.

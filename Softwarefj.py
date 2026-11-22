"""
Sistema Integral de Gestión de Clientes, Servicios y Reservas - Software FJ
Arquitectura Orientada a Objetos en memoria (sin base de datos) con manejo
avanzado de excepciones y auditoría en archivo de logs.
Codigo: 213023 UNIVERSIDAD NACIONAL ABIERTA Y A DISTANCIA
NICOLAS ANDRES GARCIA DE AVILA
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from functools import singledispatchmethod
from pathlib import Path
import re
from typing import Any


# ==============================================================================
# 1. JERARQUÍA DE EXCEPCIONES PERSONALIZADAS
# ==============================================================================

class SoftwareFJError(Exception):
    """Excepción base del dominio de Software FJ."""

    def __init__(self, mensaje: str, codigo: str = "ERR_GENERAL") -> None:
        self.codigo = codigo
        super().__init__(f"[{codigo}] {mensaje}")


class DatosInvalidosError(SoftwareFJError):
    """Se lanza cuando un dato tiene formato, tipo o rango incorrecto."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="ERR_DATOS_INVALIDOS")


class ParametroFaltanteError(SoftwareFJError):
    """Se lanza cuando falta un parámetro obligatorio o se envía vacío."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="ERR_PARAMETRO_FALTANTE")


class OperacionNoPermitidaError(SoftwareFJError):
    """Se lanza al ejecutar una acción incompatible con el estado actual."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="ERR_OPERACION_NO_PERMITIDA")


class ReservaInvalidaError(SoftwareFJError):
    """Se lanza ante reglas violadas o fallos críticos en una reserva."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="ERR_RESERVA_INVALIDA")


class ServicioNoDisponibleError(SoftwareFJError):
    """Se lanza cuando se intenta reservar o procesar un servicio inactivo."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="ERR_SERVICIO_NO_DISPONIBLE")


class CalculoInconsistenteError(SoftwareFJError):
    """Se lanza cuando una liquidación financiera produce valores inválidos."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="ERR_CALCULO_INCONSISTENTE")


# ==============================================================================
# 2. REGISTRO DE AUDITORÍA Y ERRORES (ARCHIVO DE LOGS)
# ==============================================================================

class LoggerSistema:
    """
    Gestiona la escritura de eventos y errores en un archivo plano (.log).
    El uso de archivos se restringe exclusivamente a esta auditoría.
    """

    def __init__(self, ruta_archivo: str = "software_fj.log") -> None:
        self._ruta = Path(ruta_archivo)
        self._escribir("INFO", "Sistema", "=== Nueva ejecución de Software FJ ===")

    def _escribir(self, nivel: str, origen: str, mensaje: str) -> None:
        marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea = f"[{marca_tiempo}] [{nivel:<7}] [{origen}] {mensaje}\n"
        with open(self._ruta, mode="a", encoding="utf-8") as archivo:
            archivo.write(linea)

    def info(self, origen: str, mensaje: str) -> None:
        self._escribir("INFO", origen, mensaje)

    def advertencia(self, origen: str, mensaje: str) -> None:
        self._escribir("WARNING", origen, mensaje)

    def error(self, origen: str, exc: Exception) -> None:
        detalle = f"{type(exc).__name__}: {exc}"
        if exc.__cause__ is not None:
            causa = exc.__cause__
            detalle += f" | Causa encadenada -> {type(causa).__name__}: {causa}"
        self._escribir("ERROR", origen, detalle)


# ==============================================================================
# 3. ABSTRACCIÓN BASE Y ENCAPSULACIÓN DE CLIENTES
# ==============================================================================

class EntidadSistema(ABC):
    """Clase abstracta que representa cualquier entidad general del sistema."""

    def __init__(self, id_entidad: str) -> None:
        if not id_entidad or not str(id_entidad).strip():
            raise ParametroFaltanteError("El identificador de la entidad es obligatorio.")
        self._id_entidad: str = str(id_entidad).strip().upper()
        self._fecha_registro: datetime = datetime.now()

    @property
    def id_entidad(self) -> str:
        return self._id_entidad

    @property
    def fecha_registro(self) -> datetime:
        return self._fecha_registro

    @abstractmethod
    def validar(self) -> bool:
        """Verifica la integridad de los atributos de la entidad."""

    @abstractmethod
    def obtener_resumen(self) -> dict[str, Any]:
        """Devuelve un diccionario con los datos clave de la entidad."""

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self._id_entidad})"


class Cliente(EntidadSistema):
    """Representa un cliente con atributos privados encapsulados y validados."""

    _REGEX_CORREO = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    def __init__(
        self,
        id_cliente: str,
        nombre: str,
        documento: str,
        correo: str,
        telefono: str,
    ) -> None:
        super().__init__(id_cliente)
        self.__nombre: str = ""
        self.__documento: str = ""
        self.__correo: str = ""
        self.__telefono: str = ""

        # Se asigna a través de los setters para garantizar validación estricta
        self.nombre = nombre
        self.documento = documento
        self.correo = correo
        self.telefono = telefono
        self.validar()

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not valor or not isinstance(valor, str) or not valor.strip():
            raise ParametroFaltanteError("El nombre del cliente es obligatorio.")
        if len(valor.strip()) < 3:
            raise DatosInvalidosError("El nombre debe contener al menos 3 caracteres.")
        self.__nombre = valor.strip().title()

    @property
    def documento(self) -> str:
        return self.__documento

    @documento.setter
    def documento(self, valor: str) -> None:
        if not valor or not str(valor).strip():
            raise ParametroFaltanteError("El documento de identidad es obligatorio.")
        limpio = str(valor).strip()
        if not limpio.isdigit() or not (6 <= len(limpio) <= 12):
            raise DatosInvalidosError(
                f"Documento inválido ('{valor}'): requiere entre 6 y 12 dígitos."
            )
        self.__documento = limpio

    @property
    def correo(self) -> str:
        return self.__correo

    @correo.setter
    def correo(self, valor: str) -> None:
        if not valor or not isinstance(valor, str) or not valor.strip():
            raise ParametroFaltanteError("El correo electrónico es obligatorio.")
        limpio = valor.strip().lower()
        if not self._REGEX_CORREO.match(limpio):
            raise DatosInvalidosError(f"Correo electrónico con formato inválido: '{valor}'.")
        self.__correo = limpio

    @property
    def telefono(self) -> str:
        return self.__telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        if not valor or not str(valor).strip():
            raise ParametroFaltanteError("El teléfono de contacto es obligatorio.")
        limpio = str(valor).strip().replace(" ", "").replace("+", "")
        if not limpio.isdigit() or not (7 <= len(limpio) <= 13):
            raise DatosInvalidosError(
                f"Teléfono inválido ('{valor}'): requiere entre 7 y 13 dígitos."
            )
        self.__telefono = limpio

    def validar(self) -> bool:
        if not all([self.__nombre, self.__documento, self.__correo, self.__telefono]):
            raise DatosInvalidosError(f"El cliente {self.id_entidad} posee campos vacíos.")
        return True

    def obtener_resumen(self) -> dict[str, Any]:
        return {
            "id": self.id_entidad,
            "nombre": self.__nombre,
            "documento": self.__documento,
            "correo": self.__correo,
            "telefono": self.__telefono,
        }

    def __str__(self) -> str:
        return f"Cliente[{self.id_entidad}] {self.__nombre} (Doc: {self.__documento})"


# ==============================================================================
# 4. CLASE ABSTRACTA SERVICIO, POLIMORFISMO Y SOBRECARGA DE MÉTODOS
# ==============================================================================

class Servicio(EntidadSistema):
    """Clase abstracta para el catálogo de servicios de Software FJ."""

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_hora: float,
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio)
        if not nombre or not str(nombre).strip():
            raise ParametroFaltanteError("El nombre del servicio es obligatorio.")

        try:
            tarifa = float(tarifa_hora)
        except (TypeError, ValueError) as exc:
            raise DatosInvalidosError(
                f"La tarifa por hora debe ser numérica, se recibió: '{tarifa_hora}'."
            ) from exc

        if tarifa <= 0:
            raise DatosInvalidosError("La tarifa por hora debe ser mayor a cero.")

        self._nombre: str = nombre.strip()
        self._tarifa_hora: float = tarifa
        self._disponible: bool = bool(disponible)

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_hora(self) -> float:
        return self._tarifa_hora

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        self._disponible = bool(estado)

    def verificar_disponibilidad(self) -> None:
        if not self._disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self._nombre}' ({self.id_entidad}) no está disponible."
            )

    @abstractmethod
    def calcular_costo(self, duracion_horas: int) -> float:
        """Calcula el costo base según la lógica propia de cada servicio."""

    @abstractmethod
    def describir(self) -> str:
        """Devuelve una descripción detallada y especializada del servicio."""

    @abstractmethod
    def validar_parametros(self) -> bool:
        """Valida las reglas específicas de cada subtipo de servicio."""

    def validar(self) -> bool:
        return self.validar_parametros()

    # --- MÉTODO SOBRECARGADO (@singledispatchmethod) ---
    @singledispatchmethod
    def calcular_costo_final(self, ajuste: Any, duracion_horas: int) -> float:
        """
        Sobrecarga de cálculo de costos según el tipo de ajuste recibido:
        - None: retorna costo base sin modificaciones.
        - int | float: aplica porcentaje de descuento directo (ej. 10 -> 10%).
        - dict: aplica {'impuesto': float, 'descuento': float}.
        """
        raise DatosInvalidosError(
            f"Tipo de ajuste no soportado en sobrecarga: {type(ajuste).__name__}"
        )

    @calcular_costo_final.register
    def _(self, ajuste: None, duracion_horas: int) -> float:
        return round(self.calcular_costo(duracion_horas), 2)

    @calcular_costo_final.register(int)
    @calcular_costo_final.register(float)
    def _(self, ajuste: int | float, duracion_horas: int) -> float:
        subtotal = self.calcular_costo(duracion_horas)
        if ajuste < 0 or ajuste >= 100:
            raise CalculoInconsistenteError(
                f"Descuento porcentual inválido ({ajuste}%): debe estar entre 0 y 99."
            )
        total = subtotal * (1 - float(ajuste) / 100.0)
        if total <= 0:
            raise CalculoInconsistenteError("El cálculo con descuento arrojó un monto <= 0.")
        return round(total, 2)

    @calcular_costo_final.register
    def _(self, ajuste: dict, duracion_horas: int) -> float:
        subtotal = self.calcular_costo(duracion_horas)
        try:
            impuesto = float(ajuste.get("impuesto", 0.0))
            descuento = float(ajuste.get("descuento", 0.0))
        except (TypeError, ValueError) as exc:
            raise CalculoInconsistenteError(
                "Los parámetros 'impuesto' y 'descuento' deben ser numéricos."
            ) from exc

        if impuesto < 0 or descuento < 0:
            raise CalculoInconsistenteError("Impuestos y descuentos no pueden ser negativos.")
        if descuento >= 100:
            raise CalculoInconsistenteError("El descuento no puede ser igual o mayor al 100%.")

        base_con_descuento = subtotal * (1 - descuento / 100.0)
        total = base_con_descuento * (1 + impuesto / 100.0)
        if total <= 0:
            raise CalculoInconsistenteError("El monto total calculado es inconsistente (<= 0).")
        return round(total, 2)

    def obtener_resumen(self) -> dict[str, Any]:
        return {
            "id": self.id_entidad,
            "tipo": self.__class__.__name__,
            "nombre": self._nombre,
            "tarifa_hora": self._tarifa_hora,
            "disponible": self._disponible,
            "descripcion": self.describir(),
        }


class ReservaSala(Servicio):
    """Servicio especializado para reserva de salas de reuniones y capacitación."""

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_hora: float,
        capacidad_personas: int,
        incluye_audiovisual: bool = True,
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio, nombre, tarifa_hora, disponible)
        self._capacidad_personas = capacidad_personas
        self._incluye_audiovisual = bool(incluye_audiovisual)
        self.validar_parametros()

    def validar_parametros(self) -> bool:
        if not isinstance(self._capacidad_personas, int) or self._capacidad_personas <= 0:
            raise DatosInvalidosError(
                f"Capacidad inválida ({self._capacidad_personas}): debe ser entero positivo."
            )
        if self._capacidad_personas > 100:
            raise DatosInvalidosError("La capacidad máxima permitida por sala es 100 personas.")
        return True

    def calcular_costo(self, duracion_horas: int) -> float:
        if not isinstance(duracion_horas, int) or duracion_horas <= 0:
            raise DatosInvalidosError("La duración de reserva debe ser un entero positivo.")
        costo = self._tarifa_hora * duracion_horas
        if self._incluye_audiovisual:
            costo += 25.0 * duracion_horas  # Recargo por sistema audiovisual HD
        if duracion_horas >= 8:
            costo *= 0.90  # 10% de descuento automático por jornada completa
        return round(costo, 2)

    def describir(self) -> str:
        av = "con equipo audiovisual" if self._incluye_audiovisual else "sin equipo audiovisual"
        return f"Sala '{self._nombre}' (Capacidad: {self._capacidad_personas} pers., {av})"


class AlquilerEquipo(Servicio):
    """Servicio especializado para alquiler de hardware y equipos tecnológicos."""

    _CATEGORIAS_VALIDAS = {"LAPTOP", "SERVIDOR", "PROYECTOR", "WORKSTATION", "REDES"}

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_hora: float,
        categoria: str,
        cantidad_unidades: int,
        con_seguro: bool = True,
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio, nombre, tarifa_hora, disponible)
        if not categoria or not str(categoria).strip():
            raise ParametroFaltanteError("La categoría del equipo es obligatoria.")
        self._categoria = str(categoria).strip().upper()
        self._cantidad_unidades = cantidad_unidades
        self._con_seguro = bool(con_seguro)
        self.validar_parametros()

    def validar_parametros(self) -> bool:
        if self._categoria not in self._CATEGORIAS_VALIDAS:
            raise DatosInvalidosError(
                f"Categoría '{self._categoria}' no válida. Permitidas: {sorted(self._CATEGORIAS_VALIDAS)}"
            )
        if not isinstance(self._cantidad_unidades, int) or self._cantidad_unidades <= 0:
            raise DatosInvalidosError("La cantidad de unidades debe ser mayor a cero.")
        return True

    def calcular_costo(self, duracion_horas: int) -> float:
        if not isinstance(duracion_horas, int) or duracion_horas <= 0:
            raise DatosInvalidosError("La duración del alquiler debe ser al menos 1 hora.")
        costo = self._tarifa_hora * duracion_horas * self._cantidad_unidades
        if self._con_seguro:
            costo *= 1.12  # 12% por póliza de protección de hardware
        return round(costo, 2)

    def describir(self) -> str:
        seguro = "con póliza de seguro" if self._con_seguro else "sin seguro"
        return (
            f"Alquiler {self._cantidad_unidades}x {self._nombre} "
            f"[{self._categoria}, {seguro}]"
        )


class AsesoriaEspecializada(Servicio):
    """Servicio especializado para consultoría técnica y arquitectura de TI."""

    _ESPECIALIDADES_VALIDAS = {"CIBERSEGURIDAD", "CLOUD", "DESARROLLO", "INFRAESTRUCTURA", "DATOS"}
    _FACTOR_NIVEL = {"JUNIOR": 1.0, "SENIOR": 1.35, "ARQUITECTO": 1.75}

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        tarifa_hora: float,
        especialidad: str,
        nivel_consultor: str = "SENIOR",
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio, nombre, tarifa_hora, disponible)
        if not especialidad or not nivel_consultor:
            raise ParametroFaltanteError("Especialidad y nivel de consultor son obligatorios.")
        self._especialidad = str(especialidad).strip().upper()
        self._nivel_consultor = str(nivel_consultor).strip().upper()
        self.validar_parametros()

    def validar_parametros(self) -> bool:
        if self._especialidad not in self._ESPECIALIDADES_VALIDAS:
            raise DatosInvalidosError(
                f"Especialidad '{self._especialidad}' no soportada. "
                f"Válidas: {sorted(self._ESPECIALIDADES_VALIDAS)}"
            )
        if self._nivel_consultor not in self._FACTOR_NIVEL:
            raise DatosInvalidosError(
                f"Nivel '{self._nivel_consultor}' inválido. Válidos: {list(self._FACTOR_NIVEL.keys())}"
            )
        return True

    def calcular_costo(self, duracion_horas: int) -> float:
        if not isinstance(duracion_horas, int) or duracion_horas <= 0:
            raise DatosInvalidosError("La duración de la asesoría debe ser un entero positivo.")
        factor = self._FACTOR_NIVEL[self._nivel_consultor]
        return round(self._tarifa_hora * duracion_horas * factor, 2)

    def describir(self) -> str:
        return (
            f"Asesoría en {self._especialidad}: '{self._nombre}' "
            f"(Nivel: {self._nivel_consultor})"
        )


# ==============================================================================
# 5. CLASE RESERVA Y CONTROL DE CICLO DE VIDA
# ==============================================================================

class EstadoReserva(Enum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    PROCESADA = "PROCESADA"
    CANCELADA = "CANCELADA"


class Reserva(EntidadSistema):
    """Integra Cliente, Servicio, duración y estados con manejo robusto de errores."""

    def __init__(
        self,
        id_reserva: str,
        cliente: Cliente,
        servicio: Servicio,
        duracion_horas: int,
        logger: LoggerSistema,
    ) -> None:
        super().__init__(id_reserva)
        if cliente is None or servicio is None:
            raise ParametroFaltanteError("La reserva requiere un cliente y un servicio válidos.")
        if not isinstance(cliente, Cliente):
            raise DatosInvalidosError("El cliente proporcionado no es una instancia válida.")
        if not isinstance(servicio, Servicio):
            raise DatosInvalidosError("El servicio proporcionado no es una instancia válida.")

        try:
            duracion = int(duracion_horas)
        except (TypeError, ValueError) as exc:
            raise ReservaInvalidaError(
                f"La duración debe ser entera, se recibió: '{duracion_horas}'."
            ) from exc

        if duracion <= 0 or duracion > 720:
            raise ReservaInvalidaError(
                f"Duración fuera de rango ({duracion}h): permitida entre 1 y 720 horas."
            )

        self._cliente: Cliente = cliente
        self._servicio: Servicio = servicio
        self._duracion_horas: int = duracion
        self._estado: EstadoReserva = EstadoReserva.PENDIENTE
        self._costo_final: float = 0.0
        self._logger: LoggerSistema = logger
        self.validar()

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def duracion_horas(self) -> int:
        return self._duracion_horas

    @property
    def estado(self) -> EstadoReserva:
        return self._estado

    @property
    def costo_final(self) -> float:
        return self._costo_final

    def validar(self) -> bool:
        self._cliente.validar()
        self._servicio.validar()
        return True

    def confirmar(self) -> None:
        """Confirma una reserva pendiente usando estructura try / except / else."""
        try:
            if self._estado != EstadoReserva.PENDIENTE:
                raise OperacionNoPermitidaError(
                    f"No se puede confirmar {self.id_entidad} desde estado {self._estado.value}."
                )
            self._servicio.verificar_disponibilidad()
        except SoftwareFJError as exc:
            self._logger.error(f"Reserva.confirmar[{self.id_entidad}]", exc)
            raise
        else:
            self._estado = EstadoReserva.CONFIRMADA
            self._logger.info(
                f"Reserva.confirmar[{self.id_entidad}]",
                f"Confirmada para {self._cliente.nombre} -> {self._servicio.nombre}.",
            )

    def cancelar(self, motivo: str = "Cancelación solicitada") -> None:
        """Cancela una reserva siempre que no haya sido procesada."""
        if self._estado == EstadoReserva.PROCESADA:
            raise OperacionNoPermitidaError(
                f"La reserva {self.id_entidad} ya fue PROCESADA y no admite cancelación."
            )
        if self._estado == EstadoReserva.CANCELADA:
            raise OperacionNoPermitidaError(
                f"La reserva {self.id_entidad} ya está CANCELADA."
            )
        self._estado = EstadoReserva.CANCELADA
        self._logger.advertencia(
            f"Reserva.cancelar[{self.id_entidad}]",
            f"Cancelada. Motivo: {motivo}",
        )

    def procesar(self, ajuste_tarifa: Any = None) -> float:
        """
        Liquida el costo de la reserva usando try / except / finally
        y encadenamiento de excepciones.
        """
        procesada_ok = False
        try:
            if self._estado != EstadoReserva.CONFIRMADA:
                raise OperacionNoPermitidaError(
                    f"Solo se procesan reservas CONFIRMADAS (estado actual: {self._estado.value})."
                )
            self._servicio.verificar_disponibilidad()
            total = self._servicio.calcular_costo_final(ajuste_tarifa, self._duracion_horas)

            if total <= 0:
                raise CalculoInconsistenteError(
                    f"Monto calculado inválido (${total}) en reserva {self.id_entidad}."
                )

            self._costo_final = total
            self._estado = EstadoReserva.PROCESADA
            procesada_ok = True
            self._logger.info(
                f"Reserva.procesar[{self.id_entidad}]",
                f"Procesada exitosamente. Total liquidado: ${self._costo_final:,.2f}",
            )
            return self._costo_final

        except SoftwareFJError as exc:
            self._logger.error(f"Reserva.procesar[{self.id_entidad}]", exc)
            raise
        except Exception as exc:
            error_encadenado = ReservaInvalidaError(
                f"Error inesperado al procesar reserva {self.id_entidad}."
            )
            self._logger.error(f"Reserva.procesar[{self.id_entidad}]", exc)
            raise error_encadenado from exc
        finally:
            resultado_auditoria = "EXITOSO" if procesada_ok else "FALLIDO"
            self._logger.info(
                f"Reserva.auditoria[{self.id_entidad}]",
                f"Cierre de procesamiento ({resultado_auditoria}). Estado: {self._estado.value}.",
            )

    def obtener_resumen(self) -> dict[str, Any]:
        return {
            "id_reserva": self.id_entidad,
            "cliente": self._cliente.nombre,
            "servicio": self._servicio.nombre,
            "duracion_horas": self._duracion_horas,
            "estado": self._estado.value,
            "costo_final": self._costo_final,
        }

    def __str__(self) -> str:
        return (
            f"Reserva[{self.id_entidad}] | Cliente: {self._cliente.nombre} | "
            f"Servicio: {self._servicio.nombre} ({self._duracion_horas}h) | "
            f"Estado: {self._estado.value} | Total: ${self._costo_final:,.2f}"
        )


# ==============================================================================
# 6. ORQUESTADOR CENTRAL EN MEMORIA (SIN BASE DE DATOS)
# ==============================================================================

class SistemaSoftwareFJ:
    """Administra clientes, servicios y reservas mediante listas internas en memoria."""

    def __init__(self, ruta_log: str = "software_fj.log") -> None:
        self.__clientes: list[Cliente] = []
        self.__servicios: list[Servicio] = []
        self.__reservas: list[Reserva] = []
        self.logger = LoggerSistema(ruta_log)

    @property
    def clientes(self) -> list[Cliente]:
        return list(self.__clientes)

    @property
    def servicios(self) -> list[Servicio]:
        return list(self.__servicios)

    @property
    def reservas(self) -> list[Reserva]:
        return list(self.__reservas)

    def registrar_cliente(self, cliente: Cliente) -> bool:
        try:
            cliente.validar()
            for existente in self.__clientes:
                if existente.id_entidad == cliente.id_entidad:
                    raise OperacionNoPermitidaError(
                        f"ID de cliente duplicado: '{cliente.id_entidad}'."
                    )
                if existente.documento == cliente.documento:
                    raise OperacionNoPermitidaError(
                        f"Documento ya registrado: '{cliente.documento}'."
                    )
        except SoftwareFJError as exc:
            self.logger.error("Sistema.registrar_cliente", exc)
            raise
        else:
            self.__clientes.append(cliente)
            self.logger.info("Sistema.registrar_cliente", f"Registrado: {cliente}")
            return True

    def agregar_servicio(self, servicio: Servicio) -> bool:
        try:
            servicio.validar()
            if any(s.id_entidad == servicio.id_entidad for s in self.__servicios):
                raise OperacionNoPermitidaError(
                    f"ID de servicio duplicado: '{servicio.id_entidad}'."
                )
        except SoftwareFJError as exc:
            self.logger.error("Sistema.agregar_servicio", exc)
            raise
        else:
            self.__servicios.append(servicio)
            self.logger.info("Sistema.agregar_servicio", f"Agregado: {servicio.describir()}")
            return True

    def buscar_cliente(self, id_cliente: str) -> Cliente:
        id_norm = id_cliente.strip().upper()
        for cliente in self.__clientes:
            if cliente.id_entidad == id_norm:
                return cliente
        raise DatosInvalidosError(f"Cliente '{id_cliente}' no encontrado en el sistema.")

    def buscar_servicio(self, id_servicio: str) -> Servicio:
        id_norm = id_servicio.strip().upper()
        for servicio in self.__servicios:
            if servicio.id_entidad == id_norm:
                return servicio
        raise DatosInvalidosError(f"Servicio '{id_servicio}' no encontrado en el catálogo.")

    def crear_reserva(
        self,
        id_reserva: str,
        id_cliente: str,
        id_servicio: str,
        duracion_horas: int,
    ) -> Reserva:
        try:
            if any(r.id_entidad == id_reserva.strip().upper() for r in self.__reservas):
                raise OperacionNoPermitidaError(
                    f"Código de reserva duplicado: '{id_reserva}'."
                )
            cliente = self.buscar_cliente(id_cliente)
            servicio = self.buscar_servicio(id_servicio)
            reserva = Reserva(id_reserva, cliente, servicio, duracion_horas, self.logger)
        except SoftwareFJError as exc:
            self.logger.error("Sistema.crear_reserva", exc)
            raise
        else:
            self.__reservas.append(reserva)
            self.logger.info("Sistema.crear_reserva", f"Creada: {reserva}")
            return reserva

    def obtener_resumen_general(self) -> dict[str, Any]:
        total_ingresos = sum(r.costo_final for r in self.__reservas)
        return {
            "clientes_registrados": len(self.__clientes),
            "servicios_en_catalogo": len(self.__servicios),
            "reservas_totales": len(self.__reservas),
            "ingresos_liquidados": round(total_ingresos, 2),
        }


# ==============================================================================
# 7. SIMULACIÓN DE 12 OPERACIONES COMPLETAS (VÁLIDAS Y CON FALLOS CONTROLADOS)
# ==============================================================================

def ejecutar_paso(numero: int, descripcion: str, accion) -> None:
    """Ejecuta una operación aislando excepciones para que el sistema nunca se detenga."""
    print(f"\n[{numero:02d}] {descripcion}")
    try:
        salida = accion()
        if salida is not None:
            print(f"  -> ÉXITO: {salida}")
    except SoftwareFJError as exc:
        print(f"  -> ERROR CONTROLADO: {exc}")
        if exc.__cause__ is not None:
            print(f"     Causa raíz encadenada: {type(exc.__cause__).__name__}: {exc.__cause__}")
    except Exception as exc:
        print(f"  -> ERROR INESPERADO CAPTURADO: {type(exc).__name__}: {exc}")


def main() -> None:
    sistema = SistemaSoftwareFJ(ruta_log="software_fj.log")
    print("==================================================================")
    print("   SOFTWARE FJ - GESTIÓN INTEGRAL DE CLIENTES, SERVICIOS Y RESERVAS")
    print("==================================================================")

    # 1. Registro válido de cliente 1
    ejecutar_paso(
        1,
        "Registro válido de cliente corporativo (CLI-01)",
        lambda: sistema.registrar_cliente(
            Cliente("CLI-01", "Laura Martínez", "1020456789", "laura@empresa.co", "3104567890")
        ),
    )

    # 2. Registro válido de cliente 2
    ejecutar_paso(
        2,
        "Registro válido de segundo cliente (CLI-02)",
        lambda: sistema.registrar_cliente(
            Cliente("CLI-02", "Carlos Gómez", "80123456", "cgomez@techmail.com", "3209876543")
        ),
    )

    # 3. Registro inválido de cliente (datos malformados)
    ejecutar_paso(
        3,
        "Intento de registro de cliente con documento corto y correo inválido",
        lambda: sistema.registrar_cliente(
            Cliente("CLI-03", "Ana", "123", "correo_invalido", "3001112233")
        ),
    )

    # 4. Registro inválido de cliente duplicado
    ejecutar_paso(
        4,
        "Intento de registro de cliente con documento ya existente",
        lambda: sistema.registrar_cliente(
            Cliente("CLI-04", "Laura Duplicada", "1020456789", "otra@empresa.co", "3112223344")
        ),
    )

    # 5. Creación correcta de 3 servicios especializados (Polimorfismo)
    def crear_catalogo():
        s1 = ReservaSala("SRV-01", "Sala Innovación A", 80.0, capacidad_personas=20, incluye_audiovisual=True)
        s2 = AlquilerEquipo("SRV-02", "Workstation Dell Precision", 35.0, categoria="WORKSTATION", cantidad_unidades=3)
        s3 = AsesoriaEspecializada("SRV-03", "Auditoría Zero-Trust", 120.0, especialidad="CIBERSEGURIDAD", nivel_consultor="ARQUITECTO")
        sistema.agregar_servicio(s1)
        sistema.agregar_servicio(s2)
        sistema.agregar_servicio(s3)
        return "3 servicios especializados registrados correctamente."

    ejecutar_paso(5, "Creación válida de 3 servicios especializados", crear_catalogo)

    # 6. Creación incorrecta de servicio (capacidad negativa)
    ejecutar_paso(
        6,
        "Intento de creación de servicio con parámetros inválidos",
        lambda: sistema.agregar_servicio(
            ReservaSala("SRV-99", "Sala Inválida", 50.0, capacidad_personas=-5)
        ),
    )

    # 7. Registro de servicio marcado como no disponible
    ejecutar_paso(
        7,
        "Registro de servicio temporalmente no disponible (SRV-04)",
        lambda: sistema.agregar_servicio(
            AlquilerEquipo("SRV-04", "Servidor Rack Xeon", 150.0, categoria="SERVIDOR", cantidad_unidades=1, disponible=False)
        ),
    )

    # 8. Reserva exitosa 1: Sala con jornada completa y sobrecarga dict (IVA + descuento)
    def reserva_sala_exitosa():
        res = sistema.crear_reserva("RES-01", "CLI-01", "SRV-01", duracion_horas=8)
        res.confirmar()
        res.procesar(ajuste_tarifa={"impuesto": 19.0, "descuento": 10.0})
        return str(res)

    ejecutar_paso(8, "Reserva exitosa de Sala (sobrecarga con impuesto 19% y descuento 10%)", reserva_sala_exitosa)

    # 9. Reserva exitosa 2: Asesoría con sobrecarga float (descuento directo)
    def reserva_asesoria_exitosa():
        res = sistema.crear_reserva("RES-02", "CLI-02", "SRV-03", duracion_horas=4)
        res.confirmar()
        res.procesar(ajuste_tarifa=15.0)
        return str(res)

    ejecutar_paso(9, "Reserva exitosa de Asesoría (sobrecarga con descuento directo 15%)", reserva_asesoria_exitosa)

    # 10. Reserva exitosa 3: Alquiler de equipos sin ajustes (sobrecarga None)
    def reserva_equipos_exitosa():
        res = sistema.crear_reserva("RES-03", "CLI-01", "SRV-02", duracion_horas=5)
        res.confirmar()
        res.procesar()
        return str(res)

    ejecutar_paso(10, "Reserva exitosa de Equipos (sobrecarga base sin ajustes)", reserva_equipos_exitosa)

    # 11. Reserva fallida: intento de confirmar servicio no disponible
    def reserva_servicio_inactivo():
        res = sistema.crear_reserva("RES-04", "CLI-02", "SRV-04", duracion_horas=3)
        res.confirmar()
        return str(res)

    ejecutar_paso(11, "Intento de confirmar reserva sobre servicio no disponible", reserva_servicio_inactivo)

    # 12. Cancelación válida + intento prohibido de procesar + fallo de cálculo encadenado
    def reserva_cancelada_y_error_calculo():
        res_cancel = sistema.crear_reserva("RES-05", "CLI-02", "SRV-02", duracion_horas=2)
        res_cancel.confirmar()
        res_cancel.cancelar(motivo="Reprogramación del cliente")

        res_fallo = sistema.crear_reserva("RES-06", "CLI-01", "SRV-02", duracion_horas=2)
        res_fallo.confirmar()
        res_fallo.procesar(ajuste_tarifa={"impuesto": "INVALIDO", "descuento": 5})

    ejecutar_paso(12, "Cancelación de reserva y fallo controlado por cálculo inconsistente", reserva_cancelada_y_error_calculo)

    # --- REPORTE FINAL EN CONSOLA ---
    print("\n==================================================================")
    print("   RESUMEN FINAL DEL SISTEMA (MEMORIA)                            ")
    print("==================================================================")
    for clave, valor in sistema.obtener_resumen_general().items():
        print(f" * {clave}: {valor}")

    print("\n--- Estado final de las reservas en memoria ---")
    for r in sistema.reservas:
        print(f" - {r}")

    print("\n[OK] Todos los eventos y excepciones fueron registrados en 'software_fj.log'.")


if __name__ == "__main__":
    main()
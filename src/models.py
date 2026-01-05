

class DisplayConfig:
    def __init__(self, count=None, size=None, placement=None, height=None, serial=None):
        self._count = count
        self._size = size
        self._placement = placement
        self._height = height
        self._serial = serial

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value):
        if value is not None and value <= 0:
            raise ValueError("Screen count must be positive")
        self._count = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        if value is not None and value.strip() == "":
            raise ValueError("Screen size cannot be empty")
        self._size = value

    @property
    def placement(self):
        return self._placement

    @placement.setter
    def placement(self, value):
        if value is not None and value < 0:
            raise ValueError("Screen placement must be non-negative")
        self._placement = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        if value is not None and value < 0:
            raise ValueError("Screen height must be non-negative")
        self._height = value

    @property
    def serial(self):
        return self._serial

    @serial.setter
    def serial(self, value):
        self._serial = value

    def to_dict(self):
        return {
            "count": self.count,
            "size": self.size,
            "placement": self.placement,
            "height": self.height,
            "serial": self.serial,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            count=d.get("count"),
            size=d.get("size"),
            placement=d.get("placement"),
            height=d.get("height"),
            serial=d.get("serial"),
        )


class DockConfig:
    def __init__(self, names=None, count=0, size=None, enabled=False, total_width=0):
        self._names = names or []
        self._count = count
        self._size = size or []
        self._enabled = enabled
        self._total_width = total_width

    @property
    def names(self):
        return self._names

    @names.setter
    def names(self, value):
        if not isinstance(value, list):
            raise TypeError("Dock names must be a list.")
        if not all(isinstance(n, str) and n.strip() for n in value):
            raise ValueError("All dock names must be non-empty strings.")
        self._names = value

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value):
        if value is not None and value <= 0:
            raise ValueError("Dock count must be positive")
        self._count = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            raise TypeError("Dock sizes must be a list.")
        if not all(isinstance(s, str) and s.strip() for s in value):
            raise ValueError("All dock sizes must be non-empty strings.")
        self._size = value

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value

    @property
    def total_width(self):
        return self._total_width

    @total_width.setter
    def total_width(self, value):
        if value is not None and value < 0:
            raise ValueError("Total width must be non-negative")
        self._total_width = value

    def to_dict(self):
        return {
            "names": self.names,
            "count": self.count,
            "size": self.size,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            names=d.get("names"),
            count=d.get("count"),
            size=d.get("size"),
            enabled=d.get("enabled"),
        )


class IntegralConfig:
    def __init__(self, serial=None, firmware=None, integrals=None):
        self._serial = serial
        self._firmware = firmware
        self._integrals = integrals or {}

    @property
    def serial(self):
        return self._serial

    @serial.setter
    def serial(self, value):
        self._serial = value

    @property
    def firmware(self):
        return self._firmware

    @firmware.setter
    def firmware(self, value):
        self._firmware = value

    @property
    def integrals(self):
        return self._integrals

    @integrals.setter
    def integrals(self, value):
        if not isinstance(value, dict):
            raise ValueError("Integrals must be a dictionary")
        self._integrals = value

    def to_dict(self):
        return {
            "serial": self.serial,
            "firmware": self.firmware,
            "integrals": self.integrals,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            serial=d.get("serial"),
            firmware=d.get("firmware"),
            integrals=d.get("integrals"),
        )
    

class VCConfig:
    def __init__(self, multi_display=False, placement=None, teams=False, zoom=False):
        self._multi_display = multi_display
        self._placement = placement
        self._teams = teams
        self._zoom = zoom

    @property
    def multi_display(self):
        return self._multi_display

    @multi_display.setter
    def multi_display(self, value):
        self._multi_display = value

    @property
    def placement(self):
        return self._placement

    @placement.setter
    def placement(self, value):
        self._placement = value

    @property
    def teams(self):
        return self._teams

    @teams.setter
    def teams(self, value):
        self._teams = value

    @property
    def zoom(self):
        return self._zoom

    @zoom.setter
    def zoom(self, value):
        self._zoom = value

    def to_dict(self):
        return {
            "multi_display": self.multi_display,
            "placement": self.placement,
            "teams": self.teams,
            "zoom": self.zoom,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            multi_display=d.get("multi_display"),
            placement=d.get("placement"),
            teams=d.get("teams"),
            zoom=d.get("zoom"),
        )
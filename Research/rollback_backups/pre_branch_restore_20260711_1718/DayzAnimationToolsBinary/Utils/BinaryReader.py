from io import BytesIO
import struct

class BinaryReader():
	def __init__(self, buffer:bytes):
		self.Buffer = buffer
		self.BaseStream = BytesIO(self.Buffer)

	def Read(self, *args) -> bytes:
		return self.BaseStream.read(*args)

	def GetPos(self) -> int:
		return self.BaseStream.tell()

	def SetPos(self, pos: int):
		self.BaseStream.seek(pos)

	def Seek(self, offset):
		self.SetPos(self.GetPos() + offset)

	def ReadBool(self) -> bool:
		return bool(struct.unpack('<' + "b", self.Read(1))[0])

	def ReadByte(self) -> int:
		byte = struct.unpack('<' + "c", self.Read(1))[0]
		return int.from_bytes(byte, "little")

	def ReadBytes(self, count) -> bytes:
		ret = bytearray(count)
		for i in range(count):
			ret[i] = self.Read(1)[0]
		return ret

	def ReadUByte(self) -> int:
		return struct.unpack('<' + "B", self.Read(1))[0]

	def ReadInt16(self) -> int:
		return struct.unpack('<' + "h", self.Read(2))[0]

	def ReadUInt16(self) -> int:
		return struct.unpack('<' + "H", self.Read(2))[0]

	def ReadInt32(self) -> int:
		return struct.unpack('<' + "i", self.Read(4))[0]

	def ReadUInt32(self) -> int:
		return struct.unpack('<' + "I", self.Read(4))[0]

	def ReadInt64(self) -> int:
		return struct.unpack('<' + "q", self.Read(8))[0]

	def ReadUInt64(self) -> int:
		return struct.unpack('<' + "Q", self.Read(8))[0]

	def ReadSingle(self) -> float:
		return struct.unpack('<' + "f", self.Read(4))[0]

	def ReadDouble(self) -> float:
		return struct.unpack('<' + "d", self.Read(8))[0]


	def ReadInt32BE(self) -> int:
		return struct.unpack('>' + "i", self.Read(4))[0]

	def ReadAscii(self, size: int) -> str:
		ret = struct.unpack('<' + "%is" % (size), self.Read(size))[0]
		return ret.decode("ascii")

	def ReadAsciiz(self) -> str:
		ret = []
		c = b""
		while c != b"\0":
			ret.append(c)
			c = self.Read(1)
			if not c: raise ValueError("Unterminated string: %r" % (ret))
		return  b''.join(ret).decode("ascii")

	def ReadCharParseInt(self) -> int:
		return self.ReadByte() & 15
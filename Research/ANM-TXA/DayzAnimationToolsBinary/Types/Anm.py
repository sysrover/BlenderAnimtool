from enum import Enum
import os, struct
from io import BytesIO
from DayzAnimationToolsBinary.Utils.BinaryReader import BinaryReader

SCALE_FACTOR = 1.525902E-05
'''Conversion scale commonly used in 3d software, DayZ uses it'''

FLT_EPSILON = 1.175494351E-38
'''IEEE 754 standard float epsilson'''

FLT_MAX = 3.402823466E+38
'''IEEE 754 standard float max'''

class AnmImportSettings:

	__slots__ = (
		'fUnitScale',
		'bImportTranslationKeys',
		'bImportRotationKeys',
		'bImportScaleKeys'
	)
	
	def __init__(self):
		self.fUnitScale:float = 1.0
		self.bImportTranslationKeys:bool = True
		self.bImportRotationKeys:bool = True
		self.bImportScaleKeys:bool = False

class AnmFormat(Enum):
	AnimSet5 = 5
	'''Preferable animation format because it does not hold scale animation, which DayZ disregards'''

	AnimSet6 = 6
	'''Version with scale information, useless for DayZ currently, but workbench imports animations in this format'''

importSettings = AnmImportSettings()

class Anm(object):

	__slots__ = (
		'name',
		'formSize',
		'format',
		'fps',
		'numFrames',
		'bones',
		'boneAnimModifiers',
		'events',
		'custProps'
	)

	def __init__(self, path=None, unitScale=1.0):
		self.name = ''
		self.format = AnmFormat.AnimSet5
		self.fps = 30
		self.numFrames = 0
		self.bones:list[AnmBone] = []
		self.boneAnimModifiers = []
		self.events:list[AnmEvent] = []
		self.custProps:list[tuple[str, str]] = []

	def CreateFromFile(filepath=None, inImportSettings = AnmImportSettings()):
		anm = Anm()

		if filepath is None or filepath == '':
			return anm
		
		global importSettings
		importSettings = inImportSettings

		buffer = b''
		with open(filepath, 'rb') as fs:
			buffer = fs.read()

		br = BinaryReader(buffer)
		anm.Read(br)

		return anm
	
	def Read(self, br: BinaryReader):
		# Read Form Section
		br.Seek(4) # "FORM"
		FORMSIZE = br.ReadInt32BE()
		br.Seek(7); # "ANIMSET"
		self.format = AnmFormat(br.ReadCharParseInt())
		br.Seek(4) # Anim Data Length
		br.Seek(8) # Constant
		self.fps = br.ReadInt32()

		# Read Head Section
		br.Seek(4) # "HEAD"
		HEADSIZE = br.ReadInt32BE()
		headStartPos = br.GetPos()
		while br.GetPos() < headStartPos + HEADSIZE:
			bone = AnmBone()
			bone.Read(br, self.format)
			self.bones.append(bone)
			
		# Read Data Section
		br.Seek(4) # "DATA"
		DATASIZE = br.ReadInt32BE()

		for bone in self.bones:
			for posKey in bone.posKeys:
				posKey.frame = br.ReadUInt16()
				self.numFrames = max(self.numFrames, posKey.frame + 1)

			for posKey in bone.posKeys:
				posX = br.ReadUInt16()
				posZ = br.ReadUInt16()
				posY = br.ReadUInt16()
				posKey.data = (posX, posY, posZ)

			for scaleKey in bone.scaleKeys:
				scaleKey.frame = br.ReadUInt16()
				self.numFrames = max(self.numFrames, scaleKey.frame + 1)

			for scaleKey in bone.scaleKeys:
				scaleX = br.ReadUInt16()
				scaleZ = br.ReadUInt16()
				scaleY = br.ReadUInt16()
				scaleKey.data = (scaleX, scaleY, scaleZ)

			for rotKey in bone.rotKeys:
				rotKey.frame = br.ReadUInt16()
				self.numFrames = max(self.numFrames, rotKey.frame + 1)

			for rotKey in bone.rotKeys:
				rotX = br.ReadUInt16()
				rotZ = br.ReadUInt16()
				rotY = br.ReadUInt16()
				rotW = br.ReadUInt16()
				rotKey.data = (rotX, rotY, rotZ, rotW)

		# if eof exception, there are no events so return, if more data, it must be 'EVNT'
		try: assert (br.ReadAscii(4) == 'EVNT')
		except: return
		
		EVNTSIZE = br.ReadInt32BE()
		numEvents = br.ReadUInt16()
		for _ in range(numEvents):
			event = AnmEvent()
			event.frame = br.ReadInt32()

			sizeName = br.ReadInt32()
			event.name = br.ReadAscii(sizeName).replace('bytearray(b\'', '').replace('\\x00\')', '').replace('\x00', '')

			sizeUserString = br.ReadInt32()
			event.userString = br.ReadAscii(sizeUserString).replace('bytearray(b\'', '').replace('\\x00\')', '').replace('\x00', '')

			event.userInt = br.ReadInt32()

			self.events.append(event)

		# Optional custom properties chunk CPRP
		tag_pos = br.GetPos()
		try:
			tag = br.ReadAscii(4)
		except:
			return
		if tag != 'CPRP':
			br.SetPos(tag_pos)
			return
		chunk_size = br.ReadInt32BE()
		chunk_end = br.GetPos() + chunk_size
		try:
			count = br.ReadUInt16()
		except:
			br.SetPos(chunk_end)
			return
		for _ in range(count):
			key_len = br.ReadInt32()  # Fixed: was UInt16 in Ghidra, but data shows Int32
			key_bytes = br.ReadBytes(key_len) if key_len > 0 else b''
			val_len = br.ReadInt32()  # Fixed: was UInt16 in Ghidra, but data shows Int32
			val_bytes = br.ReadBytes(val_len) if val_len > 0 else b''
			key = key_bytes.decode('utf-8', errors='ignore').rstrip('\x00')
			val = val_bytes.decode('utf-8', errors='ignore').rstrip('\x00')
			self.custProps.append((key, val))
		br.SetPos(chunk_end)

class AnmBone(object):

	__slots__ = (
		'name',
		'posBias',
		'posMulti',
		'rotBias',
		'rotMulti',
		'scaleBias',
		'scaleMulti',
		'numFrames',
		'flags',
		'posKeys',
		'rotKeys',
		'scaleKeys'
	)

	def __init__(self):
		self.name = ''
		self.posBias = 0.0
		self.posMulti = 0.0
		self.rotBias = 0.0
		self.rotMulti = 0.0
		self.scaleBias = 0.0
		self.scaleMulti = 0.0
		self.numFrames = 0
		self.flags = 0
		self.posKeys:list[AnmKeyFrame] = []
		self.rotKeys:list[AnmKeyFrame] = []
		self.scaleKeys:list[AnmKeyFrame] = []
	
	def Read(self, br: BinaryReader = None, format:AnmFormat = AnmFormat.AnimSet5):

		if br is None: return

		if format is AnmFormat.AnimSet5:
			self.name = br.ReadAscii(32).replace('\0', '')

		global SCALE_FACTOR

		self.posBias = br.ReadSingle()
		self.posMulti = br.ReadSingle() * SCALE_FACTOR

		self.rotBias = br.ReadSingle()
		self.rotMulti = br.ReadSingle() * SCALE_FACTOR

		if format is AnmFormat.AnimSet6:
			self.scaleBias = br.ReadSingle()
			self.scaleMulti = br.ReadSingle() * SCALE_FACTOR

		self.numFrames = br.ReadInt16()

		numPosKeys = br.ReadInt16()
		numRotKeys = br.ReadInt16()
		numScaleKeys = 0 if format is AnmFormat.AnimSet5 else br.ReadInt16()

		for _ in range(numPosKeys): self.posKeys.append(AnmKeyFrame())
		for _ in range(numRotKeys): self.rotKeys.append(AnmKeyFrame())
		for _ in range(numScaleKeys): self.scaleKeys.append(AnmKeyFrame())

		if format is AnmFormat.AnimSet5:
			self.flags = br.ReadInt16()
		elif format is AnmFormat.AnimSet6:
			self.flags = br.ReadByte()
			nameLen = br.ReadByte()
			self.name = br.ReadAscii(nameLen)

class AnmKeyFrame(object):

	__slots__ = (
		'frame',
		'data'
	)

	def __init__(self, frame = 0, data = ()):
		self.frame:int = frame
		self.data:tuple[float, ...] = data

class AnmEvent(object):

	__slots__ = (
		'frame',
		'name',
		'userString',
		'userInt'
	)

	def __init__(self):
		self.frame:int = 0
		self.name:str = ''
		self.userString:str = ''
		self.userInt:int = -1

def CompressFlt(input: float, minimum: float, range: float) -> int:
	return int(min(max((input - minimum) * range, 0), 0xFFFF))

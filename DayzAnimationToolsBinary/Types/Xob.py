from enum import Enum
import io
import zlib
import struct
from io import BufferedWriter, BufferedReader
from DayzAnimationTools.Utils.DayzAnimUtils import *
from DayzAnimationToolsBinary.Utils.BinaryReader import BinaryReader
from DayzAnimationToolsBinary.Utils.Lz4Decoder import Lz4Decoder

UnitScale = 1.0

class XobFormat(Enum):
	Xob6 = 6
	Xob8 = 8

class CompressionType(Enum):
	None
	Lz4 = 0x344F5A4C
	ZLib = 0x42494C5A

class Xob(object):

	__slots__ = (
		'path',
		'format',
		'sizeForm',
		'sizeHead',
		'editorCameraSettings',
		'assetList',
		'materials',
		'bones',
		'lods'
	)

	def __init__(self):
		self.path:str = ''
		self.format:XobFormat = XobFormat.Xob6
		self.sizeForm:int = 0
		self.sizeHead:int = 0
		self.editorCameraSettings:XobEditorCameraSettings = XobEditorCameraSettings()
		self.assetList:list[str] = []
		self.materials:list[XobMaterial] = []
		self.bones:list[XobBone]  = []
		self.lods:list[XobLod]  = []

	def CreateFromFile(path=None, unitScale=1.0):
		xob = Xob()

		if path is None or path == '':
			return xob
		
		xob.path:str = path

		global UnitScale
		UnitScale = unitScale

		buffer = b''
		with open(path, 'rb') as fs:
			buffer = fs.read()

		br = BinaryReader(buffer)
		xob.ReadForm( br )
		xob.ReadHead( br )
		xob.ReadLods( br )
		
		return xob

	def ReadForm(self, br: BinaryReader):
		assert br.ReadAscii(4) == 'FORM', '"FORM" signature missing!' # "FORM" signature
		self.sizeForm = br.ReadInt32BE(); # form size (big endian)
		assert br.ReadAscii(3) == 'XOB', 'Format signature missing!' # "XOB" signature
		self.format = XobFormat(br.ReadCharParseInt())

	def ReadHead(self, br: BinaryReader):
		assert br.ReadAscii(4) == 'HEAD' # "HEAD" signature
		self.sizeHead = br.ReadInt32BE(); # head size (big endian)

		br.Seek(4); # null
		
 		# editor camera info
		self.editorCameraSettings.Position = FVector(
			br.ReadSingle(),
			br.ReadSingle(),
			br.ReadSingle()
		)
		self.editorCameraSettings.Rotation = FVector(
			br.ReadSingle(),
			br.ReadSingle(),
			br.ReadSingle()
		)

		br.Seek(12); # null

		br.Seek(4); # unknown

		numMats = br.ReadUInt16()
		numBones = br.ReadUInt16()
		numLods = br.ReadUInt16()
		
		br.Seek(6) # Constant b'\xFF\0\0\0\0\0'

		# assets
		assetListSize = br.ReadInt32()
		self.assetList = []
		pos = br.GetPos()
		while br.GetPos() - pos < assetListSize:
			self.assetList.append(br.ReadAsciiz())

		# Xob8 assetList has another entry:
		# {guid}path/materialName.emat
		# after every materialName entry
		if self.format is XobFormat.Xob8:
			numMats *= 2

		# materials
		for i in range(numMats):
			mat = XobMaterial()
			mat.Read(br)
			mat.name = self.assetList[mat.idxAsset]
			self.materials.append(mat)
		
		# bones
		for _ in range(numBones):
			bone = XobBone()
			bone.Read(br)
			bone.name = self.assetList[bone.idxAsset]
			if bone.name.lower() != 'scene_root':
				self.bones.append(bone)
		XobBone.DetermineParents(self.bones)
		
		# lods
		for idxLod in range(numLods):
			lod = XobLod()
			lod.Read(br,self.format)
			lod.idx = idxLod
			self.lods.append(lod)
			for mesh in lod.meshes:
				mesh.name = self.assetList[mesh.idxAsset]
		

	def ReadLods(self, br: BinaryReader):
		for lod in self.lods:
			pos = br.GetPos() # save pos
			br.SetPos(lod.offsetDataCprs) # move pos to mesh data position
			decompressed = b''
			if lod.compressionType is CompressionType.ZLib:
				decompressed = zlib.decompress(br.ReadBytes(lod.lenDataCprs))
			else:
				num = 0
				cpsLength = 0
				decoder = Lz4Decoder()
				while num < lod.lenDataCprs:
					cpsLength = br.ReadInt32() & 0x7FFFFFFF
					decoder.Decode(br,cpsLength)
					num += cpsLength + 4
				decompressed = bytes(decoder.decompressed)
			
			br.SetPos(pos) # move pos back to original
			brCps = BinaryReader(decompressed)

			for mesh in lod.meshes:
				for face in mesh.faces:
					face.set(brCps.ReadUInt16(), brCps.ReadUInt16(), brCps.ReadUInt16())

				for face in mesh.faces:
					mesh.faceVerts.append((brCps.ReadUInt16(), brCps.ReadUInt16(), brCps.ReadUInt16()))

				for vertex in mesh.vertices:
					x = brCps.ReadSingle() * UnitScale
					z = brCps.ReadSingle() * UnitScale
					y = brCps.ReadSingle() * UnitScale
					vertex.position = FVector(x,y,z)

					if mesh.numWeightedBones > 0:
						vertex.weightIndex = brCps.ReadInt32()

				for vertex in mesh.vertices: # TODO: SwapYZ?
					packedNormal = brCps.ReadUInt32()
					x = (packedNormal >> 21) / 1023 - 1				# 11 most significant bits
					y = (packedNormal >> 10 & 2047) / 1023 - 1		# 11th to 21st bits from the right
					z = (packedNormal & 1023) / 511 - 1				# 9 least significant bits
					vertex.normal = (x, y, z)

				for vertex in mesh.vertices:
					for _ in range(len(mesh.materialIndices)):
						vertex.uvLayers.append( (brCps.ReadInt16() / 1024.0, 1 - (brCps.ReadInt16() / 1024.0)) )

				brCps.Seek(mesh.num24 * 12)

				if mesh.numWeightedBones > 0:
					posWeights = brCps.GetPos()
					for vertex in mesh.vertices:
						brCps.SetPos(posWeights + (vertex.weightIndex * 16))

						idxWeightedBone1 = brCps.ReadByte()
						idxWeightedBone2 = brCps.ReadByte()
						idxWeightedBone3 = brCps.ReadByte()
						idxWeightedBone4 = brCps.ReadByte()

						idxBone1 = mesh.indiciesWeightedBones[idxWeightedBone1] - 1
						idxBone2 = mesh.indiciesWeightedBones[idxWeightedBone2] - 1
						idxBone3 = mesh.indiciesWeightedBones[idxWeightedBone3] - 1
						idxBone4 = mesh.indiciesWeightedBones[idxWeightedBone4] - 1

						weight1 = brCps.ReadSingle()
						weight2 = brCps.ReadSingle()
						weight3 = brCps.ReadSingle()
						weight4 = 1.0 - (weight1 + weight2 + weight3)

						vertex.weights.append( (idxBone1, weight1) )
						if weight2 > 0: vertex.weights.append( (idxBone2, weight2) )
						if weight3 > 0: vertex.weights.append( (idxBone3, weight3) )
						if weight4 > 0 and idxBone4 != idxBone1 and idxBone4 != idxBone2 and idxBone4 != idxBone3:
							vertex.weights.append( (idxBone4, weight4) )

					brCps.SetPos(posWeights + (mesh.numTotalVertexWeights * 16))


class XobLod(object):

	__slots__ = (
		'idx',
		'meshes',
		'headerPos',
		'dataCprs',
		'lenDataCprs',
		'offsetDataCprs',
		'compressionType'
	)
		
	def __init__(self):
		self.meshes:list[XobMesh] = []
		self.idx:int = -1
		self.headerPos:int = 0
		self.dataCprs:bytes = b''
		self.lenDataCprs:int = 0
		self.offsetDataCprs:int = 0
		self.compressionType:CompressionType = CompressionType.ZLib
		

	def Read(self, br: BinaryReader, format: XobFormat):
		if format is XobFormat.Xob8:
			self.compressionType = CompressionType(br.ReadUInt32())

		numMeshes = br.ReadUInt32()
		for _ in range(numMeshes):
			self.meshes.append(XobMesh())

		br.Seek(4) # null
		br.Seek(4) # constant big endian 0x803f
		br.Seek(4) # unknown, big endian, typically near 10k

		self.offsetDataCprs = br.ReadUInt32()
		self.lenDataCprs = br.ReadUInt32()

		if format is XobFormat.Xob8:
			br.Seek(4) # unknown
			
		bMultiMeshLod = len(self.meshes) > 1
		
		for mesh in self.meshes:
			mesh.Read(br, format, bMultiMeshLod)


	def Write(self, bw: BufferedWriter):
		self.headerPos = bw.tell() # unknown
		bw.write(struct.pack('<I', len(self.meshes)))

		bw.write(struct.pack('>I', 0)) # null
		bw.write(struct.pack('>I', 0x803f)) # constant big endian 0x803f
		bw.write(struct.pack('>I', 10000)) # unknown, big endian, typically near 10k

		bw.write(struct.pack('<I', 0)) # offset placeholder
		bw.write(struct.pack('<I', 0)) # length placeholder

	def __str__(self):
		ret = f'XobLod {self.idx} ({len(self.meshes)} XobMesh'
		if len(self.meshes) != 1: ret += 'es'
		ret += ')'
		return ret

	def __repr__(self): return str(self)

class XobMaterial(object):

	__slots__ = (
		'name',
		'idxAsset'
	)

	def __init__(self):
		self.name:str = ''
		self.idxAsset:int = -1

	def Read(self, br: BufferedReader):
		self.idxAsset = br.ReadInt16()
	
	def Write(self, bw: BufferedWriter):
		bw.write(struct.pack('<H', self.idxAsset))

	def __str__(self): return self.name
	def __repr__(self): return str(self)

class XobBone(object):

	__slots__ = (
		'name',
		'leftIndex',
		'rightIndex',
		'parentIndex',
		'idxAsset',
		'Pos',
		'Rot'
	)

	def __init__(self):
		self.name:str = ''
		self.idxAsset:int = 0
		self.rightIndex:int = 0
		self.parentIndex:int = -1
		self.idxAsset:int = 0
		self.idxAsset:int = 0
		self.Pos:tuple[float,float,float] = (0.0,0.0,0.0)
		self.Rot:tuple[float,float,float,float] = (0.0,0.0,0.0,0.0)

	
	def Read(self, br: BinaryReader):
		
		testing = f'{br.GetPos()} {hex(br.GetPos())}'

		self.idxAsset = br.ReadInt32()

		posX = br.ReadSingle() * UnitScale
		posZ = br.ReadSingle() * UnitScale
		posY = br.ReadSingle() * UnitScale
		self.Pos = (posX, posY, posZ)

		rotX = br.ReadSingle()
		rotZ = br.ReadSingle()
		rotY = br.ReadSingle()
		rotW = -br.ReadSingle()
		self.Rot = (rotX, rotY, rotZ, rotW)

		self.leftIndex = br.ReadInt16()
		self.rightIndex = br.ReadInt16()
		
	def Write(self, bw: BufferedWriter):
		bw.write(struct.pack('<i', self.idxAsset))
		
		bw.write(struct.pack('<f', self.Pos[0]))
		bw.write(struct.pack('<f', self.Pos[2]))
		bw.write(struct.pack('<f', self.Pos[1]))
		
		bw.write(struct.pack('<f', self.Rot[0]))
		bw.write(struct.pack('<f', self.Rot[2]))
		bw.write(struct.pack('<f', self.Rot[1]))
		bw.write(struct.pack('<f', -self.Rot[3]))
		
		bw.write(struct.pack('<h', self.leftIndex))
		bw.write(struct.pack('<h', self.rightIndex))
		
	def DetermineParents(bones: list):
		# Children of Scene_Root should be considered root bones
		for idx in range(len(bones)):
			if bones[idx].parentIndex == 0:
				bones[idx].parentIndex = -1

		for idx in range(len(bones)):
			if bones[idx].leftIndex != -1:
				bones[bones[idx].leftIndex - 1].parentIndex = bones[idx].parentIndex # set left bone's parent to this bone's parent
			if bones[idx].rightIndex != -1:
				bones[bones[idx].rightIndex - 1].parentIndex = idx # set right bone's parent to this bone

	def __str__(self): return self.name
	def __repr__(self): return str(self)

class XobMesh(object):

	__slots__ = (
		'idxAsset',
		'name',
		'materialIndices',
		'faces',
		'vertices',
		'faceVerts',
		'dataDecprs',
		'numTotalVertexWeights',
		'numWeightedBones',
		'indiciesWeightedBones',
		'num24',
		'num26'
	)

	def __init__(self):
		self.materialIndices = []
		self.faces:list[XobFace] = []
		self.vertices:list[XobVertex] = []
		self.faceVerts:tuple[int,int,int] = []
		self.dataDecprs:bytearray = bytearray()

	def Read(self, br: BinaryReader, format: XobFormat, bMultiMeshLod:bool):
		if format is XobFormat.Xob6:
			self.idxAsset = br.ReadInt32()
			br.Seek(2) # unknown
		else:
			self.idxAsset = br.ReadUInt16()

		br.Seek(42) # unknown

		numFaces = br.ReadUInt16()
		for _ in range(numFaces): self.faces.append(XobFace())

		numVertices = br.ReadUInt16()
		for _ in range(numVertices): self.vertices.append(XobVertex())

		self.num24 = br.ReadUInt16()

		self.numTotalVertexWeights = br.ReadUInt16()

		self.num26 = br.ReadUInt16()
		numMaterialIndices = 0

		if format is XobFormat.Xob6: numMaterialIndices = br.ReadUInt16()
		br.Seek(2) # unknown
		key = br.ReadUInt16()
		if format is XobFormat.Xob8: numMaterialIndices = br.ReadByte()
		for _ in range(numMaterialIndices):
			self.materialIndices.append(key)
		
		self.numWeightedBones = br.ReadByte()

		br.Seek(1) # constant unknown 0x04

		br.Seek(6) # unknown

		if format is XobFormat.Xob8:
			br.Seek(17) # unknown
			if bMultiMeshLod:
				br.Seek(20) # unknown
		
		self.indiciesWeightedBones = br.ReadBytes(self.numWeightedBones)

	def Write(self, bw: BufferedWriter):
		num24 = 0 #4479
		weightsCount = 0
		bonesWithWeights = bytearray()
		for vert in self.vertices:
			for weight in vert.weights:
				weightsCount += 1
				if struct.pack('<b', weight[0]) not in bonesWithWeights:
					bonesWithWeights.extend(struct.pack('<b', weight[0]))

		bw.write(struct.pack('<i', self.idxAsset))
		bw.write(bytes(bytearray(4)))
		bw.write(bytes(bytearray(24)))
		bw.write(bytes(bytearray(16)))
		bw.write(struct.pack('<H', len(self.faces)))
		bw.write(struct.pack('<H', len(self.vertices)))
		bw.write(struct.pack('<H', num24)) # Skip Count?
		bw.write(struct.pack('<H', weightsCount)) #weightsCount
		bw.write(bytes(bytearray(2))) # Unknown
		bw.write(struct.pack('<H', len(self.materialIndices))) 
		bw.write(bytes(bytearray(2))) # Unknown
		bw.write(struct.pack('<H', self.materialIndices[0])) #key?
		bw.write(len(bonesWithWeights).to_bytes(1, 'little')) #count2?
		bw.write(b'\0') # Unknown
		bw.write(bytes(bytearray(6))) # Unknown
		if len(bonesWithWeights) > 0:
			bw.write(bytes(bonesWithWeights))

		for face in self.faces:
			self.dataDecprs.extend(struct.pack('<H', face[0]))
			self.dataDecprs.extend(struct.pack('<H', face[1]))
			self.dataDecprs.extend(struct.pack('<H', face[2]))

		self.dataDecprs.extend(bytes(bytearray(len(self.faces) * 6))) # Unknown

		for vert in self.vertices:
			self.dataDecprs.extend(struct.pack('<f', vert.position[0]))
			self.dataDecprs.extend(struct.pack('<f', vert.position[2]))
			self.dataDecprs.extend(struct.pack('<f', vert.position[1]))
			if len(bonesWithWeights) > 0:
				self.dataDecprs.extend(struct.pack('<i', vert.weightIndex))

		for vert in self.vertices:
			x = int((vert.normal[0] + 1) * 1023)
			y = int((vert.normal[1] + 1) * 1023)
			z = int((vert.normal[0] + 1) * 511)

			packedNormal = (x << 21) | (y << 10) | z

			self.dataDecprs.extend(struct.pack('<I', packedNormal))

		for vert in self.vertices:
			for idx in range(len(self.materialIndices)):
				self.dataDecprs.extend(struct.pack('<h', int(vert.uvLayers[idx][0] * 1024)))
				self.dataDecprs.extend(struct.pack('<h', int((1 - vert.uvLayers[idx][1]) * 1024)))

		#self.dataDecprs.extend(bytes(bytearray(num24 * 12))) # Unknown
		
		if len(bonesWithWeights) > 0:
			for vert in self.vertices:
				if len(vert.weights) > 4:
					print("!!! Unsupported by DayZ: XobVertex is weighted to more than 4 bones, giving remaining weight to 4th bone.")
				for weight in vert.weights:
					self.dataDecprs.extend(struct.pack('<b', bonesWithWeights.index(weight[0])))
				for _ in range(4 - len(vert.weights)):
					self.dataDecprs.extend(b'\0')
				for idxWeight in range(len(vert.weights)):
					if idxWeight == 3: pass # last weight not present because it is calculated as 1 - others
					self.dataDecprs.extend(struct.pack('<f', vert.weights[idxWeight][1]))
				for _ in range(3 - len(vert.weights)):
					self.dataDecprs.extend(struct.pack('<f', 0))

	def __str__(self): return self.name
	def __repr__(self): return str(self)

class XobEditorCameraSettings(object):

	__slots__ = (
		'Position',
		'Rotation',
	)

	def __init__(self):
		self.Position:FVector = FVector.zero()
		self.Rotation:FVector = FVector.zero()
	
	def set(self, InPosition:FVector, InRotation:FVector):
		self.Position = InPosition
		self.Rotation = InRotation

	def __str__(self): return f"(Pos = {self.Position}, Rot = {self.Rotation})"
	def __repr__(self): return str(self)

class XobVertex(object):

	__slots__ = (
		'position',
		'normal',
		'uvLayers',
		'weightIndex',
		'weights'
	)

	def __init__(self):
		self.position:FVector = FVector()
		self.normal:FVector = FVector()
		self.uvLayers:tuple[float,float] = []
		self.weightIndex:int = -1
		self.weights:list[tuple[int,float]] = []

class XobFace(object):

	__slots__ = (
		'v1',
		'v2',
		'v3',
		'normal'
	)

	def __init__(self, v1:int = 0, v2:int = 0, v3:int = 0):
		self.set(v1,v2,v3)
		self.normal:FVector = FVector()
	
	def set(self, v1:int, v2:int, v3:int):
		self.v1:int = v1
		self.v2:int = v2
		self.v3:int = v3

	def __str__(self): return f"({self.v1}, {self.v2}, {self.v3})"
	def __repr__(self): return str(self)
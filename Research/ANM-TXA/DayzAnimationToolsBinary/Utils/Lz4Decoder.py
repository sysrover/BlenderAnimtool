from DayzAnimationToolsBinary.Utils.BinaryReader import BinaryReader

class Lz4Decoder():
	def __init__(self):
		self.decompressed = []

	def Decode(self, br: BinaryReader, size: int):
		targetPos = br.GetPos() + size

		while br.GetPos() < targetPos:

			token = br.ReadByte()
			literalLength = token >> 4 # high 4 bits

			if literalLength == 0xF:
				while True:
					x = br.ReadByte()
					literalLength += x
					if x != 0xFF:
						break

			# literal data
			for _ in range(literalLength):
				self.decompressed.append(br.ReadByte())

			if br.GetPos() == targetPos: return

			matchOffset = 0
			try: matchOffset = br.ReadUInt16() # eof on last block
			except: return

			if (matchOffset == 0): continue

			matchLength = token & 0x0F

			if matchLength == 0xF:
				while True:
					x = br.ReadByte()
					matchLength += x
					if x != 0xFF:
						break
			
			matchLength += 4 # must add minimum match length
			matchPos = len(self.decompressed) - matchOffset
			for i in range(matchLength):
				self.decompressed.append(self.decompressed[matchPos + i])

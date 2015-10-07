import time
from PyQt4 import QtGui, QtCore
from .utils import Object, stage, getColor, Stage, removeItemsInList
from .events import EventDispatcher, Event, MouseEvent, AnimationEvent


__author__ = "Yuehao Wang"


class DisplayObject(EventDispatcher):
	def __init__(self):
		super(DisplayObject, self).__init__()

		self.name = "instance" + str(self.objectIndex)
		self.parent = None
		self.x = 0
		self.y = 0
		self.alpha = 1
		self.rotation = 0
		self.scaleX = 1
		self.scaleY = 1
		self.visible = True
		self.blendMode = None
		self.mask = None
		self._clipPath = None

	@property
	def width(self):
		return self._getOriginalWidth() * abs(self.scaleX)

	@property
	def height(self):
		return self._getOriginalHeight() * abs(self.scaleY)

	def __getCompositionMode(self):
		v = self.blendMode

		if v == BlendMode.SOURCE_ATOP:
			return QtGui.QPainter.CompositionMode_SourceAtop
		elif v == BlendMode.SOURCE_IN:
			return QtGui.QPainter.CompositionMode_SourceIn
		elif v == BlendMode.SOURCE_OUT:
			return QtGui.QPainter.CompositionMode_SourceOut
		elif v == BlendMode.DESTINATION_OVER:
			return QtGui.QPainter.CompositionMode_DestinationOver
		elif v == BlendMode.DESTINATION_ATOP:
			return QtGui.QPainter.CompositionMode_DestinationAtop
		elif v == BlendMode.DESTINATION_IN:
			return QtGui.QPainter.CompositionMode_DestinationIn
		elif v == BlendMode.DESTINATION_OUT:
			return QtGui.QPainter.CompositionMode_DestinationOut
		elif v == BlendMode.LIGHTER:
			return QtGui.QPainter.CompositionMode_Lighter
		elif v == BlendMode.COPY:
			return QtGui.QPainter.CompositionMode_Copy
		elif v == BlendMode.XOR:
			return QtGui.QPainter.CompositionMode_Xor
		else:
			return QtGui.QPainter.CompositionMode_SourceOver

	def _show(self, c):
		if not self.visible:
			return
		
		self._loopFrame()

		c.save()

		c.translate(self.x, self.y)
		c.setOpacity(self.alpha * c.opacity())
		c.rotate(self.rotation)
		c.scale(self.scaleX, self.scaleY)
		c.setCompositionMode(self.__getCompositionMode())

		if self._hasMask():
			c.setClipPath(self.mask._clipPath, QtCore.Qt.UniteClip)
			c.clipPath()

		self._loopDraw(c)

		c.restore()

	def _hasMask(self):
		return isinstance(self.mask, DisplayObject) and hasattr(self.mask, "_clipPath") and isinstance(self.mask._clipPath, QtGui.QPainterPath)

	def _isMouseOn(self, e, cd):
		if not self.visible:
			return

		ox = e["offsetX"]
		oy = e["offsetY"]
		x = cd["x"]
		y = cd["y"]
		scaleX = cd["scaleX"]
		scaleY = cd["scaleY"]
		w = self._getOriginalWidth()
		h = self._getOriginalHeight()

		if self._hasMask():
			return self.mask._isMouseOn(e, cd)
		else:
			if x <= ox <= x + w * scaleX and y <= oy <= y + h * scaleY:
				e["target"] = self

				return True

		return False

	def _loopFrame(self):
		pass

	def _loopDraw(self, c):
		pass

	def _getOriginalWidth(self):
		return 0

	def _getOriginalHeight(self):
		return 0

	def startX(self):
		return self.x

	def startY(self):
		return self.y

	def endX(self):
		return self.x + self.width

	def endY(self):
		return self.y + self.height

	def remove(self):
		if hasattr(self, "parent") and (isinstance(self.parent, DisplayObjectContainer) or isinstance(self.parent, Stage)):
			self.parent.removeChild(self)


class BlendMode(Object):
	SOURCE_OVER = "source-over"
	SOURCE_ATOP = "source-atop"
	SOURCE_IN = "source-in"
	SOURCE_OUT = "source-out"
	DESTINATION_OVER = "destination-over"
	DESTINATION_ATOP = "destination-atop"
	DESTINATION_IN = "destination-in"
	DESTINATION_OUT = "destination-out"
	LIGHTER = "lighter"
	COPY = "copy"
	XOR = "xor"
	NONE = None
	NORMAL = None

	def __init__(self,):
		raise Exception("BlendMode cannot be instantiated.")


class Loader(DisplayObject):
	ignoreLoadingError = False

	def __init__(self):
		super(Loader, self).__init__()

		self.content = None
		
	def load(self, url):
		image = QtGui.QImage()
		image.load(url)

		self.content = image

		if image.isNull() and not Loader.ignoreLoadingError:
			raise Exception("Loader cannot load data in the path you give.")

		e = Event(Event.COMPLETE)
		e.target = image
		self.dispatchEvent(e)


class BitmapData(Object):
	def __init__(self, image = QtGui.QImage(), x = 0, y = 0, width = 0, height = 0):
		super(BitmapData, self).__init__()

		self.image = image
		self.x = x
		self.y = y
		self.width = width
		self.height = height

		if image is not None:
			if width == 0:
				self.width = image.width()

			if height == 0:
				self.height = image.height()

	@property
	def x(self):
		return self.__x

	@x.setter
	def x(self, value):
		if value > self.image.width():
			value = self.image.width()
		
		self.__x = value

	@property
	def y(self):
		return self.__y

	@y.setter
	def y(self, value):
		if value > self.image.height():
			value = self.image.height()
		
		self.__y = value

	@property
	def width(self):
		return self.__width

	@width.setter
	def width(self, value):
		if (value + self.x) > self.image.width():
			value = self.image.width() - self.x
		
		self.__width = value

	@property
	def height(self):
		return self.__height

	@height.setter
	def height(self, value):
		if (value + self.y) > self.image.height():
			value = self.image.height() - self.y
		
		self.__height = value

	def setCoordinate(self, x = 0, y = 0):
		self.x = x
		self.y = y

	def setProperties(self, x = 0, y = 0, width = 0, height = 0):
		self.x = x
		self.y = y
		self.width = width
		self.height = height


class Bitmap(DisplayObject):
	def __init__(self, bitmapData = BitmapData()):
		super(Bitmap, self).__init__()

		self.bitmapData = bitmapData

	def _getOriginalWidth(self):
		return self.bitmapData.width

	def _getOriginalHeight(self):
		return self.bitmapData.height

	def _loopDraw(self, c):
		bmpd = self.bitmapData

		c.drawImage(0, 0, bmpd.image, bmpd.x, bmpd.y, bmpd.width, bmpd.height)


class InteractiveObject(DisplayObject):
	def __init__(self):
		super(InteractiveObject, self).__init__()
		
		self._mouseEventList = []
		self._mouseOver = False
		self.mouseEnabled = True

	def __isMouseEvent(self, e):
		return isinstance(e, Event) and (e.eventType.find("mouse") >= 0 or e.eventType.find("touch") >= 0)

	def addEventListener(self, e, listener):
		if self.__isMouseEvent(e):
			self._addEventListenerInList(e, listener, self._mouseEventList)
		else:
			super(InteractiveObject, self).addEventListener(e, listener)

	def removeEventListener(self, e, listener):
		if self.__isMouseEvent(e):
			self._removeEventListenerInList(e, listener, self._mouseEventList)
		else:
			super(InteractiveObject, self).removeEventListener(e, listener)

	def removeAllEventListeners(self):
		self._mouseEventList = []

		super(InteractiveObject, self).removeAllEventListeners()

	def dispatchEvent(self, e):
		if self.__isMouseEvent(e):
			self._dispatchEventInList(e, self._mouseEventList)
		else:
			super(InteractiveObject, self).dispatchEvent(e)

	def hasEventListener(self, e, listener):
		if self.__isMouseEvent(e):
			self._hasEventListenerInList(e, listener, self._mouseEventList)
		else:
			return super(InteractiveObject, self).hasEventListener(e, listener)


class DisplayObjectContainer(InteractiveObject):
	def __init__(self):
		super(DisplayObjectContainer, self).__init__()

		self.childList = []
		self.mouseChildren = True
		self.mouseShelter = True

	@property
	def numChildren(self):
		return len(self.childList)

	def addChild(self, child, index = None):
		childList = self.childList

		if isinstance(child, DisplayObject):
			if child.parent is not None:
				child.parent.removeChild(child)

			child.parent = self

			if index is None:
				childList.append(child)
			elif isinstance(index, int) and index < len(childList):
				childList.insert(index, child)
		else:
			raise TypeError("parameter 'child' must be a display object.")

	def addChildAt(self, child, index):
		self.addChild(child, index)

	def removeAllChildren(self):
		self.childList = []

	def removeChild(self, child):
		childList = self.childList

		if not isinstance(child, DisplayObject):
			raise TypeError("parameter 'child' must be a display object.")

		childList.remove(child)

		child.parent = None

	def removeChildAt(self, index):
		childList = self.childList

		if index < len(childList):
			child = childList[index]

			if isinstance(child, DisplayObject):
				child.parent = None

			childList.pop(index)

	def getChildAt(self, index):
		childList = self.childList

		if index < len(childList):
			return childList[index]
		else:
			return -1

	def getChildByName(self, name):
		childList = self.childList

		for o in childList:
			if o is None:
				continue

			if o.name == name:
				return o

		return -1


class Sprite(DisplayObjectContainer):
	def __init__(self):
		super(Sprite, self).__init__()

		self.graphics = Graphics()
		self.graphics.parent = self
		self.useHandCursor = False
		self._clipPath = self.graphics._clipPath

	def _loopDraw(self, c):
		self.graphics._show(c)

		stage._showDisplayList(self.childList)

	def _loopFrame(self):
		self.dispatchEvent(Event.ENTER_FRAME)

	def startX(self):
		left = self.graphics.startX()

		for o in self.childList:
			sx = o.startX()

			if sx < left:
				left = sx
		
		return left + self.x

	def startY(self):
		top = self.graphics.startY()

		for o in self.childList:
			sy = o.startY()

			if sy < top:
				top = sy
		
		return top + self.y

	def endX(self):
		right = self.graphics.endX()

		for o in self.childList:
			ex = o.endX()

			if ex > right:
				right = ex
		
		return right + self.x

	def endY(self):
		bottom = self.graphics.endY()

		for o in self.childList:
			ey = o.endY()

			if ey > bottom:
				bottom = ey
		
		return bottom + self.y

	def __getVisualCoordinate(self, origin, obj):
		return {
			"x" : origin["x"] + obj.x * origin["scaleX"],
			"y" : origin["y"] + obj.y * origin["scaleY"],
			"scaleX" : origin["scaleX"] * obj.scaleX,
			"scaleY" : origin["scaleY"] * obj.scaleY
		}

	def _isMouseOn(self, e, cd):
		if not self.visible:
			return

		childList = self.childList[::-1]
		
		if not self._hasMask():
			for o in childList:
				childCd = self.__getVisualCoordinate(cd, o)

				if o._isMouseOn(e, childCd):
					e["target"] = o

					return True

			graphicsCd = self.__getVisualCoordinate(cd, self.graphics)

			if (self.graphics._isMouseOn(e, graphicsCd)):
				e["target"] = self.graphics

				return True
		else:
			return self.mask._isMouseOn(e, cd)

		return False

	def _enterMouseEvent(self, e, cd):
		if not self.visible:
			return

		currentCd = self.__getVisualCoordinate(cd, self)

		isOn = self._isMouseOn(e, currentCd)

		if isOn:
			if self.useHandCursor:
				stage.useHandCursor = True

			if e["eventType"] == MouseEvent.MOUSE_MOVE.eventType and not self._mouseOver:
				self._mouseOver = True

				e["eventType"] = MouseEvent.MOUSE_OVER.eventType

				self.__dispatchMouseEvent(e, currentCd)

				e["eventType"] = MouseEvent.MOUSE_MOVE.eventType

			if self.mouseChildren:
				for o in self.childList[::-1]:					
					if (hasattr(o, "_enterMouseEvent") and hasattr(o._enterMouseEvent, "__call__") and o._enterMouseEvent(e, currentCd)):
						break
						
			self.__dispatchMouseEvent(e, currentCd)

			if self.mouseShelter:
				return True
			else:
				return False
		elif e["eventType"] == MouseEvent.MOUSE_MOVE.eventType and self._mouseOver:
			self._mouseOutEvent(e, cd)

		return False

	def _mouseOutEvent(self, e, cd):
		if not self.visible:
			return

		currentCd = self.__getVisualCoordinate(cd, self)

		stage.useHandCursor = False

		self._mouseOver = False

		if self.mouseChildren:
			for o in self.childList[::-1]:
				if (hasattr(o, "_mouseOutEvent") and hasattr(o._mouseOutEvent, "__call__") and o._mouseOutEvent(e, currentCd)):
					break

		e["eventType"] = MouseEvent.MOUSE_OUT.eventType

		self.__dispatchMouseEvent(e, currentCd)

		e["eventType"] = MouseEvent.MOUSE_MOVE.eventType

	def __dispatchMouseEvent(self, e, cd):
		if not self.mouseEnabled:
			return

		for o in self._mouseEventList:
			t = o["eventType"]
			l = o["listener"]

			if t.eventType == e["eventType"]:
				eve = Event(e["eventType"])
				eve.offsetX = e["offsetX"]
				eve.offsetY = e["offsetY"]
				eve.selfX = (e["offsetX"] - cd["x"]) / cd["scaleX"]
				eve.selfY = (e["offsetY"] - cd["y"]) / cd["scaleY"]
				eve.target = e["target"]
				eve.currentTarget = self

				l(eve)

	def _getOriginalWidth(self):
		return self.endX() - self.startX()

	def _getOriginalHeight(self):
		return self.endY() - self.startY()


class JoinStyle(Object):
	MITER = "miter"
	ROUND = "round"
	BEVEL = "bevel"

	def __init__(self):
		raise Exception("JoinStyle cannot be instantiated.")


class CapsStyle(Object):
	NONE = "none"
	SQUARE = "square"
	ROUND = "round"

	def __init__(self):
		raise Exception("CapsStyle cannot be instantiated.")


class Graphics(DisplayObject):
	def __init__(self):
		super(Graphics, self).__init__()
		
		self.__drawingList = []
		self.__dataList = []
		self.__currentGraphics = None
		self._clipPath = QtGui.QPainterPath()

	def _show(self, c):
		for item in self.__drawingList:
			if not isinstance(item, dict):
				return

			path = item["path"]

			if not path:
				continue

			lineWidth = item["lineWidth"]
			lineColor = item["lineColor"]
			fillColor = item["fillColor"]
			joins = item["joins"]
			caps = item["caps"]
			miterLimit = item["miterLimit"]
			fillAlpha = item["fillAlpha"]
			lineAlpha = item["lineAlpha"]

			brush = None
			pen = QtGui.QPen()

			c.save()

			if lineWidth:
				pen.setWidth(lineWidth)
			else:
				pen.setWidth(0)

			if lineColor:
				color = getColor(lineColor)

				if lineAlpha:
					color.setAlpha(lineAlpha)

				pen.setColor(color)
			else:
				pen.setColor(getColor("transparent"))

			if joins:
				pen.setJoinStyle(joins)

			if caps:
				pen.setCapStyle(caps)

			if miterLimit:
				pen.setMiterLimit(miterLimit)

			if fillColor:
				color = getColor(fillColor)

				if fillAlpha and hasattr(color, "setAlpha"):
					color.setAlpha(fillAlpha)

				brush = QtGui.QBrush(color)

				if isinstance(fillColor, LinearGradientColor):
					brush.setStyle(QtCore.Qt.LinearGradientPattern)
				elif isinstance(fillColor, RadialGradientColor):
					brush.setStyle(QtCore.Qt.RadialGradientPattern)
				elif isinstance(fillColor, ConicalGradientColor):
					brush.setStyle(QtCore.Qt.ConicalGradientPattern)
				else:
					brush.setStyle(QtCore.Qt.SolidPattern)

				c.setBrush(brush)

			c.setPen(pen)
			c.drawPath(path)

			c.restore()

	def clear(self):
		self.__drawingList = []
		self.__dataList = []
		self.__currentGraphics = None
		del self._clipPath
		self._clipPath = QtGui.QPainterPath()

	def beginFill(self, color = "transparent", alpha = 1):
		if color == "transparent":
			alpha = 0

		self.__currentGraphics = {
			"path" : QtGui.QPainterPath(),
			"lineAlpha" : 255,
			"lineWidth" : None,
			"lineColor" : None,
			"fillColor" : color,
			"fillAlpha" : 255 * alpha,
			"joins" : None,
			"caps" : None,
			"miterLimit" : None
		}

	def endFill(self):
		if not self.__currentGraphics:
			return

		self.__currentGraphics["path"].setFillRule(QtCore.Qt.WindingFill)

		self.__drawingList.append(self.__currentGraphics)

	def lineStyle(self, thickness = 1, color = "black", alpha = 1, joints = None, caps = None, miterLimit = 3):
		if not self.__currentGraphics:
			return

		if color == "transparent":
			alpha = 0

		if joints == JoinStyle.ROUND:
			joints = QtCore.Qt.RoundJoin
		elif joints == JoinStyle.MITER:
			joints = QtCore.Qt.MiterJoin
		elif joints == JoinStyle.BEVEL:
			joints = QtCore.Qt.BevelJoin

		if caps == CapsStyle.NONE:
			caps = QtCore.Qt.FlatCap
		elif caps == CapsStyle.SQUARE:
			caps = QtCore.Qt.SquareCap
		elif caps == CapsStyle.ROUND:
			caps = QtCore.Qt.RoundCap

		self.__currentGraphics["lineWidth"] = thickness
		self.__currentGraphics["lineColor"] = color
		self.__currentGraphics["lineAlpha"] = 255 * alpha
		self.__currentGraphics["joints"] = joints
		self.__currentGraphics["caps"] = caps
		self.__currentGraphics["miterLimit"] = miterLimit

	def moveTo(self, x, y):
		if not self.__currentGraphics:
			return

		self.__currentGraphics["path"].moveTo(x, y)

		self._clipPath.moveTo(x, y)

	def lineTo(self, x, y):
		if not self.__currentGraphics:
			return

		self.__currentGraphics["path"].lineTo(x, y)

		self._clipPath.lineTo(x, y)

	def drawRect(self, x, y, width, height):
		if not self.__currentGraphics:
			return

		self.__currentGraphics["path"].addRect(x, y, width, height)

		self._clipPath.addRect(x, y, width, height)
		self.__dataList.append({"startX" : x, "startY" : y, "endX" : x + width, "endY" : y + height})

	def drawCircle(self, x, y, radius):
		self.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

	def drawEllipse(self, x, y, width, height):
		if not self.__currentGraphics:
			return

		self.__currentGraphics["path"].addEllipse(x, y, width, height)

		self._clipPath.addEllipse(x, y, width, height)
		self.__dataList.append({"startX" : x, "startY" : y, "endX" : x + width, "endY" : y + height})

	def drawRoundRect(self, x, y, width, height, ellipseWidth, ellipseHeight = None):
		if not self.__currentGraphics:
			return

		if not ellipseHeight:
			ellipseHeight = ellipseWidth

		self.__currentGraphics["path"].addRoundedRect(x, y, width, height, ellipseWidth, ellipseHeight)

		self._clipPath.addRoundedRect(x, y, width, height, ellipseWidth, ellipseHeight)
		self.__dataList.append({"startX" : x, "startY" : y, "endX" : x + width, "endY" : y + height})

	def startX(self):
		left = None

		for o in self.__dataList:
			if left is None or o["startX"] < left:
				left = o["startX"]

		if left is None:
			left = 0

		return left

	def startY(self):
		top = None

		for o in self.__dataList:
			if top is None or o["startY"] < top:
				top = o["startY"]

		if top is None:
			top = 0

		return top

	def endX(self):
		right = None

		for o in self.__dataList:
			if right is None or o["endX"] > right:
				right = o["endX"]

		if right is None:
			right = 0

		return right

	def endY(self):
		bottom = None

		for o in self.__dataList:
			if bottom is None or o["endY"] > bottom:
				bottom = o["endY"]

		if bottom is None:
			bottom = 0

		return bottom

	def _isMouseOn(self, e, cd):
		if not self.visible:
			return

		ox = e["offsetX"]
		oy = e["offsetY"]
		x = cd["x"]
		y = cd["y"]
		scaleX = cd["scaleX"]
		scaleY = cd["scaleY"]

		e["target"] = self

		for o in self.__dataList:
			if x + o["startX"] <= ox <= x + o["endX"] * scaleX and y + o["startY"] <= oy <= y + o["endY"] * scaleY:
				return True

		return False


class FPS(Sprite):
	def __init__(self):
		super(FPS, self).__init__()
		
		self.__count = 0
		self.__preTime = time.time()

		self.__background = Sprite()
		self.__background.alpha = 0.8
		self.addChild(self.__background)

		from .text import TextField

		self.__txt = TextField()
		self.__txt.size = 20
		self.__txt.textColor = "white"
		self.addChild(self.__txt)

		self.addEventListener(Event.ENTER_FRAME, self.__onFrame)

	def __onFrame(self, e):
		currentTime = time.time()

		if currentTime - self.__preTime >= 1:
			self.__txt.text = str(self.__count)

			self.__background.graphics.clear()
			self.__background.graphics.beginFill("black")
			self.__background.graphics.drawRect(0, 0, self.__txt.width, self.__txt.height)
			self.__background.graphics.endFill()

			self.__count = 0

			self.__preTime = currentTime

			return

		self.__count += 1


class AnimationFrame(Object):
	def __init__(self, x = 0, y = 0, width = 0, height = 0):
		super(AnimationFrame, self).__init__()
		
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.scaleX = 1
		self.scaleY = 1
		self.rotation = 0
		self.alpha = 1
		self.delay = 0


class AnimationPlayMode(Object):
	HORIZONTAL = "horizontal"
	VERTICAL = "vertical"

	def __init__(self):
		raise Exception("AnimationPlayMode cannot be instantiated.")


class Animation(Sprite):
	def __init__(self, bitmapData = BitmapData(), frameList = [[AnimationFrame()]]):
		super(Animation, self).__init__()
		
		self.bitmapData = bitmapData
		self.frameList = frameList
		self.bitmap = Bitmap(bitmapData)
		self.loop = True
		self.loopTimes = None
		self.currentColumn = 0
		self.currentRow = 0
		self.playMode = AnimationPlayMode.HORIZONTAL
		self.mirroring = False
		self.speed = 0
		self.currentFrame = frameList[0][0]
		self.__bitmapDataStartX = bitmapData.x
		self.__bitmapDataStartY = bitmapData.y
		self.__speedIndex = 0
		self.__loopIndex = 0
		self.__currentDelay = 0
		self.__delayStartTime = None
		self.__playing = False
		
		self.addChild(self.bitmap)
		self.bitmapData.setProperties(self.currentFrame.x, self.currentFrame.y, self.currentFrame.width, self.currentFrame.height)
		self.addEventListener(Event.ENTER_FRAME, self.__onFrame)

	@property
	def playing(self):
		return self.__playing

	@property
	def speed(self):
		return self.__speed

	@speed.setter
	def speed(self, value):
		self.__speed = value
		self.__speedIndex = value
	
	def __onFrame(self, e):
		rowPlayFlag = True
		completeCondition = None

		if self.playing:
			if self.__speedIndex < self.speed:
				self.__speedIndex += 1

				return

			self.__speedIndex = 0

			if self.__currentDelay >= 0 and self.__delayStartTime is not None and (time.time() - self.__delayStartTime) * 1000 < self.__currentDelay:
				return
			else:
				self.__currentDelay = 0
				self.__delayStartTime = None

			currentRow = self.frameList[self.currentRow]
			currentFrame = currentRow[self.currentColumn]

			self.currentFrame = currentFrame

			self.bitmap.scaleX = currentFrame.scaleX
			self.bitmap.scaleY = currentFrame.scaleY
			self.bitmap.rotation = currentFrame.rotation
			self.bitmap.alpha = currentFrame.alpha

			if self.mirroring:
				self.bitmap.x = self.bitmap.width
				self.bitmap.scaleX *= -1
			else:
				self.bitmap.x = 0

			if currentFrame.delay >= 0:
				self.__currentDelay = currentFrame.delay
				self.__delayStartTime = time.time()

			self.bitmapData.setProperties(currentFrame.x + self.__bitmapDataStartX, currentFrame.y + self.__bitmapDataStartY, currentFrame.width, currentFrame.height)

			self.dispatchEvent(AnimationEvent.CHANGE_FRAME)

			if self.playMode == AnimationPlayMode.VERTICAL:
				rowPlayFlag = False

			if rowPlayFlag:
				self.currentColumn += 1

				completeCondition = lambda: self.currentColumn >= len(currentRow)
			else:
				self.currentRow += 1

				completeCondition = lambda: self.currentRow >= len(self.frameList)

			if completeCondition():
				if self.loop and self.__loopWithinTimes():
					if rowPlayFlag:
						self.currentColumn = 0
					else:
						self.currentRow = 0
				else:
					self.__playing = False
					self.__loopIndex = 0

					if rowPlayFlag:
						self.currentColumn = len(currentRow) - 1
					else:
						self.currentRow = len(self.frameList) - 1

					self.dispatchEvent(AnimationEvent.STOP)

	def __loopWithinTimes(self):
		if self.loopTimes:
			self.__loopIndex += 1

			if self.__loopIndex < self.loopTimes:
				return True

			self.__loopIndex = 0

			return False

		return True

	def play(self):
		self.__playing = True

		self.dispatchEvent(AnimationEvent.START)

	def stop(self):
		self.__playing = False

		self.dispatchEvent(AnimationEvent.STOP)

	def reset(self):
		self.__speedIndex = 0
		self.__loopIndex = 0
		self.__currentDelay = 0
		self.__delayStartTime = None

	def getFrame(self, col, row):
		if 0 <= row < len(self.frameList) and 0 <= col < len(self.frameList[row]):
			return self.frameList[row][col]

		return -1

	def divideUniformSizeFrames(width = 0, height = 0, col = 1, row = 1):
		result = []
		frameWidth = width / col
		frameHeight = height / row

		for i in range(row):
			rowList = []

			for j in range(col):
				frame = AnimationFrame(j * frameWidth, i * frameHeight, frameWidth, frameHeight)
				rowList.append(frame)
			
			result.append(rowList)

		return result


class AnimationSet(Sprite):
	def __init__(self):
		super(AnimationSet, self).__init__()
		
		self.animationList = {}
		self.currentAnimation = None

	def addAnimation(self, label, animation, showNow = False):
		if not (isinstance(label, str) and isinstance(animation, Animation)):
			raise TypeError("parameter 'label' must be a str object and 'animation' must be an Animation object.")

		if label in self.animationList:
			raise ValueError("the name of 'label' is repeated.")

		animation.visible = False

		self.animationList[label] = animation

		self.addChild(animation)

		if showNow:
			self.changeAnimation(label)

	def removeAnimation(self, label):
		if not isinstance(label, str):
			raise TypeError("parameter 'label' must be a str object.")

		if label in self.animationList:
			self.animationList[label].remove()

			self.animationList.pop(label)

	def changeAnimation(self, label, fromCol = None, fromRow = None, isReset = False):
		for n in self.animationList:
			o = self.animationList[n]

			if n == label:
				o.visible = True

				if fromRow is not None:
					o.currentRow = fromRow

				if fromCol is not None:
					o.currentColumn = fromCol

				if isReset:
					o.reset()

				o.play()

				self.currentAnimation = o
			else:
				o.visible = False

	def getAnimation(self, label):
		if label in self.animationList:
			return self.animationList[label]
			
		return -1


class SpreadMethod(object):
	PAD = "pad"
	REPEAT = "repeat"
	REFLECT = "reflect"

	def __init__(self):
		raise Exception("SpreadMethod cannot be instantiated.")
		

class GradientColor(Object):
	def __init__(self, alpha = 1):
		super(GradientColor, self).__init__()
		
		self.__alpha = 255 * alpha
		self.value = None
		self.spread = SpreadMethod.PAD

	@property
	def spread(self):
		return self.__spread

	@spread.setter
	def spread(self, value):
		if not isinstance(self.value, QtGui.QGradient):
			return

		self.__spread = value

		if value == SpreadMethod.PAD:
			self.value.setSpread(QtGui.QGradient.PadSpread)
		elif value == SpreadMethod.REPEAT:
			self.value.setSpread(QtGui.QGradient.RepeatSpread)
		elif value == SpreadMethod.REFLECT:
			self.value.setSpread(QtGui.QGradient.ReflectSpread)

	def addColorStop(self, position, colorName):
		if not isinstance(self.value, QtGui.QGradient) or not position or not colorName:
			return

		color = getColor(colorName)
		color.setAlpha(self.__alpha)

		self.value.setColorAt(position, color)


class LinearGradientColor(GradientColor):
	def __init__(self, startX = 0, startY = 0, endX = 0, endY = 0, alpha = 1):
		super(LinearGradientColor, self).__init__(alpha)
		
		self.value = QtGui.QLinearGradient(startX, startY, endX, endY)


class RadialGradientColor(GradientColor):
	def __init__(self, centerX = 0, centerY = 0, radius = 0, alpha = 1):
		super(RadialGradientColor, self).__init__(alpha)
		
		self.value = QtGui.QRadialGradient(centerX, centerY, radius)


class ConicalGradientColor(GradientColor):
	def __init__(self, centerX = 0, centerY = 0, angle = 0, alpha = 1):
		super(ConicalGradientColor, self).__init__(alpha)
		
		self.value = QtGui.QConicalGradient(centerX, centerY, angle)
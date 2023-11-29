from PyQt5.QtCore import Qt, QPoint, QRectF, QPointF
from PyQt5.QtWidgets import QGraphicsRectItem
from PyQt5.QtGui import QPixmap, QPen
import numpy as np
from .create_mask import create_mask


class AutosegLayer(QGraphicsRectItem):
    def __init__(self, parent, label_signal):
        super().__init__(parent)
        self.setOpacity(0.0)
        self.setPen(QPen(Qt.PenStyle.NoPen))

        self._label_signal = label_signal
        self._pixmap = QPixmap()
        self._autoseg_mode = False
        self._img = None  # QImage to fetch color from
        self._np_img = None  # np array for fast pixels fetch
        self._threshold_value = 190

    
    def set_threshold(self, value: int):
        self._threshold_value = value

    def set_image(self, image_path: str, autoseg_path:str):
        #TODO: tiene que haber una mejor opción que el clear pero de otra formo no logro que se me actualice
        r = self.parentItem().pixmap().rect()
        self.setRect(QRectF(r))

        threshold = self._threshold_value
        create_mask(image_path, autoseg_path, threshold)
        self.clear()
        self._pixmap.load(autoseg_path)
        self._update_img()

    def _update_img(self):
        image = self._pixmap.toImage()
        buffer = image.bits()
        buffer.setsize(image.byteCount())
        np_img = np.frombuffer(buffer, dtype=np.uint8)
        np_img = np_img.reshape((image.height(), image.width(), 4))
        self._img = image
        self._np_img = np_img

    def clear(self):
        r = self.parentItem().pixmap().rect()
        self.setRect(QRectF(r))
        self._pixmap = QPixmap(r.size())
        self._pixmap.fill(Qt.GlobalColor.transparent)
        self.update()  # to make changes be visible instantly

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.save()
        painter.drawPixmap(QPoint(), self._pixmap)
        painter.restore()

    def handle_click(self, pos: QPointF,diam: int):
        #Se le pasa el punto y el diámetro del pincel. Después calcula que puntos del mask caen dentro
        if not self._autoseg_mode or not self._img:
            return

        #centro
        x = pos.x()
        y = pos.y()

        #diámetro 
        d = diam

        h,w,_ = self._np_img.shape

        xmin = max(int(x-d),0)
        xmax = min(int(x+d),w)
        ymin = max(int(y-d),0)
        ymax = min(int(y+d),h)
        
        puntos = []
        #Comprobar si hay algún punto no negro en el círculo
        #solo usar el boundingbox, si no hay que recorrer toda la imagen
        #TODO: nada óptimo, tiene que haber mejores opciones

        bbox = self._np_img[ymin:ymax,xmin:xmax,0] #solo miramos un color, porque todo tiene que ser 0 si es negro
        bbox = np.squeeze(bbox)
        i,j = np.where(bbox != 0)

        for index in zip(i,j):
            abs_y = index[0]+ymin
            abs_x = index[1]+xmin
            distancia = np.sqrt((y-abs_y)**2 + (x-abs_x)**2)

            if distancia <= int((d/2) + 1):
                puntos.append([abs_x,abs_y])
        
        self._label_signal.emit(puntos)

    def handle_autoseg_mode(self, is_autoseg: bool):
        self._autoseg_mode = is_autoseg

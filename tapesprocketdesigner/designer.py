#!/usr/bin/python3
import sys
import math
#import ezdxf

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QPointF

if (__name__ == "__main__"):
    import dxf_templates_b2
else:
    import tapesprocketdesigner.dxf_templates_b2

# See: https://images.autodesk.com/adsk/files/autocad_2012_pdf_dxf-reference_enu.pdf
class DXFGenerator:

    def __init__(self):
        self.dxf = ""

    def add(self, str):
        self.dxf += str

    def insertCode(self, code, value):
        self.dxf += code + "\n" + value + "\n"

    def line(self, theLine, scale):
        self.insertCode(   '0', 'LINE' )
        self.insertCode(   '8', 'Default' ) # layer name
        self.insertCode(  '62', '4' )
        self.insertCode(   '5', '255' ) # DXF entity handle
        self.insertCode( '100', 'AcDbEntity' )
        self.insertCode( '100', 'AcDbLine' )
        self.insertCode(  '10', '{:.3f}'.format(theLine[0][0] * scale) ) # line start x
        self.insertCode(  '20', '{:.3f}'.format(theLine[0][1] * scale) ) # line start y
        self.insertCode(  '30', '0.0' )
        self.insertCode(  '11', '{:.3f}'.format(theLine[1][0] * scale) ) # line end x
        self.insertCode(  '21', '{:.3f}'.format(theLine[1][1] * scale) ) # line end x
        self.insertCode(  '31', '0.0' )        

    def point(self, point, scale):
        self.insertCode(   '0', 'POINT' )
        self.insertCode(   '8', 'Drills' ) # layer name
        self.insertCode(  '62', '4' )
        self.insertCode(   '5', '255' ) # DXF entity handle
        self.insertCode( '100', 'AcDbEntity' )
        self.insertCode( '100', 'AcDbPoint' )
        self.insertCode(  '10', '{:.3f}'.format(point[0] * scale) )
        self.insertCode(  '20', '{:.3f}'.format(point[1] * scale) )
        self.insertCode(  '30', '0.0' )

    def layerTable(self, layers):
        self.insertCode('0', 'TABLE')
        self.insertCode('2', 'LAYER')
        self.insertCode('5', '2')
        self.insertCode('330', '0')
        self.insertCode('100', 'AcDbSymbolTable')
        # group code 70 tells a reader how many table records to expect (e.g. pre-allocate memory for).
        # It must be greater or equal to the actual number of records
        self.insertCode('70',str(len(layers)))

        for layer in layers:
            self.insertCode('0', 'LAYER')
            self.insertCode('5', '10')
            self.insertCode('330', '2')
            self.insertCode('100', 'AcDbSymbolTableRecord')
            self.insertCode('100', 'AcDbLayerTableRecord')
            self.insertCode('2', layer)
            self.insertCode('70', '0')
            self.insertCode('62', '7')
            self.insertCode('6', 'CONTINUOUS')

        self.insertCode('0','ENDTAB')
        self.insertCode('0','ENDSEC')

    def startLWPolyline(self, numVerteces):
        self.insertCode(   '0', 'LINE' )
        self.insertCode(   '8', 'Default' ) # layer name
        self.insertCode(  '62', '4' )
        self.insertCode(   '5', '255' ) # DXF entity handle
        self.insertCode( '100', 'AcDbEntity' )
        self.insertCode( '100', 'AcDbPolyline' )
        self.insertCode(  '10', '{:.3f}'.format(theLine[0][0] * scale) ) # line start x
        self.insertCode(  '20', '{:.3f}'.format(theLine[0][1] * scale) ) # line start y
        self.insertCode(  '30', '0.0' )
        self.insertCode(  '11', '{:.3f}'.format(theLine[1][0] * scale) ) # line end x
        self.insertCode(  '21', '{:.3f}'.format(theLine[1][1] * scale) ) # line end x
        self.insertCode(  '31', '0.0' )          

    def generate(self, lines) -> str :
    
        # handle unit scaling if any
        unit_scale = 1
        self.dxf = ""

        # headery crap
        self.insertCode( '999', 'Tape sprocket created by tapegear.py' ) # bogus code 'almost' universally accepted as a comment; comment this line if your DXF parser complains
        self.add( dxf_templates_b2.r14_header )
        self.layerTable(["Default", "Drills"])
        self.add( dxf_templates_b2.r14_blocks )
        
        # now the actual geometry...
        for L in lines:
            self.line(L, unit_scale)

        #for i in rect_comp_drills:
        #    dxf_point(i, unit_scale)

        # and footer
        self.add( dxf_templates_b2.r14_footer )

        return self.dxf

class SprocketCanvas(QWidget):

    def __init__(self):
        super().__init__()
        self.lines = []
        self.userOuterRadius = 1000000

    def paintEvent(self, paintEvent):
        painter = QPainter(self)
        brush = QBrush()
        brush.setColor(QColor('lightgrey'))
        brush.setStyle(Qt.SolidPattern)
        painter.fillRect(self.rect(), brush)

        center = self.rect().center()

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QColor('black'))
        for L in self.lines:
            start = QPointF(center.x() + self.k*L[0][0], center.y() - self.k*L[0][1])
            stop  = QPointF(center.x() + self.k*L[1][0], center.y() - self.k*L[1][1])
            painter.drawLine(start, stop)

    def setLines(self, lines, user_outer_radius):
        self.lines = lines
        self.userOuterRadius = user_outer_radius
        self.k = ((min(self.width(), self.height()) + 0.0) / (self.userOuterRadius*2.0)) * 0.75
        self.update()

    def getLines(self): 
        return self.lines

    def resizeEvent(self, sizeEvent):
        self.k = ((min(self.width(), self.height()) + 0.0) / (self.userOuterRadius*2.0)) * 0.75

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Tape Sprocket Designer')

        self.mainWidget = QWidget()
        self.mainLayout = QHBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)

        # Generate the left side panel
        panelLayout = QVBoxLayout()
        self.mainLayout.addLayout(panelLayout)

        # setup Basic Parameters group
        self.basicParametersGrp = QGroupBox("Basic Parameters")
        self.basicParametersGrp.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        panelLayout.addWidget(self.basicParametersGrp)

        gridLayout = QGridLayout()
        self.basicParametersGrp.setLayout(gridLayout)

        gridLayout.addWidget(QLabel("# of teeth"), 0,0)
        self.numTeeth = QLineEdit("14")
        self.numTeeth.setValidator(QIntValidator(1,100, self))
        gridLayout.addWidget(self.numTeeth, 0,1)

        gridLayout.addWidget(QLabel("Tooth width/diameter"), 1,0)
        self.toothDiameter = QLineEdit("1")
        gridLayout.addWidget(self.toothDiameter, 1,1)
        gridLayout.addWidget(QLabel("mm"), 1,2)

        gridLayout.addWidget(QLabel("Tooth spacing (pitch)"), 2,0)
        self.toothSpacing = QLineEdit("4")
        gridLayout.addWidget(self.toothSpacing, 2,1)
        gridLayout.addWidget(QLabel("mm"), 2,2)

        gridLayout.addWidget(QLabel("Tooth flank height"), 3,0)
        self.toothFlankHeight = QLineEdit("1")
        gridLayout.addWidget(self.toothFlankHeight, 3,1)
        gridLayout.addWidget(QLabel("mm"), 3,2)

        gridLayout.addWidget(QLabel("Tooth length"), 4,0)
        self.toothLengthPct = QLineEdit("60")
        gridLayout.addWidget(self.toothLengthPct, 4,1)
        gridLayout.addWidget(QLabel("percent"), 4,2)

        # setup Report group

        self.reportGrp = QGroupBox("Report")
        self.reportGrp.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        panelLayout.addWidget(self.reportGrp)

        gridLayout2 = QGridLayout()
        self.reportGrp.setLayout(gridLayout2)

        gridLayout2.addWidget(QLabel("Inner diameter"), 0,0)
        self.innerDiameter = QLabel("N/A")
        gridLayout2.addWidget(self.innerDiameter, 0,1)
        gridLayout2.addWidget(QLabel("mm"), 0,2)

        gridLayout2.addWidget(QLabel("Design diameter"), 1,0)
        self.designDiameter = QLabel("N/A")
        gridLayout2.addWidget(self.designDiameter, 1,1)
        gridLayout2.addWidget(QLabel("mm"), 1,2)

        gridLayout2.addWidget(QLabel("Outer diameter"), 2,0)
        self.outerDiameter = QLabel("N/A")
        gridLayout2.addWidget(self.outerDiameter, 2,1)
        gridLayout2.addWidget(QLabel("mm"), 2,2)

        gridLayout2.addWidget(QLabel("Max. outer diameter"), 3,0)
        self.maxOuterDiameter = QLabel("N/A")
        gridLayout2.addWidget(self.maxOuterDiameter, 3,1)
        gridLayout2.addWidget(QLabel("mm"), 3,2)        

        # Export to DXF button
        self.exportButton = QPushButton("Export to DXF")
        self.exportButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.exportButton.pressed.connect(self.onWriteDXF)
        panelLayout.addWidget(self.exportButton)

        panelLayout.addSpacerItem(QSpacerItem(0,0, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding))

        # Generate the right sprocket display

        rightLayout = QVBoxLayout()

        self.sprocketCanvas = SprocketCanvas()
        self.sprocketCanvas.setMinimumSize(200,200)
        sprocketCanvasSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #sprocketCanvasSizePolicy.setHeightForWidth(True)
        self.sprocketCanvas.setSizePolicy(sprocketCanvasSizePolicy)
        rightLayout.addWidget(self.sprocketCanvas, 1)
        #rightLayout.addSpacerItem(QSpacerItem(0,0, QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))

        self.mainLayout.addLayout(rightLayout, 1)

        # add everything to the main window
        self.setCentralWidget(self.mainWidget)

        # Connect up the GUI widgets
        self.numTeeth.editingFinished.connect(self.computeGear)
        self.toothDiameter.editingFinished.connect(self.computeGear)
        self.toothSpacing.editingFinished.connect(self.computeGear)
        self.toothFlankHeight.editingFinished.connect(self.computeGear)
        self.toothLengthPct.editingFinished.connect(self.computeGear)

        self.show()

    def computeGear(self):
        n_teeth   = float(self.numTeeth.text())
        tooth_dia = float(self.toothDiameter.text())
        tooth_pitch = float(self.toothSpacing.text())
        flank_height = float(self.toothFlankHeight.text())
        tooth_length_pct = float(self.toothLengthPct.text())

        #Process:
        # Generate a single tooth: taper edges so that (leftedge-to-rightedge) distance is no greater than the outer-to-outer distance at the base of the tooth: 'undo' the splay caused by the teeth being on an arc.
        # This splay is given by the angle that subtends the arc bounded by the outer edges of the tooth (straight part at top of "design" radius). This is the center-to-center arc length + the arc 'inside' one tooth (1/2 tooth on the outside of each center).
        # But we already know the *angle* formed by the center-to-center tooth pitch: (360/nTeeth), so we only need to find the arc length inside one tooth and its resulting angle, and add this to the pitch angle.

        # Intratooth arc angle in degrees: (360/pi) * asin(C / 2r), where C = chord length.

        # So the outer (as well as inner) surface of each tooth must come in 1/2 that amount (relative to radial / sticking straight out).



        # Generate important radii: what I'm calling "design" radius (top of tooth flank; widest point of "where the tape sits"). For thin tapes this is approximately the same as inner radius, but we may as well go ahead and calculate it.
        # Inner radius
        # Maximum outer radius. This is where the tooth comes to a point at the given face angle. The final outer radius can be chosen anywhere between design radius and maximum outer radius (tops of teeth will be cut off).

        # Design radius: ((nTeeth*pitch) / (2*pi))
        # Inner radius: ((nTeeth*pitch) / (2*pi)) - flank height

        # Outer radius: design radius + tooth face height
        # Tooth inner angle is 90 - outer angle, so, tooth face height: tan(90-angle) = h / (w/2) --> h = (w/2)*tan(90-angle)

        ####FIXME: Tooth auto-angle currently broken. Making two adjacent teeth 'straight' on their outside edges is not enough!

        # Calculate where the nominal teeth intersect these circles and generate lines between them.


        design_circumference = n_teeth * tooth_pitch
        design_radius = design_circumference / (2.0*math.pi)
        inner_radius = design_radius - flank_height

        # get the allowed range for the outer radius
        # to do this, need to get (or suggest) the tooth angle. This will be related to 'splay' described above.
        # Unless the user has chosen (or overridden) a desired angle, calculate and use the recommended value

        chord_angle = 2.0 * (180.0/math.pi) * math.asin(tooth_dia / (2.0 * design_radius))

        #try:
        #    tooth_outer_angle = float(toothFaceAngleValue.get())
        #    tooth_inner_angle = 90.0 - tooth_outer_angle - (chord_angle / 2.0)
        #except ValueError:
        tooth_outer_angle = (chord_angle + (360.0 / n_teeth)) / 4.0 # half the equidistant-to-two-teeth to edge-of-tooth angle -> 1/4 of edge-to-edge angle
        tooth_inner_angle = 90.0 - tooth_outer_angle - (chord_angle / 2.0)
            #toothFaceAngleValue.set(str(tooth_outer_angle))

        print("Tooth centers angle: {:f}".format(360.0/n_teeth))
        print("Tooth width contribution: {:f}".format(chord_angle))
        print("Tooth edges angle: {:f}".format((360.0/n_teeth) + chord_angle))

        print("Design circumference = {:f} radius = {:f}".format(design_circumference, design_radius))
        print("Min. tooth angle: {:f} degrees from vertical".format(tooth_outer_angle))

        tooth_face_height = (tooth_dia / 2.0) * math.tan(tooth_inner_angle * (math.pi / 180.0))
        max_outer_radius = design_radius + tooth_face_height

        user_outer_radius = design_radius + ((max_outer_radius - design_radius) * (tooth_length_pct/100.0)) #design_radius + (design_radius*0.5) #max_outer_radius

        print("Resulting tooth height (angled portion) = {:f}".format(tooth_face_height))
        print("Outer radius = {:f}".format(max_outer_radius))

        # From list of tooth centers...
        # Flank (starts,ends): tooth center +/- tooth chordal angle
        # Faces: Remember, working in polar coords. Doublecheck this, but I think where the angle of the ray intersecting the "end of face" (between 0 and chord_angle/2 relative to tooth center) falls will be proportional to where end of face falls between design radius and max. outer radius.

        face_ratio = (user_outer_radius - design_radius) / (max_outer_radius - design_radius) # will produce a result between 0 and 1

        # Actual angle will be the inverse of this, since where user outer = max outer, angle is 0.

        tooth_ending_angle = (1 - face_ratio) * (chord_angle / 2)

        tooth_centers = []

        for i in range(0, int(n_teeth)):
            tooth_centers.append((360.0 / n_teeth) * i)

        # For each tooth:
        #   line(start of flank ~ end of flank)
        #   line(end of flank (start of face) ~ where face intersects outer radius)
        #   line/arc(first ~ second face intersection with outer radius)
        #   reverse of the above (end and start of face, flank)
        #   arc(end of flank ~ start of next tooth's flank)

        # pairs of (r,theta) for line starting and ending point
        polar_lines = []

        for i in tooth_centers:
        # Polar angles are usually considered increasing counterclockwise, with zero "to the right" - we'll do the same,
        # going from righthand side to lefthand side of each tooth.
        # Right flank
            polar_lines.append([ [inner_radius, i-(chord_angle/2)], [design_radius, i-(chord_angle/2)] ])
        # Right face
            polar_lines.append([ [design_radius, i-(chord_angle/2)], [user_outer_radius, i-tooth_ending_angle] ])
        # blunted tip
            polar_lines.append([ [user_outer_radius, i-tooth_ending_angle], [user_outer_radius, i+tooth_ending_angle] ])
        # left face
            polar_lines.append([ [user_outer_radius, i+tooth_ending_angle], [design_radius, i+(chord_angle/2)] ])
        # left flank
            polar_lines.append([ [design_radius, i+(chord_angle/2)], [inner_radius, i+(chord_angle/2)] ])
        # finally, the space between this and the next tooth
            polar_lines.append([ [inner_radius, i+(chord_angle/2)], [inner_radius, i+(360.0/n_teeth)-(chord_angle/2)] ])


        # if cutter crap-removal on: remove the shoulder left behind when outside-pocketing concave portions; in this case where the tooth flanks meet the inner radius.
        # cut (d/2) below the radius, then across by at least d (+ ballhair?) to ensure pocket algorithm will allow cutting in there, then back to inner radius.
        # It is an error if d exceeds the distance between teeth.

        # Hmm... will also fail if d exceeds 1/2 distance between teeth, and makes more math for me. For now just add drills that will take the shoulders off.

        polar_comp_drills = []

        try:
            #comp_r = float(cutterDiaLabelValue.get()) / 2.0
            comp_r = float(0.0) / 2.0
            for i in tooth_centers:
                # at end of this tooth
                # put the hole center @ inside diameter line, 1 cutter radius from edge of tooth
                polar_comp_drills.append([inner_radius, i+(chord_angle/2) + (360*comp_r/(2*math.pi*(inner_radius - comp_r)))])
                # at start of next tooth
                polar_comp_drills.append([inner_radius , i+(360.0/n_teeth)-(chord_angle/2) - (360*comp_r/(2*math.pi*(inner_radius - comp_r)))])
        except ValueError:
            comp_r = 0

        rect_lines = []
        rect_comp_drills = []

        for i in polar_lines:
            rect_lines.append([self.p2r(i[0][0],i[0][1]),  self.p2r(i[1][0],i[1][1])])

        for i in polar_comp_drills:
            rect_comp_drills.append(self.p2r(i[0],i[1]))

        self.sprocketCanvas.setLines(rect_lines, user_outer_radius)

        self.innerDiameter.setText("{:.3f}".format(inner_radius * 2))
        self.designDiameter.setText("{:.3f}".format(design_radius * 2))
        self.outerDiameter.setText("{:.3f}".format(user_outer_radius * 2))
        self.maxOuterDiameter.setText("{:.3f}".format(max_outer_radius * 2))

    def p2r(self, r, theta):
        #python's builtin math functions work in radians, so convert...
        theta = theta * (math.pi / 180.0)
        return r*math.cos(theta), r*math.sin(theta)


    def dist(self, xy1, xy2):
        dist_x = abs(xy1[0] - xy2[0])
        dist_y = abs(xy1[1] - xy2[1])
        distance = math.sqrt((dist_x*dist_x) + (dist_y*dist_y))
        return distance

    def onWriteDXF(self):
        if not self.sprocketCanvas.getLines():
            return            

        dxfgen = DXFGenerator()
        dxf = dxfgen.generate(self.sprocketCanvas.getLines())

        fileName, _ = QFileDialog.getSaveFileName(self, "Export as DXF","","DXF Files (*.dxf)")
        if fileName:
            DFXFile = open(fileName, "w")
            DFXFile.write(dxf)
            DFXFile.close()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())

if (__name__ == "__main__"):
    main()

#!/usr/bin/python3
# Copyright 2023 - 2023, Niels Moseley and the pyrigremote contributors
# SPDX-License-Identifier: GPL-3.0-only

import sys
import math
import ezdxf
from ezdxf import units
import svgwrite

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import Qt, QPointF

from version import *
from customlabel import *
from sprocketcanvas import *

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Tape Sprocket Designer {:s}'.format(version))
        self.mainWidget = QWidget()
        self.mainLayout = QHBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)

        # Generate the left side panel
        panelLayout = QVBoxLayout()
        self.mainLayout.addLayout(panelLayout)

        # setup Basic Parameters group
        self.basicParametersGrp = QGroupBox("Basic Parameters")
        self.basicParametersGrp.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
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
        self.reportGrp.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        panelLayout.addWidget(self.reportGrp)

        gridLayout2 = QGridLayout()
        self.reportGrp.setLayout(gridLayout2)

        label = CustomLabel("Inner diameter")
        label.enter.connect(self.onInnerEnter)
        label.leave.connect(self.onLeave)
        gridLayout2.addWidget(label, 0,0)
        self.innerDiameter = QLabel("N/A")
        gridLayout2.addWidget(self.innerDiameter, 0,1)
        gridLayout2.addWidget(QLabel("mm"), 0,2)

        label = CustomLabel("Design diameter")
        label.enter.connect(self.onDesignEnter)
        label.leave.connect(self.onLeave)
        gridLayout2.addWidget(label, 1,0)
        self.designDiameter = QLabel("N/A")
        gridLayout2.addWidget(self.designDiameter, 1,1)
        gridLayout2.addWidget(QLabel("mm"), 1,2)

        label = CustomLabel("Outer diameter")
        label.enter.connect(self.onOuterEnter)
        label.leave.connect(self.onLeave)
        gridLayout2.addWidget(label, 2,0)
        self.outerDiameter = QLabel("N/A")
        gridLayout2.addWidget(self.outerDiameter, 2,1)
        gridLayout2.addWidget(QLabel("mm"), 2,2)

        label = CustomLabel("Max. outer diameter")
        label.enter.connect(self.onMaxOuterEnter)
        label.leave.connect(self.onLeave)
        gridLayout2.addWidget(label, 3,0)
        self.maxOuterDiameter = QLabel("N/A")
        gridLayout2.addWidget(self.maxOuterDiameter, 3,1)
        gridLayout2.addWidget(QLabel("mm"), 3,2)        

        # Export to DXF button
        buttonLayout = QHBoxLayout()

        self.exportDXFButton = QPushButton("Export to DXF")
        self.exportDXFButton.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.exportDXFButton.pressed.connect(self.onWriteDXF)
        buttonLayout.addWidget(self.exportDXFButton)

        self.exportSVFButton = QPushButton("Export to SVG")
        self.exportSVFButton.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.exportSVFButton.pressed.connect(self.onWriteSVG)
        buttonLayout.addWidget(self.exportSVFButton)

        panelLayout.addLayout(buttonLayout)

        panelLayout.addSpacerItem(QSpacerItem(0,0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.MinimumExpanding))

        # Generate the right sprocket display

        rightLayout = QVBoxLayout()

        self.sprocketCanvas = SprocketCanvas()
        self.sprocketCanvas.setMinimumSize(200,200)
        sprocketCanvasSizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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

        # init data
        self.lines = []
        self.max_outer_radius = 0
        self.inner_radius = 0
        self.outer_radius = 0
        self.design_radius = 0
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
        self.design_radius = design_circumference / (2.0*math.pi)
        self.inner_radius = self.design_radius - flank_height

        # get the allowed range for the outer radius
        # to do this, need to get (or suggest) the tooth angle. This will be related to 'splay' described above.
        # Unless the user has chosen (or overridden) a desired angle, calculate and use the recommended value

        chord_angle = 2.0 * (180.0/math.pi) * math.asin(tooth_dia / (2.0 * self.design_radius))

        #try:
        #    tooth_outer_angle = float(toothFaceAngleValue.get())
        #    tooth_inner_angle = 90.0 - tooth_outer_angle - (chord_angle / 2.0)
        #except ValueError:
        tooth_outer_angle = (chord_angle + (360.0 / n_teeth)) / 4.0 # half the equidistant-to-two-teeth to edge-of-tooth angle -> 1/4 of edge-to-edge angle
        tooth_inner_angle = 90.0 - tooth_outer_angle - (chord_angle / 2.0)
            #toothFaceAngleValue.set(str(tooth_outer_angle))

        #print("Tooth centers angle: {:f}".format(360.0/n_teeth))
        #print("Tooth width contribution: {:f}".format(chord_angle))
        #print("Tooth edges angle: {:f}".format((360.0/n_teeth) + chord_angle))

        #print("Design circumference = {:f} radius = {:f}".format(design_circumference, design_radius))
        #print("Min. tooth angle: {:f} degrees from vertical".format(tooth_outer_angle))

        tooth_face_height = (tooth_dia / 2.0) * math.tan(tooth_inner_angle * (math.pi / 180.0))
        self.max_outer_radius = self.design_radius + tooth_face_height

        self.outer_radius = self.design_radius + ((self.max_outer_radius - self.design_radius) * (tooth_length_pct/100.0)) #design_radius + (design_radius*0.5) #self.max_outer_radius

        #print("Resulting tooth height (angled portion) = {:f}".format(tooth_face_height))
        #print("Outer radius = {:f}".format(self.max_outer_radius))

        # From list of tooth centers...
        # Flank (starts,ends): tooth center +/- tooth chordal angle
        # Faces: Remember, working in polar coords. Doublecheck this, but I think where the angle of the ray intersecting the "end of face" (between 0 and chord_angle/2 relative to tooth center) falls will be proportional to where end of face falls between design radius and max. outer radius.

        face_ratio = (self.outer_radius - self.design_radius) / (self.max_outer_radius - self.design_radius) # will produce a result between 0 and 1

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
            polar_lines.append([ [self.inner_radius, i-(chord_angle/2)], [self.design_radius, i-(chord_angle/2)] ])
        # Right face
            polar_lines.append([ [self.design_radius, i-(chord_angle/2)], [self.outer_radius, i-tooth_ending_angle] ])
        # blunted tip
            polar_lines.append([ [self.outer_radius, i-tooth_ending_angle], [self.outer_radius, i+tooth_ending_angle] ])
        # left face
            polar_lines.append([ [self.outer_radius, i+tooth_ending_angle], [self.design_radius, i+(chord_angle/2)] ])
        # left flank
            polar_lines.append([ [self.design_radius, i+(chord_angle/2)], [self.inner_radius, i+(chord_angle/2)] ])
        # finally, the space between this and the next tooth
            polar_lines.append([ [self.inner_radius, i+(chord_angle/2)], [self.inner_radius, i+(360.0/n_teeth)-(chord_angle/2)] ])


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
                polar_comp_drills.append([self.inner_radius, i+(chord_angle/2) + (360*comp_r/(2*math.pi*(self.inner_radius - comp_r)))])
                # at start of next tooth
                polar_comp_drills.append([self.inner_radius , i+(360.0/n_teeth)-(chord_angle/2) - (360*comp_r/(2*math.pi*(self.inner_radius - comp_r)))])
        except ValueError:
            comp_r = 0

        self.lines = []
        rect_comp_drills = []

        for i in polar_lines:
            self.lines.append([self.p2r(i[0][0],i[0][1]),  self.p2r(i[1][0],i[1][1])])

        for i in polar_comp_drills:
            rect_comp_drills.append(self.p2r(i[0],i[1]))

        self.sprocketCanvas.setLines(self.lines, self.outer_radius)

        self.innerDiameter.setText("{:.3f}".format(self.inner_radius * 2))
        self.designDiameter.setText("{:.3f}".format(self.design_radius * 2))
        self.outerDiameter.setText("{:.3f}".format(self.outer_radius * 2))
        self.maxOuterDiameter.setText("{:.3f}".format(self.max_outer_radius * 2))

    def p2r(self, r, theta):
        #python's builtin math functions work in radians, so convert...
        theta = theta * (math.pi / 180.0)
        return r*math.cos(theta), r*math.sin(theta)

    def p2r_tuple(self, r, theta):
        #python's builtin math functions work in radians, so convert...
        theta = theta * (math.pi / 180.0)
        return (r*math.cos(theta), r*math.sin(theta))

    def dist(self, xy1, xy2):
        dist_x = abs(xy1[0] - xy2[0])
        dist_y = abs(xy1[1] - xy2[1])
        distance = math.sqrt((dist_x*dist_x) + (dist_y*dist_y))
        return distance

    def onWriteDXF(self):
        if not self.sprocketCanvas.getLines():
            return            

        fileName, _ = QFileDialog.getSaveFileName(self, "Export as DXF","","DXF Files (*.dxf)")
        if fileName:
            doc = ezdxf.new("R2000")
            doc.units = units.MM
            msp = doc.modelspace()

            for L in self.lines:
                pstart = (L[0][0], L[0][1])
                pstop  = (L[1][0], L[1][1])
                msp.add_line(pstart, pstop)

            doc.saveas(fileName)

    def onWriteSVG(self):
        if not self.sprocketCanvas.getLines():
            return            

        fileName, _ = QFileDialog.getSaveFileName(self, "Export as SVG","","SVG Files (*.svg)")
        if fileName:
            w = self.max_outer_radius * 2
            h = self.max_outer_radius * 2
            dwg = svgwrite.Drawing(fileName, size=('{:f}mm'.format(w), '{:f}mm'.format(h)),
                viewBox=('0 0 {:f} {:f}').format(w,h))

            p = dwg.path(stroke=svgwrite.rgb(0, 0, 0, '%'), stroke_width=0.25)

            firstCoordinate = True
            for L in self.lines:
                px = w/2 + L[0][0]
                py = h/2 + L[0][1]
                if firstCoordinate:
                    p.push("M {:f} {:f}". format(px,py))
                    firstCoordinate = False
                else:
                    p.push(" {:f} {:f}". format(px,py))

                #pstart = (w/2 + L[0][0], h/2 + L[0][1])
                #pstop  = (w/2 + L[1][0], h/2 + L[1][1])
                #dwg.add(dwg.line(pstart, pstop, stroke=svgwrite.rgb(0, 0, 0, '%'), stroke_width=0.25))

            dwg.add(p)

            dwg.save()            

    def onInnerEnter(self):
        if (self.inner_radius > 0):
            self.sprocketCanvas.setCircle(self.inner_radius)

    def onOuterEnter(self):
        if (self.outer_radius > 0):
            self.sprocketCanvas.setCircle(self.outer_radius)
        return

    def onDesignEnter(self):
        if (self.design_radius > 0):
            self.sprocketCanvas.setCircle(self.design_radius)
        return

    def onMaxOuterEnter(self):
        if (self.max_outer_radius > 0):
            self.sprocketCanvas.setCircle(self.max_outer_radius)
        return

    def onLeave(self):
        self.sprocketCanvas.setCircle(0)
        return

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())

if (__name__ == "__main__"):
    main()


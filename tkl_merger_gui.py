import os
import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import tkl_merger

class MainWindow(QtWidgets.QMainWindow):
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		
		self.central_widget = QtWidgets.QWidget(self)
		self.setCentralWidget(self.central_widget)
		
		self.setWindowTitle('tkl-merger')
		try:
			scriptDir = os.path.dirname(os.path.realpath(__file__))
			self.setWindowIcon(QtGui.QIcon(os.path.join(scriptDir,'icon.png')))
		except: pass
		
		self.dir_models = "C:/Program Files (x86)/Universal Interactive/Blue Tongue Software/Jurassic Park Operation Genesis/JPOG/Data/Models"
		self.dir_out = "C:\\"
		self.dinos = []
		self.tmd_names = []
		self.boss_tkl = ""
		self.names_to_full_paths = {}
		self.tmd_to_tkl = {}

		# Just some button connected to `plot` method
		self.b_add = QtWidgets.QPushButton('Load TMDs')
		self.b_add.setToolTip("Load TMD files you want to merge.")
		self.b_add.clicked.connect(self.add_tmds)
		
		self.b_remove = QtWidgets.QPushButton('Remove TMDs')
		self.b_remove.setToolTip("Remove TMD files you do not want to merge.")
		self.b_remove.clicked.connect(self.remove_tmds)
		
		self.b_merge = QtWidgets.QPushButton('Merge')
		self.b_merge.setToolTip("Merge these files according to the current settings.")
		self.b_merge.clicked.connect(self.run)

		self.c_tkl = QtWidgets.QComboBox(self)
		self.c_tkl.setToolTip("Select the master TKL. This determines how many keys you may use.")
		self.c_tkl.currentIndexChanged.connect(self.set_boss_tkl)
		
		self.tmd_widget = QtWidgets.QListWidget()
		self.tmd_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		
		self.qgrid = QtWidgets.QGridLayout()
		self.qgrid.setHorizontalSpacing(0)
		self.qgrid.setVerticalSpacing(0)
		self.qgrid.addWidget(self.b_add, 0, 0)
		self.qgrid.addWidget(self.b_remove, 0, 1)
		self.qgrid.addWidget(self.b_merge, 0, 2)
		self.qgrid.addWidget(self.c_tkl, 0, 3)
		self.qgrid.addWidget(self.tmd_widget, 1, 0, 1, 4)
		
		self.central_widget.setLayout(self.qgrid)
		
	def run(self):
		self.dir_out = QtWidgets.QFileDialog.getExistingDirectory(self, 'Output folder', self.dir_out, )
		if self.dir_out:
			tkl_merger.work([ self.names_to_full_paths[tmd_name] for tmd_name in self.tmd_names], self.dir_out, self.boss_tkl)
			print("Done!")
	
	def set_boss_tkl(self):
		self.boss_tkl = self.c_tkl.currentText()
	
	def update_tkl_combo(self):
		boss_tkl = self.boss_tkl
		self.c_tkl.clear()
		self.c_tkl.addItems(sorted(set(self.tmd_to_tkl.values())))
		#see if the old tkl boss is still in existance, then update it
		active_index = self.c_tkl.findText(boss_tkl)
		if active_index > -1:
			self.c_tkl.setCurrentIndex(active_index)
	
	def add_tmds(self):
		file_src = QtWidgets.QFileDialog.getOpenFileNames(self, 'Load TMDs', self.dir_models, "TMD files (*.tmd)")[0]
		for tmd_path in file_src:
			self.dir_models, tmd_name = os.path.split(tmd_path)
			if tmd_name not in self.tmd_names:
				self.tmd_names.append(tmd_name)
				self.tmd_widget.addItem(tmd_name)
				#get the tkl name
				with open(tmd_path, 'rb') as f:
					f.seek(12)
					tkl_name = f.read(8).split(b"\x00")[0].decode("utf-8")#+".tkl"
					self.tmd_to_tkl[tmd_name] = tkl_name
				
				self.names_to_full_paths[tmd_name] = tmd_path
		self.update_tkl_combo()
		
	def remove_tmds(self):
		for item in self.tmd_widget.selectedItems():
			tmd_name = item.text()
			for i in reversed(range(0, len(self.tmd_names))):
				if self.tmd_names[i] == tmd_name:
					self.tmd_names.pop(i)
					self.tmd_to_tkl.pop(tmd_name)
			self.tmd_widget.takeItem(self.tmd_widget.row(item))
		
		self.update_tkl_combo()

if __name__ == '__main__':
	appQt = QtWidgets.QApplication([])
	
	#style
	appQt.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
	dark_palette = QtGui.QPalette()
	WHITE =     QtGui.QColor(255, 255, 255)
	BLACK =     QtGui.QColor(0, 0, 0)
	RED =       QtGui.QColor(255, 0, 0)
	PRIMARY =   QtGui.QColor(53, 53, 53)
	SECONDARY = QtGui.QColor(35, 35, 35)
	TERTIARY =  QtGui.QColor(42, 130, 218)
	dark_palette.setColor(QtGui.QPalette.Window,          PRIMARY)
	dark_palette.setColor(QtGui.QPalette.WindowText,      WHITE)
	dark_palette.setColor(QtGui.QPalette.Base,            SECONDARY)
	dark_palette.setColor(QtGui.QPalette.AlternateBase,   PRIMARY)
	dark_palette.setColor(QtGui.QPalette.ToolTipBase,     WHITE)
	dark_palette.setColor(QtGui.QPalette.ToolTipText,     WHITE)
	dark_palette.setColor(QtGui.QPalette.Text,            WHITE)
	dark_palette.setColor(QtGui.QPalette.Button,          PRIMARY)
	dark_palette.setColor(QtGui.QPalette.ButtonText,      WHITE)
	dark_palette.setColor(QtGui.QPalette.BrightText,      RED)
	dark_palette.setColor(QtGui.QPalette.Link,            TERTIARY)
	dark_palette.setColor(QtGui.QPalette.Highlight,       TERTIARY)
	dark_palette.setColor(QtGui.QPalette.HighlightedText, BLACK)
	appQt.setPalette(dark_palette)
	appQt.setStyleSheet("QToolTip { color: #ffffff; background-color: #353535; border: 1px solid white; }")
	
	win = MainWindow()
	win.show()
	appQt.exec_()